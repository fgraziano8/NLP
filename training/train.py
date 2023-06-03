import torch
import collections
import numpy as np
import evaluate
import random
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
from tqdm.auto import tqdm
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import default_data_collator
from accelerate import Accelerator
from transformers import get_scheduler


raw_datasets = load_dataset("squad_it")
metric = evaluate.load("squad")

MODEL_CHECKPOINT = "dbmdz/bert-base-italian-xxl-cased" # xlm-roberta-base -> epoch 0: {'exact_match': 63.35917991851755, 'f1': 74.56437626967886}
# 1 - epoch 0: {'exact_match': 62.596924694440794, 'f1': 74.0358723261344}
# 2 - epoch 1: {'exact_match': 64.27914311998948, 'f1': 75.54955833237116}
# 3 - epoch 2: {'exact_match': 63.871730845051914, 'f1': 75.34846697119495}
# 4 - epoch 3: {'exact_match': 63.188329609672756, 'f1': 74.81940412222508}

MAX_LENGTH = 384
STRIDE = 128
tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)

BATCH_SIZE = 8
LEARNING_RATE = 2e-5
EPOCHS = 4

torch.manual_seed(0)

random.seed(0)
np.random.seed(0)
g = torch.Generator()
g.manual_seed(0)
g2 = torch.Generator()
g2.manual_seed(0)


def preprocess_training_examples(examples):
    questions = [q.strip() for q in examples["question"]]
    inputs = tokenizer(
        questions,
        examples["context"],
        max_length=MAX_LENGTH,
        truncation="only_second",
        stride=STRIDE,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    offset_mapping = inputs.pop("offset_mapping")
    sample_map = inputs.pop("overflow_to_sample_mapping")
    answers = examples["answers"]
    start_positions = []
    end_positions = []

    for i, offset in enumerate(offset_mapping):
        sample_idx = sample_map[i]
        answer = answers[sample_idx]
        start_char = answer["answer_start"][0]
        end_char = answer["answer_start"][0] + len(answer["text"][0])
        sequence_ids = inputs.sequence_ids(i)

        # Find the start and end of the context
        idx = 0
        while sequence_ids[idx] != 1:
            idx += 1
        context_start = idx
        while sequence_ids[idx] == 1:
            idx += 1
        context_end = idx - 1

        # If the answer is not fully inside the context, label is (0, 0)
        if offset[context_start][0] > start_char or offset[context_end][1] < end_char:
            start_positions.append(0)
            end_positions.append(0)
        else:
            # Otherwise it's the start and end token positions
            idx = context_start
            while idx <= context_end and offset[idx][0] <= start_char:
                idx += 1
            start_positions.append(idx - 1)

            idx = context_end
            while idx >= context_start and offset[idx][1] >= end_char:
                idx -= 1
            end_positions.append(idx + 1)

    inputs["start_positions"] = start_positions
    inputs["end_positions"] = end_positions
    return inputs


def preprocess_validation_examples(examples):
    questions = [q.strip() for q in examples["question"]]
    inputs = tokenizer(
        questions,
        examples["context"],
        max_length=MAX_LENGTH,
        truncation="only_second",
        stride=STRIDE,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    sample_map = inputs.pop("overflow_to_sample_mapping")
    example_ids = []

    for i in range(len(inputs["input_ids"])):
        sample_idx = sample_map[i]
        example_ids.append(examples["id"][sample_idx])

        sequence_ids = inputs.sequence_ids(i)
        offset = inputs["offset_mapping"][i]
        inputs["offset_mapping"][i] = [
            o if sequence_ids[k] == 1 else None for k, o in enumerate(offset)
        ]

    inputs["example_id"] = example_ids
    return inputs


def compute_metrics(start_logits, end_logits, features, examples):
    n_best = 20
    max_answer_length = 30

    example_to_features = collections.defaultdict(list)
    for idx, feature in enumerate(features):
        example_to_features[feature["example_id"]].append(idx)

    predicted_answers = []
    for i, example in enumerate(tqdm(examples)):
        if i > len(start_logits):
            break
        example_id = example["id"]
        context = example["context"]
        answers = []

        # Loop through all features associated with that example
        for feature_index in example_to_features[example_id]:
            start_logit = start_logits[feature_index]
            end_logit = end_logits[feature_index]
            offsets = features[feature_index]["offset_mapping"]

            start_indexes = np.argsort(start_logit)[-1: -n_best - 1: -1].tolist()
            end_indexes = np.argsort(end_logit)[-1: -n_best - 1: -1].tolist()
            for start_index in start_indexes:
                for end_index in end_indexes:
                    # Skip answers that are not fully in the context
                    if offsets[start_index] is None or offsets[end_index] is None:
                        continue
                    # Skip answers with a length that is either < 0 or > max_answer_length
                    if (
                            end_index < start_index
                            or end_index - start_index + 1 > max_answer_length
                    ):
                        continue
                    try:
                        answer = {
                            "text": context[offsets[start_index][0]: offsets[end_index][1]],
                            "logit_score": start_logit[start_index] + end_logit[end_index],
                        }
                        answers.append(answer)
                    except:
                        pass

        # Select the answer with the best score
        if len(answers) > 0:
            best_answer = max(answers, key=lambda x: x["logit_score"])
            predicted_answers.append(
                {"id": example_id, "prediction_text": best_answer["text"]}
            )
        else:
            predicted_answers.append({"id": example_id, "prediction_text": ""})

    theoretical_answers = [{"id": ex["id"], "answers": ex["answers"]} for ex in examples]

    return metric.compute(predictions=predicted_answers, references=theoretical_answers)


def evaluate_model(trainer, val_dataset, raw_val_dataset):
    predictions, _, _ = trainer.predict(val_dataset)
    start_logits, end_logits = predictions

    eval_metrics = compute_metrics(start_logits, end_logits, val_dataset, raw_val_dataset)

    print()
    print("Evaluation metrics:")
    print(f"EM: {round(eval_metrics['exact_match'], 2)}, F1-score: {round(eval_metrics['f1'], 2)}")


if __name__ == '__main__':

    train_dataset = raw_datasets["train"].map(
        preprocess_training_examples,
        batched=True,
        remove_columns=raw_datasets["train"].column_names,
    )

    print(f'# rec. in raw dataset {len(raw_datasets["train"])}, in final train set: {len(train_dataset)}')

    validation_dataset = raw_datasets["test"].map(
        preprocess_validation_examples,
        batched=True,
        remove_columns=raw_datasets["test"].column_names,
    )

    print(f'# rec. in raw dataset {len(raw_datasets["test"])}, in final validation set: {len(validation_dataset)}')

    # directory where we save the model for each epoch
    OUTPUT_DIR = "fabgraziano_bert_qa_" + str(EPOCHS) + "e_v1"

    train_dataset.set_format("torch")
    validation_set = validation_dataset.remove_columns(["example_id", "offset_mapping"])
    validation_set.set_format("torch")

    train_dataloader = DataLoader(
        train_dataset,
        shuffle=True,
        collate_fn=default_data_collator,
        batch_size=BATCH_SIZE,
        generator=g
    )
    eval_dataloader = DataLoader(
        validation_set,
        collate_fn=default_data_collator,
        batch_size=BATCH_SIZE,
        generator=g2
    )

    model = AutoModelForQuestionAnswering.from_pretrained(MODEL_CHECKPOINT)

    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)

    # mixed mode (fp16)
    accelerator = Accelerator(mixed_precision="fp16")

    model, optimizer, train_dataloader, eval_dataloader = accelerator.prepare(
        model, optimizer, train_dataloader, eval_dataloader
    )

    num_train_epochs = EPOCHS
    num_update_steps_per_epoch = len(train_dataloader)
    num_training_steps = num_train_epochs * num_update_steps_per_epoch

    lr_scheduler = get_scheduler(
        "linear",
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=num_training_steps,
    )

    progress_bar = tqdm(range(num_training_steps))

    for epoch in range(EPOCHS):
        #
        # Training
        #
        model.train()
        for step, batch in enumerate(train_dataloader):
            outputs = model(**batch)
            loss = outputs.loss
            accelerator.backward(loss)

            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()
            progress_bar.update(1)

        #
        # Evaluation
        #
        model.eval()
        start_logits = []
        end_logits = []
        accelerator.print("Evaluation!")
        for batch in tqdm(eval_dataloader):
            with torch.no_grad():
                outputs = model(**batch)

            start_logits.append(accelerator.gather(outputs.start_logits).cpu().numpy())
            end_logits.append(accelerator.gather(outputs.end_logits).cpu().numpy())

        start_logits = np.concatenate(start_logits)
        end_logits = np.concatenate(end_logits)
        start_logits = start_logits[: len(validation_dataset)]
        end_logits = end_logits[: len(validation_dataset)]

        metrics = compute_metrics(
            start_logits, end_logits, validation_dataset, raw_datasets["test"]
        )
        print(f"epoch {epoch}:", metrics)

        # Salva ad ogni epoch
        accelerator.wait_for_everyone()

        unwrapped_model = accelerator.unwrap_model(model)
        unwrapped_model.save_pretrained(OUTPUT_DIR, save_function=accelerator.save)

        if accelerator.is_main_process:
            tokenizer.save_pretrained(OUTPUT_DIR)

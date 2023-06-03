from modules import configModule
from transformers import pipeline, TranslationPipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from datasets import Dataset


@configModule.log_calls
def translate_qa(sentence, origLang, finalLang):
    translator_checkpoint = "Helsinki-NLP/opus-mt-" + origLang + "-" + finalLang
    configModule.logging.info("Utilizzato il checkpoint: " + translator_checkpoint)

    translator = pipeline("translation", model=translator_checkpoint, device=0)

    translator_result = translator(sentence)

    return translator_result[0]['translation_text']


def translate_doc(sentence, origLang, finalLang):
    translator_checkpoint = "Helsinki-NLP/opus-mt-" + origLang + "-" + finalLang

    translator_checkpoint = "Helsinki-NLP/opus-mt-it-en"
    configModule.logging.info("Utilizzato il checkpoint: " + translator_checkpoint)

    # Ottieni il modello e il tokenizer corrispondenti al checkpoint
    model = AutoModelForSeq2SeqLM.from_pretrained(translator_checkpoint)
    tokenizer = AutoTokenizer.from_pretrained(translator_checkpoint)

    translator = TranslationPipeline(
        model=model,
        tokenizer=tokenizer,
        device=0
    )

    max_segment_length = 512

    # Suddividi il testo di input in segmenti più piccoli
    segments = [sentence[i:i + max_segment_length] for i in range(0, len(sentence), max_segment_length)]

    # Creazione del dataset
    dataset = Dataset.from_dict({"translation_input": segments})

    # Definisci una funzione di traduzione che utilizza la pipeline di traduzione
    def translate_example(example):
        translations = translator(example["translation_input"])
        translation_text_list = [translation["translation_text"] for translation in translations]
        return {"translation_text": translation_text_list}

    # Applica la traduzione a ciascun elemento del dataset
    translated_dataset = dataset.map(translate_example, batched=True, batch_size=16)

    # Combina le traduzioni parziali per ottenere la traduzione completa
    full_translation = " ".join(translated_dataset["translation_text"])

    return full_translation


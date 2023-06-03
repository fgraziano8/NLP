from modules import configModule
from transformers import pipeline
from exceptions import customExceptions

NO_ANSW_FOUND_IT = "Non è stato possibile trovare la risposta a questa domanda."
NO_ANSW_FOUND_EN = "Unable to find the answer to this question."


#@configModule.log_calls
def question_answering(input_context, context_language, input_question):
    if context_language == 'en':
        return question_answering_en(input_context, input_question)
    elif context_language == 'it':
        return question_answering_it(input_context, input_question)
    else:
        configModule.logging.error("UnspecifiedQuestionAnsweringError - Implementazione della lingua '" + context_language + "' per il QA non gestita.")
        raise customExceptions.UnspecifiedQuestionAnsweringError("Implementazione della lingua '" + context_language + "' per il QA non gestita.")


def question_answering_en(input_context, input_question):
    qa_checkpoint = configModule.config.qa_en

    configModule.logging.info("Utilizzato il checkpoint: " + qa_checkpoint)

    nlp = pipeline('question-answering', model=qa_checkpoint, tokenizer=qa_checkpoint, device=0)
    QA_input = {
        'question': input_question,
        'context': input_context
    }

    ans_gen = nlp(QA_input)

    if ans_gen["score"] > configModule.config.qa_en_sensitivity:
        ans_gen["print_answer"] = ans_gen["answer"]
    else:
        ans_gen["print_answer"] = NO_ANSW_FOUND_EN

    return ans_gen


def question_answering_it(input_context, input_question):
    qa_checkpoint = configModule.config.qa_it

    configModule.logging.info("Utilizzato il checkpoint: " + qa_checkpoint)

    nlp = pipeline('question-answering', model=qa_checkpoint, tokenizer=qa_checkpoint, device=0)
    QA_input = {
        'question': input_question,
        'context': input_context,
    }

    ans_gen = nlp(QA_input)

    if ans_gen["score"] > configModule.config.qa_it_sensitivity:
        ans_gen["print_answer"] = ans_gen["answer"]
    else:
        ans_gen["print_answer"] = NO_ANSW_FOUND_IT

    return ans_gen

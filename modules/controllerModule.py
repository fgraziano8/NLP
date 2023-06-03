import json
import datetime
from modules.objectsModule import QuestionAnswer, Answer
from modules import translationModule, configModule, detectionModule, questionAnsweringModule

READ_SECTION = "READ"
QA_SECTION = "QA"
EXIT = "EXIT"

global procDoc


@configModule.log_calls
def init():
    return configModule.config.initial_message


@configModule.log_calls
def process_input_home(read_input):
    configModule.logging.info('Input letto: "' + read_input + '"')

    if read_input is None or not read_input.strip():
        configModule.logging.info("Errore input None o vuoto.")
        msg_ret = "Il nome del file non puo' essere vuoto."

    elif read_input.lower().strip() == "&help":
        msg_ret = print_special_command_list(READ_SECTION)

    elif read_input.lower().strip() == "&exit":
        return manage_exit(), EXIT

    elif read_input.lower().strip() == "&read":
        msg_ret = "Digita il nome del documento che vuoi elaborare."

    elif read_input.lower().strip() == "&list":
        str_ret = "Lista dei PDF elaborati:"
        configModule.logging.info("Lista PDF attualmente in memoria: ".join(configModule.processedDocuments.keys()))
        for pdfKeys in configModule.processedDocuments.keys():
            str_ret = str_ret + "\n- " + pdfKeys
        msg_ret = str_ret

    elif read_input.lower().strip() == "&clear":
        configModule.processedDocuments.clear()
        configModule.logging.info("Lista PDF in memoria pulita.")
        msg_ret = "Lista dei PDF resettata."

    elif read_input.strip().startswith('&'):
        configModule.logging.info("Comando speciale non riconosciuto o non disponibile.")
        msg_ret = "Comando speciale non riconosciuto o non disponibile."

    else:
        try:
            return manage_question_answering(read_input), QA_SECTION
        except Exception as e:
            configModule.logging.error("Errore: si è verificato un problema nella gestione del documento " + read_input + " - " + str(e))
            msg_ret = str(e)

    return msg_ret, READ_SECTION


@configModule.log_calls
def print_special_command_list(section):
    command_ret = "&help - Mostra l'elenco dei comandi speciali."
    command_ret = command_ret + "\n" +"&read - Vai all'inserimento di un nuovo documento da elaborare."

    if section == READ_SECTION:
        command_ret = command_ret + "\n" +"&list - Mostra l'elenco dei documenti elaborati e caricati in memoria."
        command_ret = command_ret + "\n" +"&clear - Resetta la lista dei PDF elaborati."

    command_ret = command_ret + "\n" +"&exit - Esci dal programma."

    return command_ret


@configModule.log_calls
def manage_exit():
    msg_ret = "Informazioni salvate."

    try:
        now = datetime.datetime.now()
        formatted_date = now.strftime(configModule.config.output_date_format)
        configModule.config.end_date = now.strftime(configModule.DATE_FORMAT)

        configModule.logging.info("Salvataggio delle informazioni...")

        json_data = {
            "configurations": configModule.config.__json__(),
            "processed_documents": configModule.processedDocuments
        }
        json_string = json.dumps(json_data, default=lambda obj: obj.__json__(), sort_keys=False)

        # Scrivi il JSON su un file
        with open(configModule.config.output_path + "output_" + formatted_date + ".json", "w") as f:
            f.write(json_string)
    except Exception as e:
        msg_ret = "Errore: si è verificato un problema durante il salvataggio delle informazioni."
        configModule.logging.error("Errore: si è verificato un problema durante il salvataggio - " + str(e))

    return msg_ret


@configModule.log_calls
def manage_question_answering(file_name):
    global procDoc

    pdfId = detectionModule.detect_file(file_name)
    procDoc = configModule.processedDocuments[pdfId]

    configModule.logging.info("Caricato il file '" + procDoc.name + "' (" + procDoc.lang + ")")

    return "Caricato il file '" + procDoc.name + "' (" + procDoc.lang + ")"


@configModule.log_calls
def process_input_qa(input_question):
    global procDoc

    configModule.logging.info("Input letto: " + input_question)
    msg_ret = None

    if input_question is None or not input_question.strip():
        configModule.logging.info("Errore input None o vuoto.")
        msg_ret = "La domanda non puo' essere vuota."

    elif input_question.lower().strip() == "&help":
        msg_ret = print_special_command_list(QA_SECTION)

    elif input_question.lower().strip() == "&exit":
        return manage_exit(), EXIT

    elif input_question.lower().strip() == "&read":
        configModule.logging.info("Torno al flusso iniziale.")
        return "Digita il nome del documento che vuoi elaborare.", READ_SECTION

    elif input_question.strip().startswith('&'):
        configModule.logging.info("Comando speciale non riconosciuto o non disponibile.")
        msg_ret = "Comando speciale non riconosciuto o non disponibile."

    else:
        translated_answer = "-"

        configModule.logging.info("Rilevamento lingua della domanda.")
        try:
            questionLang = detectionModule.detect_language(input_question)
        except Exception as e:
            configModule.logging.error("Impossibile processare la domanda.")
            return str(e), QA_SECTION

        if questionLang != procDoc.lang:
            configModule.logging.info("Traduzione domanda necessaria " + questionLang + " -> " + procDoc.lang)
            translated_question = translationModule.translate_qa(input_question, questionLang, procDoc.lang)
            configModule.logging.info("Domanda tradotta (" + procDoc.lang + "): " + translated_question)
            translation = True

            question = translated_question

        else:
            translation = False

            question = input_question

        try:
            generatedAnswer = questionAnsweringModule.question_answering(procDoc.text, procDoc.lang, question)
        except Exception as e:
            configModule.logging.error("Impossibile processare l'attivita di Question-Answering.")
            return str(e), QA_SECTION

        if translation:
            configModule.logging.info("Traduzione risposta necessaria " + procDoc.lang + " -> " + questionLang)
            translated_answer = translationModule.translate_qa(generatedAnswer["print_answer"], procDoc.lang, questionLang)
            answer = translated_answer
            configModule.logging.info("Risposta originale (" + procDoc.lang + "): " + generatedAnswer["print_answer"])

        else:
            answer = generatedAnswer["print_answer"]

        msg_ret = configModule.config.answer + answer
        configModule.logging.info("Risposta (" + questionLang + "): " + answer)

        newAnswer = Answer(generatedAnswer["answer"], answer, procDoc.lang, translation, translated_answer, questionLang,
                           generatedAnswer["score"], generatedAnswer["start"], generatedAnswer["end"])
        newQuestionAnswer = QuestionAnswer(input_question, questionLang, translation, question, procDoc.lang,
                                           newAnswer)

        procDoc.qa_list.append(newQuestionAnswer)

        # Aggiorno il valore associato a quella chiave nel dizionario
        configModule.processedDocuments[procDoc.name] = procDoc

    return msg_ret, QA_SECTION

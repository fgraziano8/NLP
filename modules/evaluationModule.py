import json
import pickle
import datetime
from modules import objectsModule, configModule, detectionModule, questionAnsweringModule, translationModule, sentenceSimilarityModule

global mapped_data, output_log_name

DATE_FORMAT = "%d/%m/%Y %H:%M:%S.%f"


def read_eval_json(force_it=False):
    global mapped_data

    # Caricamento del file JSON
    with open('Evaluations/evaluation.json', encoding='utf-8') as json_file:
        data = json.load(json_file)

    mapped_data = {}
    for pdf_name, pdf_data in data.items():

        if force_it and "it" != pdf_data["lang"]:
            continue

        eval_qa_list = []
        for qa in pdf_data["qa_list"]:
            question = objectsModule.EvaluationQA(qa["id"], qa["question"], qa["lang"], qa["question_page"], qa["expected_answer"])
            eval_qa_list.append(question)
        pdf = objectsModule.EvaluationDocuments(pdf_data["name"], pdf_data["page_num"], pdf_data["lang"], eval_qa_list)
        mapped_data[pdf_name] = pdf


def write_eval_json(json_name):
    global mapped_data

    json_string = json.dumps(mapped_data, default=lambda obj: obj.__json__(), sort_keys=False, ensure_ascii=False)

    with open("Evaluations/" + json_name, 'w', encoding='utf-8') as json_file:
        json_file.write(json_string)


def print_checkpoint(message):
    global output_log_name

    now = datetime.datetime.now()
    formatted_date = now.strftime(DATE_FORMAT)

    print(formatted_date + " - " + message)

    with open("Evaluations/" + output_log_name, 'a+') as file_log:
        print(formatted_date + " - " + message, file=file_log)

    return formatted_date


def start():
    global mapped_data, output_log_name

    now = datetime.datetime.now()
    formatted_date_file = now.strftime(configModule.config.output_date_format)
    output_json_name = "evaluation_result_" + formatted_date_file + ".json"
    output_log_name = "evaluation_result_" + formatted_date_file + "_log.txt"

    print_checkpoint("#################### START ####################")
    print_checkpoint("")

    read_eval_json()

    print_checkpoint("JSON LETTO")
    print_checkpoint("")

    i = 1

    for pdf_name, pdf in mapped_data.items():

        eval_start_date = print_checkpoint("INIZIO A PROCESSARE " + pdf_name + " (" + str(i) + " DI " + str(len(mapped_data.items())) + ")")
        pdf.eval_start_date = eval_start_date

        try:
            pdf_detected = detectionModule.detect_pdf(pdf_name)

            print_checkpoint("RILEVATO " + pdf_name)

            j = 1

            for qaobj in pdf.eval_qa_list:

                eval_qa_start_date = print_checkpoint("DOCUMENTO " + pdf_name + " - DOMANDA " + str(j) + " DI " + str(len(pdf.eval_qa_list)))
                qaobj.eval_qa_start_date = eval_qa_start_date

                try:

                    if qaobj.lang == pdf.lang:
                        question = qaobj.question
                        qaobj.translated = False
                    else:
                        question = translationModule.translate_qa(qaobj.question, qaobj.lang, pdf.lang)
                        qaobj.translated = True

                    generatedAnswer = questionAnsweringModule.question_answering(configModule.processedDocuments[pdf_detected].text, pdf.lang, question)

                    final_answ = generatedAnswer["answer"]
                    if qaobj.translated:
                        answer_text = translationModule.translate_qa(generatedAnswer["answer"], pdf.lang, qaobj.lang)
                        generatedAnswer["translation"] = True
                        generatedAnswer["translatedAnswer"] = answer_text
                        generatedAnswer["translatedAnswerLang"] = qaobj.lang
                        final_answ = answer_text

                    eval_qa_end_date = print_checkpoint("DOCUMENTO " + pdf_name + " - DOMANDA " + str(j) + " DI " + str(len(pdf.eval_qa_list)) + " - OK")

                    qaobj.answer = generatedAnswer

                    qaobj.similarity = sentenceSimilarityModule.get_similarity(qaobj.expected_answer, final_answ)

                    write_eval_json(output_json_name)
                    
                except Exception as e:
                    eval_qa_end_date = print_checkpoint("DOCUMENTO " + pdf_name + " - DOMANDA " + str(j) + " DI " + str(len(pdf.eval_qa_list)) + " - KO - " + str(e))

                qaobj.eval_qa_end_date = eval_qa_end_date

                j += 1

            eval_end_date = print_checkpoint("FINITO DI PROCESSARE " + pdf_name)

        except Exception as e:
            eval_end_date = print_checkpoint("ERRORE NEL PROCESSARE " + pdf_name + " - " + str(e))

        pdf.eval_end_date = eval_end_date

        i += 1
        print_checkpoint("")

    # Salvataggio del dizionario su file
    with open("Evaluations/eval_test.pickle", "wb") as file:
        pickle.dump(mapped_data, file)

    print_checkpoint("#################### END ####################")


def start_fit():
    global mapped_data, output_log_name
    
    now = datetime.datetime.now()
    formatted_date_file = now.strftime(configModule.config.output_date_format)
    output_json_name = "evaluation_result_FIT_" + formatted_date_file + ".json"
    output_log_name = "evaluation_result_FIT_" + formatted_date_file + "_log.txt"

    print_checkpoint("#################### START FIT ####################")
    print_checkpoint("")

    read_eval_json(True)

    print_checkpoint("JSON FIT LETTO")
    print_checkpoint("")

    i = 1

    for pdf_name, pdf in mapped_data.items():

        eval_start_date = print_checkpoint("INIZIO A PROCESSARE " + pdf_name + " (" + str(i) + " DI " + str(len(mapped_data.items())) + ")")
        pdf.eval_start_date = eval_start_date

        try:
            pdf_detected = detectionModule.detect_pdf(pdf_name)

            print_checkpoint("RILEVATO " + pdf_name)

            print_checkpoint("DOCUMENTO " + pdf_name + " - INIZIO TRADUZIONE")
            translated_context = translationModule.translate_doc(configModule.processedDocuments[pdf_detected].text, "it", "en")
            print_checkpoint("DOCUMENTO " + pdf_name + " - FINE TRADUZIONE")

            j = 1

            for qaobj in pdf.eval_qa_list:

                eval_qa_start_date = print_checkpoint("DOCUMENTO " + pdf_name + " - DOMANDA " + str(j) + " DI " + str(len(pdf.eval_qa_list)))
                qaobj.eval_qa_start_date = eval_qa_start_date

                try:

                    if qaobj.lang.strip() == "en":
                        question = qaobj.question
                        qaobj.translated = False
                    else:
                        question = translationModule.translate_qa(qaobj.question, "it", "en")
                        qaobj.translated = True

                    generatedAnswer = questionAnsweringModule.question_answering(translated_context, "en", question)

                    final_answ = generatedAnswer["answer"]
                    if qaobj.translated:
                        answer_text = translationModule.translate_qa(generatedAnswer["answer"], "en", "it")
                        generatedAnswer["translation"] = True
                        generatedAnswer["translatedAnswer"] = answer_text
                        generatedAnswer["translatedAnswerLang"] = qaobj.lang
                        final_answ = answer_text

                    eval_qa_end_date = print_checkpoint("DOCUMENTO " + pdf_name + " - DOMANDA " + str(j) + " DI " + str(
                        len(pdf.eval_qa_list)) + " - OK")

                    qaobj.answer = generatedAnswer

                    qaobj.similarity = sentenceSimilarityModule.get_similarity(qaobj.expected_answer, final_answ)

                    write_eval_json(output_json_name)

                except Exception as e:
                    eval_qa_end_date = print_checkpoint("DOCUMENTO " + pdf_name + " - DOMANDA " + str(j) + " DI " + str(
                        len(pdf.eval_qa_list)) + " - KO - " + str(e))

                qaobj.eval_qa_end_date = eval_qa_end_date

                j += 1

            eval_end_date = print_checkpoint("FINITO DI PROCESSARE " + pdf_name)

        except Exception as e:
            eval_end_date = print_checkpoint("ERRORE NEL PROCESSARE " + pdf_name + " - " + str(e))

        pdf.eval_end_date = eval_end_date

        i += 1
        print_checkpoint("")

    # Salvataggio del dizionario su file
    with open("Evaluations/eval_fit_test.pickle", "wb") as file:
        pickle.dump(mapped_data, file)

    print_checkpoint("#################### END FIT ####################")


def read_eval_pickle():
    global mapped_data, output_log_name

    output_log_name = "test.txt"

    # Caricamento del dizionario dal file
    with open("Evaluations/eval_fit_test.pickle", "rb") as file:
        mapped_data = pickle.load(file)


def print_evaluation_stats():
    global mapped_data

    # Inizializza le variabili per i calcoli delle statistiche
    min_doc_name_all = ""
    max_doc_name_all = ""
    min_doc_name_it = ""
    max_doc_name_it = ""
    min_doc_name_en = ""
    max_doc_name_en = ""

    min_duration_all = None
    max_duration_all = None
    total_duration_all = 0
    count_all = 0

    min_duration_it = None
    max_duration_it = None
    total_duration_it = 0
    count_it = 0

    min_duration_en = None
    max_duration_en = None
    total_duration_en = 0
    count_en = 0

    min_duration_qa = None
    min_duration_qa_text = ""
    min_duration_qa_doc = ""
    max_duration_qa = None
    max_duration_qa_text = ""
    max_duration_qa_doc = ""

    min_duration_en_qa = None
    min_duration_en_qa_text = ""
    min_duration_en_qa_doc = ""
    max_duration_en_qa = None
    max_duration_en_qa_text = ""
    max_duration_en_qa_doc = ""
    total_duration_qa_en = 0
    count_qa_en = 0

    min_duration_it_qa = None
    min_duration_it_qa_text = ""
    min_duration_it_qa_doc = ""
    max_duration_it_qa = None
    max_duration_it_qa_text = ""
    max_duration_it_qa_doc = ""
    total_duration_qa_it = 0
    count_qa_it = 0

    min_score_qa = None
    max_score_qa = None
    min_similarity_qa = None
    max_similarity_qa = None

    min_score_it_qa = None
    max_score_it_qa = None
    min_similarity_it_qa = None
    max_similarity_it_qa = None
    total_score_qa_it = 0
    total_similarity_qa_it = 0

    min_score_en_qa = None
    max_score_en_qa = None
    min_similarity_en_qa = None
    max_similarity_en_qa = None
    total_score_qa_en = 0
    total_similarity_qa_en = 0

    min_translations_similarity_diff = None
    max_translations_similarity_diff = None
    total_translations_similarity_diff = 0
    count_translations_similarity_diff = 0

    print_checkpoint("")
    print_checkpoint("")
    print_checkpoint("")

    print_checkpoint("#################### STATISTICHE PARZIALI ####################")
    print_checkpoint("")

    # Cicla attraverso gli elementi del dizionario
    for doc_name, eval_doc in mapped_data.items():
        partial_score_qa = 0
        partial_similarity_qa = 0

        # Calcola la durata di elaborazione del documento
        eval_start = datetime.datetime.strptime(eval_doc.eval_start_date, DATE_FORMAT)
        eval_end = datetime.datetime.strptime(eval_doc.eval_end_date, DATE_FORMAT)
        duration = eval_end - eval_start

        # Aggiorna le statistiche per tutti i documenti
        if min_duration_all is None or duration < min_duration_all:
            min_duration_all = duration
            min_doc_name_all = doc_name
        if max_duration_all is None or duration > max_duration_all:
            max_duration_all = duration
            max_doc_name_all = doc_name

        total_duration_all += duration.total_seconds()
        count_all += 1

        # Aggiorna le statistiche per i documenti in italiano
        if eval_doc.lang == "it":
            if min_duration_it is None or duration < min_duration_it:
                min_duration_it = duration
                min_doc_name_it = doc_name
            if max_duration_it is None or duration > max_duration_it:
                max_duration_it = duration
                max_doc_name_it = doc_name

            total_duration_it += duration.total_seconds()
            count_it += 1

            # Aggiorna le statistiche per le domande in italiano
            for qa in eval_doc.eval_qa_list:
                eval_qa_start = datetime.datetime.strptime(qa.eval_qa_start_date, DATE_FORMAT)
                eval_qa_itd = datetime.datetime.strptime(qa.eval_qa_end_date, DATE_FORMAT)
                duration_qa = eval_qa_itd - eval_qa_start

                if qa.translated:
                    qaOri = None

                    for qa2 in eval_doc.eval_qa_list:
                        if not qa2.translated and qa.id == qa2.id:
                            qaOri = qa2
                            break

                    if qaOri is not None:
                        translation_similarity_diff = qaOri.similarity - qa.similarity
                        count_translations_similarity_diff += 1
                        total_translations_similarity_diff = translation_similarity_diff

                        if min_translations_similarity_diff is None or translation_similarity_diff < min_translations_similarity_diff:
                            min_translations_similarity_diff = translation_similarity_diff
                        if max_translations_similarity_diff is None or translation_similarity_diff > max_translations_similarity_diff:
                            max_translations_similarity_diff = translation_similarity_diff

                if min_score_qa is None or qa.answer["score"] < min_score_qa:
                    min_score_qa = qa.answer["score"]
                if max_score_qa is None or qa.answer["score"] > max_score_qa:
                    max_score_qa = qa.answer["score"]

                if min_score_it_qa is None or qa.answer["score"] < min_score_it_qa:
                    min_score_it_qa = qa.answer["score"]
                if max_score_it_qa is None or qa.answer["score"] > max_score_it_qa:
                    max_score_it_qa = qa.answer["score"]

                total_score_qa_it += qa.answer["score"]
                partial_score_qa += qa.answer["score"]

                if min_similarity_qa is None or qa.similarity < min_similarity_qa:
                    min_similarity_qa = qa.similarity
                if max_similarity_qa is None or qa.similarity > max_similarity_qa:
                    max_similarity_qa = qa.similarity

                if min_similarity_it_qa is None or qa.similarity < min_similarity_it_qa:
                    min_similarity_it_qa = qa.similarity
                if max_similarity_it_qa is None or qa.similarity > max_similarity_it_qa:
                    max_similarity_it_qa = qa.similarity

                total_similarity_qa_it += qa.similarity
                partial_similarity_qa += qa.similarity

                if min_duration_qa is None or duration_qa < min_duration_qa:
                    min_duration_qa = duration_qa
                    min_duration_qa_text = qa.question
                    min_duration_qa_doc = doc_name
                if max_duration_qa is None or duration_qa > max_duration_qa:
                    max_duration_qa = duration_qa
                    max_duration_qa_text = qa.question
                    max_duration_qa_doc = doc_name

                if min_duration_it_qa is None or duration_qa < min_duration_it_qa:
                    min_duration_it_qa = duration_qa
                    min_duration_it_qa_text = qa.question
                    min_duration_it_qa_doc = doc_name
                if max_duration_it_qa is None or duration_qa > max_duration_it_qa:
                    max_duration_it_qa = duration_qa
                    max_duration_it_qa_text = qa.question
                    max_duration_it_qa_doc = doc_name

                total_duration_qa_it += duration_qa.total_seconds()
                count_qa_it += 1

        # Aggiorna le statistiche per i documenti in inglese
        if eval_doc.lang == "en":
            if min_duration_en is None or duration < min_duration_en:
                min_duration_en = duration
                min_doc_name_en = doc_name
            if max_duration_en is None or duration > max_duration_en:
                max_duration_en = duration
                max_doc_name_en = doc_name
            total_duration_en += duration.total_seconds()
            count_en += 1

            # Aggiorna le statistiche per le domande in inglese
            for qa in eval_doc.eval_qa_list:
                eval_qa_start = datetime.datetime.strptime(qa.eval_qa_start_date, DATE_FORMAT)
                eval_qa_end = datetime.datetime.strptime(qa.eval_qa_end_date, DATE_FORMAT)
                duration_qa = eval_qa_end - eval_qa_start

                if qa.translated:
                    qaOri = None

                    for qa2 in eval_doc.eval_qa_list:
                        if not qa2.translated and qa.id == qa2.id:
                            qaOri = qa2
                            break

                    if qaOri is not None:
                        translation_similarity_diff = qaOri.similarity - qa.similarity
                        count_translations_similarity_diff += 1
                        total_translations_similarity_diff = translation_similarity_diff

                        if min_translations_similarity_diff is None or translation_similarity_diff < min_translations_similarity_diff:
                            min_translations_similarity_diff = translation_similarity_diff
                        if max_translations_similarity_diff is None or translation_similarity_diff > max_translations_similarity_diff:
                            max_translations_similarity_diff = translation_similarity_diff

                if min_score_qa is None or qa.answer["score"] < min_score_qa:
                    min_score_qa = qa.answer["score"]
                if max_score_qa is None or qa.answer["score"] > max_score_qa:
                    max_score_qa = qa.answer["score"]

                if min_score_en_qa is None or qa.answer["score"] < min_score_en_qa:
                    min_score_en_qa = qa.answer["score"]
                if max_score_en_qa is None or qa.answer["score"] > max_score_en_qa:
                    max_score_en_qa = qa.answer["score"]

                total_score_qa_en += qa.answer["score"]
                partial_score_qa += qa.answer["score"]

                if min_similarity_qa is None or qa.similarity < min_similarity_qa:
                    min_similarity_qa = qa.similarity
                if max_similarity_qa is None or qa.similarity > max_similarity_qa:
                    max_similarity_qa = qa.similarity

                if min_similarity_en_qa is None or qa.similarity < min_similarity_en_qa:
                    min_similarity_en_qa = qa.similarity
                if max_similarity_en_qa is None or qa.similarity > max_similarity_en_qa:
                    max_similarity_en_qa = qa.similarity

                total_similarity_qa_en += qa.similarity
                partial_similarity_qa += qa.similarity

                if min_duration_qa is None or duration_qa < min_duration_qa:
                    min_duration_qa = duration_qa
                    min_duration_qa_text = qa.question
                    min_duration_qa_doc = doc_name
                if max_duration_qa is None or duration_qa > max_duration_qa:
                    max_duration_qa = duration_qa
                    max_duration_qa_text = qa.question
                    max_duration_qa_doc = doc_name

                if min_duration_en_qa is None or duration_qa < min_duration_en_qa:
                    min_duration_en_qa = duration_qa
                    min_duration_en_qa_text = qa.question
                    min_duration_en_qa_doc = doc_name
                if max_duration_en_qa is None or duration_qa > max_duration_en_qa:
                    max_duration_en_qa = duration_qa
                    max_duration_en_qa_text = qa.question
                    max_duration_en_qa_doc = doc_name

                total_duration_qa_en += duration_qa.total_seconds()
                count_qa_en += 1

        # Calcola le statistiche parziali medie
        avg_partial_score_qa = partial_score_qa / len(eval_doc.eval_qa_list) if partial_score_qa > 0 else 0
        avg_partial_similarity_qa = partial_similarity_qa / len(eval_doc.eval_qa_list) if partial_similarity_qa > 0 else 0

        print_checkpoint("Documento: " + doc_name + " - Numero di pagine: " + str(eval_doc.page_num) + " - Numero di domande: " + str(len(eval_doc.eval_qa_list)) + " - Durata elaborazione: " + str(duration) + " - Score medio: " + str(avg_partial_score_qa) + " - Correttezza media: " + str(avg_partial_similarity_qa))

    # Calcola le statistiche globali medie
    avg_duration_all = total_duration_all / count_all
    avg_duration_it = total_duration_it / count_it if count_it > 0 else 0
    avg_duration_en = total_duration_en / count_en if count_en > 0 else 0
    avg_duration_qa = (total_duration_qa_it + total_duration_qa_en) / (count_qa_it + count_qa_en) if (count_qa_it + count_qa_en) > 0 else 0
    avg_duration_qa_it = total_duration_qa_it / count_qa_it if count_qa_it > 0 else 0
    avg_duration_qa_en = total_duration_qa_en / count_qa_en if count_qa_en > 0 else 0
    avg_score_qa = (total_score_qa_it + total_score_qa_en) / (count_qa_it + count_qa_en) if (count_qa_it + count_qa_en) > 0 else 0
    avg_score_qa_it = total_score_qa_it / count_qa_it if count_qa_it > 0 else 0
    avg_score_qa_en = total_score_qa_en / count_qa_en if count_qa_en > 0 else 0
    avg_similarity_qa = (total_similarity_qa_it + total_similarity_qa_en) / (count_qa_it + count_qa_en) if (count_qa_it + count_qa_en) > 0 else 0
    avg_similarity_qa_it = total_similarity_qa_it / count_qa_it if count_qa_it > 0 else 0
    avg_similarity_qa_en = total_similarity_qa_en / count_qa_en if count_qa_en > 0 else 0
    avg_translation_similarity_diff = total_translations_similarity_diff / count_translations_similarity_diff if count_translations_similarity_diff > 0 else 0

    print_checkpoint("")
    print_checkpoint("")
    print_checkpoint("")

    print_checkpoint("#################### STATISTICHE GLOBALI ####################")

    print_checkpoint("")

    # Stampa le statistiche
    print_checkpoint("Durata minima di elaborazione tra tutti i documenti: " + str(min_duration_all) +  " per il documento " + min_doc_name_all)
    print_checkpoint("Durata massima di elaborazione tra tutti i documenti: " + str(max_duration_all) + " per il documento " + max_doc_name_all)
    print_checkpoint("Durata media di elaborazione tra tutti i documenti: " + str(avg_duration_all))

    print_checkpoint("")

    print_checkpoint("Durata minima di elaborazione tra i documenti in italiano: " + str(min_duration_it) + " per il documento " + min_doc_name_it)
    print_checkpoint("Durata massima di elaborazione tra i documenti in italiano: " + str(max_duration_it) + " per il documento " + max_doc_name_it)
    print_checkpoint("Durata media di elaborazione tra i documenti in italiano: " + str(avg_duration_it))

    print_checkpoint("")

    print_checkpoint("Durata minima di elaborazione tra i documenti in inglese: " + str(min_duration_en) + " per il documento " + min_doc_name_en)
    print_checkpoint("Durata massima di elaborazione tra i documenti in inglese: " + str(max_duration_en) + " per il documento " + max_doc_name_en)
    print_checkpoint("Durata media di elaborazione tra i documenti in inglese: " + str(avg_duration_en))

    print_checkpoint("")

    print_checkpoint("Durata minima di elaborazione tra tutte le domande: " + str(min_duration_qa) + " per il documento " + min_duration_qa_doc)
    print_checkpoint("     Testo della domanda: " + min_duration_qa_text)
    print_checkpoint("Durata massima di elaborazione tra tutte le domande: " + str(max_duration_qa) + " per il documento " + max_duration_qa_doc)
    print_checkpoint("     Testo della domanda: " + max_duration_qa_text)
    print_checkpoint("Durata media di elaborazione tra tutte le domande: " + str(avg_duration_qa))

    print_checkpoint("")

    print_checkpoint("Durata minima di elaborazione tra tutte le domande in italiano: " + str(min_duration_it_qa) + " per il documento " + min_duration_it_qa_doc)
    print_checkpoint("     Testo della domanda: " + min_duration_it_qa_text)
    print_checkpoint("Durata massima di elaborazione tra tutte le domande in italiano: " + str(max_duration_it_qa) + " per il documento " + max_duration_it_qa_doc)
    print_checkpoint("     Testo della domanda: " + max_duration_it_qa_text)
    print_checkpoint("Durata media di elaborazione tra tutte le domande in italiano: " + str(avg_duration_qa_it))

    print_checkpoint("")

    print_checkpoint("Durata minima di elaborazione tra tutte le domande in inglese: " + str(min_duration_en_qa) + " per il documento " + min_duration_en_qa_doc)
    print_checkpoint("     Testo della domanda: " + min_duration_en_qa_text)
    print_checkpoint("Durata massima di elaborazione tra tutte le domande in inglese: " + str(max_duration_en_qa) + " per il documento " + max_duration_en_qa_doc)
    print_checkpoint("     Testo della domanda: " + max_duration_en_qa_text)
    print_checkpoint("Durata media di elaborazione tra tutte le domande in inglese: " + str(avg_duration_qa_en))

    print_checkpoint("")

    print_checkpoint("Score minimo tra le risposte alle domande di tutti i documenti: " + str(min_score_qa))
    print_checkpoint("Score massimo tra le risposte alle domande di tutti i documenti: " + str(max_score_qa))
    print_checkpoint("Score medio tra le risposte alle domande di tutti i documenti: " + str(avg_score_qa))

    print_checkpoint("")

    print_checkpoint("Score minimo tra le risposte alle domande di tutti i documenti in italiano: " + str(min_score_it_qa))
    print_checkpoint("Score massimo tra le risposte alle domande di tutti i documenti in italiano: " + str(max_score_it_qa))
    print_checkpoint("Score medio tra le risposte alle domande di tutti i documenti in italiano: " + str(avg_score_qa_it))

    print_checkpoint("")

    print_checkpoint("Score minimo tra le risposte alle domande di tutti i documenti in inglese: " + str(min_score_en_qa))
    print_checkpoint("Score massimo tra le risposte alle domande di tutti i documenti in inglese: " + str(max_score_en_qa))
    print_checkpoint("Score medio tra le risposte alle domande di tutti i documenti in inglese: " + str(avg_score_qa_en))

    print_checkpoint("")

    print_checkpoint("Correttezza minima tra le risposte alle domande di tutti i documenti: " + str(min_similarity_qa))
    print_checkpoint("Correttezza massima tra le risposte alle domande di tutti i documenti: " + str(max_similarity_qa))
    print_checkpoint("Correttezza media tra le risposte alle domande di tutti i documenti: " + str(avg_similarity_qa))

    print_checkpoint("")

    print_checkpoint("Correttezza minima tra le risposte alle domande di tutti i documenti in italiano: " + str(min_similarity_it_qa))
    print_checkpoint("Correttezza massima tra le risposte alle domande di tutti i documenti in italiano: " + str(max_similarity_it_qa))
    print_checkpoint("Correttezza media tra le risposte alle domande di tutti i documenti in italiano: " + str(avg_similarity_qa_it))

    print_checkpoint("")

    print_checkpoint("Correttezza minima tra le risposte alle domande di tutti i documenti in inglese: " + str(min_similarity_en_qa))
    print_checkpoint("Correttezza massima tra le risposte alle domande di tutti i documenti in inglese: " + str(max_similarity_en_qa))
    print_checkpoint("Correttezza media tra le risposte alle domande di tutti i documenti in inglese: " + str(avg_similarity_qa_en))

    print_checkpoint("")
    # Incertezza intesa come differenza tra la correttazza della risposta originale e quella tradotta
    print_checkpoint("Incertezza minima nella traduzione di domande e risposte sottoposte ai documenti: " + str(-1 * min_translations_similarity_diff))
    print_checkpoint("Incertezza massima nella traduzione di domande e risposte sottoposte ai documenti: " + str(-1 * max_translations_similarity_diff))
    print_checkpoint("Incertezza media nella traduzione di domande e risposte sottoposte ai documenti: " + str(-1 * avg_translation_similarity_diff))
    print_checkpoint("(I valori positivi indicano un guadagno)")

    print_checkpoint("")
    print_checkpoint("")

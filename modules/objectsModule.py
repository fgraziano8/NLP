class Document:
    def __init__(self, name, text, lang, qa_list):
        self.name = name
        self.text = text
        self.lang = lang
        self.qa_list = qa_list

    def __json__(self):
        return {
            "name": self.name,
            # "text": self.text,
            "lang": self.lang,
            "qa_list": [qa.__json__() for qa in self.qa_list]
        }


class QuestionAnswer:
    def __init__(self, question, questionLang, translation, translatedQuestion, translatedQuestionLang, answer):
        self.question = question
        self.questionLang = questionLang
        self.translation = translation
        self.translatedQuestion = translatedQuestion
        self.translatedQuestionLang = translatedQuestionLang
        self.answer = answer

    def __json__(self):
        output_order = ["question", "questionLang", "translation", "translatedQuestion", "translatedQuestionLang", "answer"]
        output_dict = {k: getattr(self, k) for k in output_order if getattr(self, k) is not None}
        if not self.translation:
            output_dict.pop("translatedQuestion", None)
            output_dict.pop("translatedQuestionLang", None)
        return output_dict


class Answer:
    def __init__(self, answer, printedAnswer, answerLang, translation, translatedAnswer, translatedAnswerLang, score, start, end):
        self.answer = answer
        self.printedAnswer = printedAnswer
        self.answerLang = answerLang
        self.translation = translation
        self.translatedAnswer = translatedAnswer
        self.translatedAnswerLang = translatedAnswerLang
        self.score = score
        self.start = start
        self.end = end

    def __json__(self):
        output_order = ["answer", "printedAnswer", "answerLang", "translation", "translatedAnswer", "translatedAnswerLang", "score", "start", "end"]
        output_dict = {k: getattr(self, k) for k in output_order if getattr(self, k) is not None}
        if not self.translation:
            output_dict.pop("translatedAnswer", None)
            output_dict.pop("translatedAnswerLang", None)
        return output_dict


class Configurations:
    def __init__(self):
        self.start_date = None
        self.end_date = None
        self.log_level = None
        self.log_format = None
        self.log_file = None
        self.document_path = None
        self.supported_languages = None
        self.supported_extensions = None
        self.initial_message = None
        self.insert_file_name = None
        self.insert_question = None
        self.answer = None
        self.qa_it = None
        self.qa_it_sensitivity = None
        self.qa_en = None
        self.qa_en_sensitivity = None
        self.sentence_similarity = None
        self.output_path = None
        self.output_date_format = None
        self.chat_date_format = None
        self.background_color = None
        self.entry_background_color = None
        self.entry_text_color = None
        self.send_background_color = None
        self.send_active_background_color = None
        self.send_text_color = None
        self.messages_background_color = None
        self.messages_text_color = None
        self.response_background_color = None
        self.response_text_color = None
        self.font = None

    def __json__(self):
        output_order = ["start_date", "end_date", "log_level", "log_format", "log_file", "document_path", "supported_languages", "supported_extensions", "initial_message", "insert_file_name", "insert_question", "answer", "qa_it", "qa_it_sensitivity", "qa_en", "qa_en_sensitivity", "sentence_similarity", "output_path", "output_date_format", "chat_date_format", "background_color", "entry_background_color", "entry_text_color", "send_background_color", "send_active_background_color", "send_text_color", "messages_background_color", "messages_text_color", "response_background_color", "response_text_color", "font"]
        output_dict = {k: getattr(self, k) for k in output_order if getattr(self, k) is not None}

        return output_dict


class EvaluationDocuments:
    def __init__(self, name, page_num, lang, eval_qa_list, eval_start_date=None, eval_end_date=None):
        self.name = name
        self.page_num = page_num
        self.lang = lang
        self.eval_qa_list = eval_qa_list
        self.eval_start_date = eval_start_date
        self.eval_end_date = eval_end_date

    def __json__(self):
        return {
            "name": self.name,
            "page_num": self.page_num,
            "lang": self.lang,
            "eval_start_date": self.eval_start_date,
            "eval_end_date": self.eval_end_date,
            "eval_qa_list": [qa.__json__() for qa in self.eval_qa_list]
        }


class EvaluationQA:
    def __init__(self, idQA, question, lang, question_page, expected_answer, answer=None, eval_qa_start_date=None, eval_qa_end_date=None, translated=None, similarity=None):
        self.id = idQA
        self.question = question
        self.lang = lang
        self.question_page = question_page
        self.expected_answer = expected_answer
        self.answer = answer
        self.eval_qa_start_date = eval_qa_start_date
        self.eval_qa_end_date = eval_qa_end_date
        self.translated = translated
        self.similarity = similarity

    def __json__(self):
        output_order = ["eval_qa_start_date", "eval_qa_end_date", "id", "question", "lang", "translated", "question_page", "expected_answer", "answer", "similarity"]
        output_dict = {k: getattr(self, k) for k in output_order if getattr(self, k) is not None}

        return output_dict


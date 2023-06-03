import configparser
import logging
import datetime
from modules.objectsModule import Configurations

LOG_SECTION = "LOG"
DOCUMENTS_SECTION = "DOCUMENTS"
LABELS_SECTION = "LABELS"
CHECKPOINTS_SECTION = "CHECKPOINTS"
OUTPUT_SECTION = "OUTPUT"
INTERFACE_SECTION = "INTERFACE"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"
processedDocuments = {}
config = Configurations()


def load_configurations(file_name):
    now = datetime.datetime.now()
    formatted_date = now.strftime(DATE_FORMAT)

    try:
        configDict = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        configDict.read(file_name)

        languages = configDict[DOCUMENTS_SECTION]["supportedLanguages"]
        extensions = configDict[DOCUMENTS_SECTION]["supportedExtensions"]

        config.start_date = formatted_date
        config.log_level = configDict[LOG_SECTION]["level"]
        config.log_format = configDict[LOG_SECTION]["format"]
        config.log_file = configDict[LOG_SECTION]["file"]
        config.document_path = configDict[DOCUMENTS_SECTION]["path"]
        config.initial_message = configDict[LABELS_SECTION]["messaggioIniziale"] + " "
        config.insert_file_name = configDict[LABELS_SECTION]["inserimentoNomeFile"] + " "
        config.insert_question = configDict[LABELS_SECTION]["inserimentoDomanda"] + " "
        config.answer = configDict[LABELS_SECTION]["risposta"] + " "
        config.qa_it = configDict[CHECKPOINTS_SECTION]["qa_it"]
        config.qa_it_sensitivity = float(configDict[CHECKPOINTS_SECTION]["qa_it_sensitivity"])
        config.qa_en = configDict[CHECKPOINTS_SECTION]["qa_en"]
        config.qa_en_sensitivity = float(configDict[CHECKPOINTS_SECTION]["qa_en_sensitivity"])
        config.sentence_similarity = configDict[CHECKPOINTS_SECTION]["sentence_similarity"]
        config.output_path = configDict[OUTPUT_SECTION]["path"]
        config.output_date_format = configDict[OUTPUT_SECTION]["dateFormat"]
        config.supported_languages = [lang.strip() for lang in languages.split(",")]
        config.supported_extensions = [ext.strip() for ext in extensions.split(",")]
        config.chat_date_format = configDict[INTERFACE_SECTION]["chat_date_format"]
        config.background_color = configDict[INTERFACE_SECTION]["background_color"]
        config.entry_background_color = configDict[INTERFACE_SECTION]["entry_background_color"]
        config.entry_text_color = configDict[INTERFACE_SECTION]["entry_text_color"]
        config.send_background_color = configDict[INTERFACE_SECTION]["send_background_color"]
        config.send_active_background_color = configDict[INTERFACE_SECTION]["send_active_background_color"]
        config.send_text_color = configDict[INTERFACE_SECTION]["send_text_color"]
        config.messages_background_color = configDict[INTERFACE_SECTION]["messages_background_color"]
        config.messages_text_color = configDict[INTERFACE_SECTION]["messages_text_color"]
        config.response_background_color = configDict[INTERFACE_SECTION]["response_background_color"]
        config.response_text_color = configDict[INTERFACE_SECTION]["response_text_color"]
        config.font = configDict[INTERFACE_SECTION]["font"]
    except KeyError as k:
        logging.error("KeyError - Impossibile trovare il valore " + str(k) + " nel file " + file_name)
        raise
    except NameError:
        logging.error("NameError - Impossibile trovare il file " + file_name)
        raise
    except Exception as e:
        logging.error("Exception - Eccezione durante la lettura del file " + file_name + " - " + str(e))
        raise


def init():
    load_configurations("config.ini")
    # Configura il logger
    logging.basicConfig(format=config.log_format, filename=config.log_file, level=config.log_level)

    logging.info('Inizializzazione dei parametri...')
    logging.info(config)
    logging.info('Inizializzazione terminata.')


def log_calls(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Invocata {func.__name__} con argomenti: {args}")
        return func(*args, **kwargs)

    return wrapper

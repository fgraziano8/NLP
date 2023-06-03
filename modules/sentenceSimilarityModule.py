from modules import configModule
from sentence_transformers import SentenceTransformer, util


@configModule.log_calls
def get_similarity(sentence1, sentence2):
    # Caricamento del modello SentenceTransformer preaddestrato
    model = SentenceTransformer(configModule.config.sentence_similarity)

    # Calcolo degli embedding per entrambe le frasi
    embedding_1 = model.encode(sentence1, convert_to_tensor=True)
    embedding_2 = model.encode(sentence2, convert_to_tensor=True)

    # Calcolo della similarità coseno tra i due vettori di embedding
    res = util.pytorch_cos_sim(embedding_1, embedding_2)

    # Calcolo di similarità coseno
    similarity_score = res[0, 0].item()

    # Ritorna il valore di similarità coseno arrotondato
    return similarity_score

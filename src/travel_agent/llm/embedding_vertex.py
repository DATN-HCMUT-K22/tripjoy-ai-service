from vertexai.language_models import TextEmbeddingModel


class VertexEmbedding:
    def __init__(self):
        self.model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    def embed(self, texts: list[str]):
        """
        Nhận vào list[str] và trả về list[list[float]]
        """
        if not texts:
            return []  # tránh lỗi Unsupported input []

        embeddings = self.model.get_embeddings(texts)
        return [e.values for e in embeddings]

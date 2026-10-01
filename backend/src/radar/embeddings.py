"""Embeddings locais; nenhum texto é enviado ao provedor de geração."""
import hashlib
import os
from functools import lru_cache

from langchain_core.embeddings import Embeddings
from .config import private_root

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DIMENSIONS = 384


class LocalEmbeddings(Embeddings):
    def __init__(self):
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
        from fastembed import TextEmbedding
        from tokenizers import Tokenizer
        self.engine = TextEmbedding(MODEL, cache_dir=str(private_root() / "models"), threads=2,
                                    providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_str(self.engine.model.tokenizer.to_str())
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()

    def token_count(self, text):
        return len(self.tokenizer.encode(text, add_special_tokens=False).ids)

    def provenance(self):
        directory = self.engine.model._model_dir
        files = {}
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix in (".onnx", ".json"):
                files[str(path.relative_to(directory))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"model": MODEL, "dimensions": DIMENSIONS, "max_tokens": 128, "files": files}

    def embed_documents(self, texts):
        if any(self.token_count(t) > 126 for t in texts):
            raise ValueError("Texto excede a janela do modelo")
        return [v.tolist() for v in self.engine.passage_embed(texts, batch_size=8)]

    def embed_query(self, text):
        if not text.strip() or self.token_count(text) > 126:
            raise ValueError("Consulta vazia ou longa demais")
        return next(self.engine.query_embed(text)).tolist()


@lru_cache(maxsize=1)
def local_embeddings():
    return LocalEmbeddings()

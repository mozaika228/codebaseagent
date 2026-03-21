from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from chromadb import PersistentClient

from ..config import VECTOR_STORE_DIR


@dataclass
class ChromaStore:
  collection: str

  def _client(self):
    return PersistentClient(path=str(VECTOR_STORE_DIR))

  def _collection(self):
    return self._client().get_or_create_collection(self.collection)

  def add_documents(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict[str, Any]], documents: list[str]) -> None:
    if not ids:
      return
    self._collection().upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)

  def query(self, query_embeddings: list[list[float]], n_results: int = 5) -> dict[str, Any]:
    return self._collection().query(query_embeddings=query_embeddings, n_results=n_results)

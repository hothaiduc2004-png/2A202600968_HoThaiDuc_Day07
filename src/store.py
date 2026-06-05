from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            self._use_chroma = True
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(name=collection_name)
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        embedding = self._embedding_fn(doc.content)
        return {
            'id': doc.id,
            'content': doc.content,
            'metadata': doc.metadata.copy() if doc.metadata else {},
            'embedding': embedding
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        query_embedding = self._embedding_fn(query)
        
        # Compute similarity scores
        scored = []
        for record in records:
            score = _dot(query_embedding, record['embedding'])
            scored.append({**record, 'score': score})
        
        # Sort by score descending and return top_k
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        if self._use_chroma and self._collection:
            # ChromaDB path
            ids = []
            documents = []
            embeddings = []
            
            for doc in docs:
                ids.append(doc.id)
                documents.append(doc.content)
                embeddings.append(self._embedding_fn(doc.content))
            
            self._collection.add(ids=ids, documents=documents, embeddings=embeddings)
        else:
            # In-memory path
            for doc in docs:
                record = self._make_record(doc)
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        if self._use_chroma and self._collection:
            # ChromaDB path
            results = self._collection.query(query_texts=[query], n_results=top_k)
            # Format results to match in-memory format
            formatted = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    formatted.append({
                        'content': doc,
                        'score': results['distances'][0][i] if results['distances'] else 0.0
                    })
            return formatted
        else:
            # In-memory path
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        if self._use_chroma and self._collection:
            return self._collection.count()
        else:
            return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        if metadata_filter is None:
            return self.search(query, top_k)
        
        if self._use_chroma and self._collection:
            # ChromaDB path - use where filter
            results = self._collection.query(query_texts=[query], n_results=top_k, where=metadata_filter)
            formatted = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    formatted.append({
                        'content': doc,
                        'score': results['distances'][0][i] if results['distances'] else 0.0
                    })
            return formatted
        else:
            # In-memory path - filter then search
            filtered_records = []
            for record in self._store:
                # Check if all filter conditions match
                match = True
                for key, value in metadata_filter.items():
                    if record['metadata'].get(key) != value:
                        match = False
                        break
                if match:
                    filtered_records.append(record)
            
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        if self._use_chroma and self._collection:
            try:
                self._collection.delete(ids=[doc_id])
                return True
            except Exception:
                return False
        else:
            # In-memory path
            initial_size = len(self._store)
            self._store = [r for r in self._store if r['id'] != doc_id]
            return len(self._store) < initial_size

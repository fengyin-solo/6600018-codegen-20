"""Collection service for managing themed ancient book collections."""
import uuid
import time
from typing import List, Dict, Optional, Any

from app.models.schemas import (
    Collection,
    CollectionCreate,
    CollectionUpdate,
    CollectionSearchResult,
    Document,
    OCRResult
)


class CollectionService:
    def __init__(self):
        self._collections: Dict[str, Collection] = {}
        self._documents: Dict[str, Document] = {}

    def create_collection(self, data: CollectionCreate) -> Collection:
        now = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        collection = Collection(
            id=str(uuid.uuid4()),
            name=data.name,
            description=data.description,
            category=data.category,
            document_ids=[],
            created_at=now,
            updated_at=now,
        )
        self._collections[collection.id] = collection
        return collection

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        return self._collections.get(collection_id)

    def list_collections(self, category: Optional[str] = None) -> List[Collection]:
        items = list(self._collections.values())
        if category:
            items = [c for c in items if c.category == category]
        return sorted(items, key=lambda c: c.updated_at, reverse=True)

    def update_collection(self, collection_id: str, data: CollectionUpdate) -> Optional[Collection]:
        collection = self._collections.get(collection_id)
        if not collection:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(collection, key, value)
        collection.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        return collection

    def delete_collection(self, collection_id: str) -> bool:
        if collection_id in self._collections:
            del self._collections[collection_id]
            return True
        return False

    def add_document_to_collection(self, collection_id: str, document_id: str) -> Optional[Collection]:
        collection = self._collections.get(collection_id)
        if not collection:
            return None
        if document_id not in collection.document_ids:
            collection.document_ids.append(document_id)
            collection.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        return collection

    def remove_document_from_collection(self, collection_id: str, document_id: str) -> Optional[Collection]:
        collection = self._collections.get(collection_id)
        if not collection:
            return None
        if document_id in collection.document_ids:
            collection.document_ids.remove(document_id)
            collection.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        return collection

    def register_document(self, document: Document) -> Document:
        self._documents[document.id] = document
        return document

    def get_document(self, document_id: str) -> Optional[Document]:
        return self._documents.get(document_id)

    def get_collection_documents(self, collection_id: str) -> List[Document]:
        collection = self._collections.get(collection_id)
        if not collection:
            return []
        docs = []
        for did in collection.document_ids:
            doc = self._documents.get(did)
            if doc:
                docs.append(doc)
        return docs

    def search_in_collection(self, collection_id: str, query: str) -> List[CollectionSearchResult]:
        docs = self.get_collection_documents(collection_id)
        results: List[CollectionSearchResult] = []
        q = query.lower()
        for doc in docs:
            for r in doc.results:
                text = (r.corrected or r.text).lower()
                if q in text:
                    results.append(CollectionSearchResult(
                        document_id=doc.id,
                        document_name=doc.name,
                        result=r
                    ))
        return results

    def export_collection_tei(self, collection_id: str) -> Optional[str]:
        collection = self._collections.get(collection_id)
        if not collection:
            return None
        docs = self.get_collection_documents(collection_id)
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<TEI xmlns="http://www.tei-c.org/ns/1.0">')
        lines.append('  <teiHeader>')
        lines.append('    <fileDesc>')
        lines.append(f'      <titleStmt><title>{collection.name}</title>')
        if collection.description:
            lines.append(f'        <note type="description">{collection.description}</note>')
        lines.append('      </titleStmt>')
        lines.append('    </fileDesc>')
        lines.append('  </teiHeader>')
        lines.append('  <text>')
        lines.append('    <body>')
        lines.append(f'      <div type="collection" xml:id="col_{collection.id}">')
        lines.append(f'        <head>{collection.name}</head>')
        if collection.category:
            lines.append(f'        <note type="category">{collection.category}</note>')
        for doc in docs:
            lines.append(f'        <div type="document" xml:id="doc_{doc.id}">')
            lines.append(f'          <head>{doc.name}</head>')
            for r in doc.results:
                lines.append(
                    f'          <seg type="line" xml:id="{r.id}" cert="{r.confidence:.2f}">{r.corrected or r.text}</seg>'
                )
            for a in doc.annotations:
                lines.append(
                    f'          <note type="{a.type}" label="{a.label}" xml:id="{a.id}">{a.content}</note>'
                )
            lines.append('        </div>')
        lines.append('      </div>')
        lines.append('    </body>')
        lines.append('  </text>')
        lines.append('</TEI>')
        return "\n".join(lines)


collection_service = CollectionService()

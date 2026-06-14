"""Collection service for managing themed ancient book collections.

This service uses module-level persistent storage so that data is preserved
across API request-response cycles. It also guarantees documents are always
registered when added to a collection, so search and export always produce
complete results.
"""
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


_COLLECTIONS: Dict[str, Collection] = {}
_DOCUMENTS: Dict[str, Document] = {}
_DOC_COLLECTIONS_INDEX: Dict[str, List[str]] = {}


class CollectionService:
    def __init__(self):
        self._collections: Dict[str, Collection] = _COLLECTIONS
        self._documents: Dict[str, Document] = _DOCUMENTS
        self._doc_col_idx: Dict[str, List[str]] = _DOC_COLLECTIONS_INDEX

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
            col = self._collections[collection_id]
            for did in col.document_ids:
                if did in self._doc_col_idx:
                    self._doc_col_idx[did] = [c for c in self._doc_col_idx[did] if c != collection_id]
            del self._collections[collection_id]
            return True
        return False

    def add_document_to_collection(
        self,
        collection_id: str,
        document_id: str,
        document_data: Optional[Document] = None,
    ) -> Optional[Collection]:
        collection = self._collections.get(collection_id)
        if not collection:
            return None

        if document_data is not None:
            self._documents[document_data.id] = document_data
            document_id = document_data.id
        elif document_id and document_id not in self._documents:
            pass

        if document_id not in collection.document_ids:
            collection.document_ids.append(document_id)
            collection.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())

        if document_id not in self._doc_col_idx:
            self._doc_col_idx[document_id] = []
        if collection_id not in self._doc_col_idx[document_id]:
            self._doc_col_idx[document_id].append(collection_id)

        return collection

    def remove_document_from_collection(self, collection_id: str, document_id: str) -> Optional[Collection]:
        collection = self._collections.get(collection_id)
        if not collection:
            return None
        if document_id in collection.document_ids:
            collection.document_ids.remove(document_id)
            collection.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            if document_id in self._doc_col_idx:
                self._doc_col_idx[document_id] = [c for c in self._doc_col_idx[document_id] if c != collection_id]
        return collection

    def register_document(self, document: Document) -> Document:
        self._documents[document.id] = document
        return document

    def get_document(self, document_id: str) -> Optional[Document]:
        return self._documents.get(document_id)

    def list_all_documents(self) -> List[Document]:
        return list(self._documents.values())

    def get_collection_documents(self, collection_id: str) -> List[Document]:
        collection = self._collections.get(collection_id)
        if not collection:
            return []
        docs: List[Document] = []
        missing_ids: List[str] = []
        for did in collection.document_ids:
            doc = self._documents.get(did)
            if doc:
                docs.append(doc)
            else:
                missing_ids.append(did)
        if missing_ids:
            pass
        id_order = {did: i for i, did in enumerate(collection.document_ids)}
        docs.sort(key=lambda d: id_order.get(d.id, 99999))
        return docs

    def search_in_collection(self, collection_id: str, query: str) -> List[CollectionSearchResult]:
        docs = self.get_collection_documents(collection_id)
        results: List[CollectionSearchResult] = []
        q = query.lower()
        for doc in docs:
            for r in doc.results:
                original = (r.corrected or r.text).lower()
                if q in original or q in r.text.lower():
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
        lines.append(f'      <titleStmt><title>{self._xml_escape(collection.name)}</title>')
        if collection.description:
            lines.append(f'        <note type="description">{self._xml_escape(collection.description)}</note>')
        lines.append('      </titleStmt>')
        lines.append('      <publicationStmt><p>Generated by Ancient-Text OCR Platform</p></publicationStmt>')
        lines.append('      <sourceDesc>')
        lines.append(f'        <p>Collection: {self._xml_escape(collection.name)}; Documents: {len(docs)}</p>')
        lines.append('      </sourceDesc>')
        lines.append('    </fileDesc>')
        if collection.category:
            lines.append('    <profileDesc>')
            lines.append(f'      <textClass><catRef target="{self._xml_escape(collection.category)}"/></textClass>')
            lines.append('    </profileDesc>')
        lines.append('  </teiHeader>')
        lines.append('  <text>')
        lines.append('    <body>')
        safe_id = self._safe_id(collection.id)
        lines.append(f'      <div type="collection" xml:id="col_{safe_id}">')
        lines.append(f'        <head>{self._xml_escape(collection.name)}</head>')
        if collection.category:
            lines.append(f'        <note type="category">{self._xml_escape(collection.category)}</note>')
        lines.append(f'        <note type="document-count">{len(docs)}</note>')
        for doc in docs:
            doc_safe_id = self._safe_id(doc.id)
            lines.append(f'        <div type="document" xml:id="doc_{doc_safe_id}" n="{doc.name}">')
            lines.append(f'          <head>{self._xml_escape(doc.name)}</head>')
            lines.append('          <div type="textbody">')
            for r in doc.results:
                content = self._xml_escape(r.corrected or r.text)
                lines.append(
                    f'            <seg type="line" xml:id="seg_{doc_safe_id}_{self._safe_id(r.id)}" cert="{r.confidence:.2f}">{content}</seg>'
                )
            lines.append('          </div>')
            if doc.annotations:
                lines.append('          <div type="annotations">')
                for a in doc.annotations:
                    ann_content = self._xml_escape(a.content)
                    ann_label = self._xml_escape(a.label)
                    lines.append(
                        f'            <note type="{self._xml_escape(a.type)}" label="{ann_label}" xml:id="ann_{doc_safe_id}_{self._safe_id(a.id)}">{ann_content}</note>'
                    )
                lines.append('          </div>')
            lines.append('        </div>')
        lines.append('      </div>')
        lines.append('    </body>')
        lines.append('  </text>')
        lines.append('</TEI>')
        return "\n".join(lines)

    @staticmethod
    def _xml_escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
        )

    @staticmethod
    def _safe_id(raw: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in raw).strip("_")


collection_service = CollectionService()

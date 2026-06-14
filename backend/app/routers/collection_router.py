from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from app.models.schemas import (
    Collection,
    CollectionCreate,
    CollectionUpdate,
    CollectionDocumentAdd,
    CollectionDocumentAddWithData,
    CollectionSearchResult,
    Document
)
from app.services.collection_service import collection_service

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=Collection)
def create_collection(data: CollectionCreate):
    return collection_service.create_collection(data)


@router.get("", response_model=List[Collection])
def list_collections(category: Optional[str] = Query(None)):
    return collection_service.list_collections(category)


@router.get("/{collection_id}", response_model=Collection)
def get_collection(collection_id: str):
    collection = collection_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.put("/{collection_id}", response_model=Collection)
def update_collection(collection_id: str, data: CollectionUpdate):
    collection = collection_service.update_collection(collection_id, data)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.delete("/{collection_id}")
def delete_collection(collection_id: str):
    ok = collection_service.delete_collection(collection_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"success": True}


@router.post("/{collection_id}/documents", response_model=Collection)
def add_document(collection_id: str, data: CollectionDocumentAdd):
    collection = collection_service.add_document_to_collection(
        collection_id=collection_id,
        document_id=data.document_id,
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.post("/{collection_id}/documents/with-data", response_model=Collection)
def add_document_with_data(collection_id: str, data: CollectionDocumentAddWithData):
    collection = collection_service.add_document_to_collection(
        collection_id=collection_id,
        document_id=data.document.id,
        document_data=data.document,
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.post("/documents/batch-sync", response_model=dict)
def batch_sync_documents(docs: List[Document]):
    for doc in docs:
        collection_service.register_document(doc)
    return {"synced": len(docs), "total_documents": len(collection_service.list_all_documents())}


@router.post("/documents/register", response_model=Document)
def register_document(doc: Document):
    return collection_service.register_document(doc)


@router.get("/documents/all", response_model=List[Document])
def list_all_documents():
    return collection_service.list_all_documents()


@router.delete("/{collection_id}/documents/{document_id}", response_model=Collection)
def remove_document(collection_id: str, document_id: str):
    collection = collection_service.remove_document_from_collection(collection_id, document_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.get("/{collection_id}/documents", response_model=List[Document])
def get_collection_documents(collection_id: str):
    collection = collection_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    docs = collection_service.get_collection_documents(collection_id)
    return docs


@router.get("/{collection_id}/documents/missing", response_model=dict)
def get_missing_documents(collection_id: str):
    collection = collection_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    docs = collection_service.get_collection_documents(collection_id)
    existing_ids = {d.id for d in docs}
    missing = [did for did in collection.document_ids if did not in existing_ids]
    return {
        "total_ids": len(collection.document_ids),
        "resolved": len(docs),
        "missing_ids": missing
    }


@router.get("/{collection_id}/search", response_model=List[CollectionSearchResult])
def search_collection(collection_id: str, query: str = Query(...)):
    collection = collection_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection_service.search_in_collection(collection_id, query)


@router.get("/{collection_id}/export/tei")
def export_collection_tei(collection_id: str):
    tei = collection_service.export_collection_tei(collection_id)
    if tei is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    from fastapi.responses import PlainTextResponse
    collection = collection_service.get_collection(collection_id)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in collection.name)
    filename = f"collection_{safe_name or collection_id}.xml"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return PlainTextResponse(tei, media_type="application/xml", headers=headers)

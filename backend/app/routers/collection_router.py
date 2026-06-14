from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from app.models.schemas import (
    Collection,
    CollectionCreate,
    CollectionUpdate,
    CollectionDocumentAdd,
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
    collection = collection_service.add_document_to_collection(collection_id, data.document_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.delete("/{collection_id}/documents/{document_id}", response_model=Collection)
def remove_document(collection_id: str, document_id: str):
    collection = collection_service.remove_document_from_collection(collection_id, document_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.post("/documents/register", response_model=Document)
def register_document(doc: Document):
    return collection_service.register_document(doc)


@router.get("/{collection_id}/documents", response_model=List[Document])
def get_collection_documents(collection_id: str):
    collection = collection_service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection_service.get_collection_documents(collection_id)


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
    filename = f"collection_{collection.name.replace(' ', '_')}.xml"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return PlainTextResponse(tei, media_type="application/xml", headers=headers)

from pydantic import BaseModel
from typing import List, Optional


class OCRResult(BaseModel):
    id: str
    text: str
    bbox: List[float]
    confidence: float
    corrected: Optional[str] = None


class Annotation(BaseModel):
    id: str
    type: str
    bbox: List[float]
    label: str
    content: str


class Document(BaseModel):
    id: str
    name: str
    image_url: str
    results: List[OCRResult]
    annotations: List[Annotation] = []
    created_at: str


class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class Collection(CollectionBase):
    id: str
    document_ids: List[str] = []
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CollectionDocumentAdd(BaseModel):
    document_id: str


class CollectionSearchResult(BaseModel):
    document_id: str
    document_name: str
    result: OCRResult


class CollectionExport(BaseModel):
    collection_id: str
    format: str = "tei"

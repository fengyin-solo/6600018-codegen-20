export interface OCRResult {
  id: string
  text: string
  bbox: [number, number, number, number]
  confidence: number
  corrected?: string
}

export interface Document {
  id: string
  name: string
  imageUrl: string
  results: OCRResult[]
  annotations: Annotation[]
  createdAt: string
}

export interface Annotation {
  id: string
  type: 'region' | 'character' | 'note'
  bbox: [number, number, number, number]
  label: string
  content: string
}

export interface VariantChar {
  ancient: string
  modern: string
  frequency: number
}

export interface Collection {
  id: string
  name: string
  description?: string
  category?: string
  documentIds: string[]
  createdAt: string
  updatedAt: string
}

export interface CollectionCreateInput {
  name: string
  description?: string
  category?: string
}

export interface CollectionUpdateInput {
  name?: string
  description?: string
  category?: string
}

export interface CollectionSearchResult {
  documentId: string
  documentName: string
  result: OCRResult
}

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type {
  Collection,
  CollectionCreateInput,
  CollectionUpdateInput,
  CollectionSearchResult,
  Document
} from '../types'

export const useCollectionStore = defineStore('collections', () => {
  const collections = ref<Collection[]>([])
  const currentCollection = ref<Collection | null>(null)
  const collectionDocuments = ref<Document[]>([])
  const collectionSearchResults = ref<CollectionSearchResult[]>([])
  const collectionSearchQuery = ref('')
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const MOCK_COLLECTIONS: Collection[] = [
    {
      id: 'mock-col-1',
      name: '论语全集',
      description: '儒家经典《论语》的完整合集',
      category: '儒家经典',
      documentIds: [],
      createdAt: '2025-01-15',
      updatedAt: '2025-01-20'
    }
  ]

  function loadMockCollections() {
    collections.value = [...MOCK_COLLECTIONS]
    currentCollection.value = MOCK_COLLECTIONS[0]
  }

  function _toCamelCase(obj: any): any {
    if (Array.isArray(obj)) return obj.map(_toCamelCase)
    if (obj !== null && typeof obj === 'object') {
      const result: any = {}
      for (const key of Object.keys(obj)) {
        const camelKey = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
        result[camelKey] = _toCamelCase(obj[key])
      }
      return result
    }
    return obj
  }

  function _toSnakeCase(obj: any): any {
    if (Array.isArray(obj)) return obj.map(_toSnakeCase)
    if (obj !== null && typeof obj === 'object') {
      const result: any = {}
      for (const key of Object.keys(obj)) {
        const snakeKey = key.replace(/[A-Z]/g, (c) => '_' + c.toLowerCase())
        result[snakeKey] = _toSnakeCase(obj[key])
      }
      return result
    }
    return obj
  }

  async function fetchCollections(category?: string) {
    isLoading.value = true
    error.value = null
    try {
      const params = category ? `?category=${encodeURIComponent(category)}` : ''
      const resp = await fetch(`/api/collections${params}`)
      if (resp.ok) {
        const data = await resp.json()
        collections.value = _toCamelCase(data)
      }
    } catch (e) {
      collections.value = [...MOCK_COLLECTIONS]
    } finally {
      isLoading.value = false
    }
  }

  async function createCollection(input: CollectionCreateInput) {
    isLoading.value = true
    error.value = null
    try {
      const resp = await fetch('/api/collections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(_toSnakeCase(input))
      })
      if (resp.ok) {
        const data = await resp.json()
        const col: Collection = _toCamelCase(data)
        collections.value.unshift(col)
        return col
      }
    } catch (e) {
      const now = new Date().toISOString()
      const col: Collection = {
        id: Date.now().toString(),
        name: input.name,
        description: input.description,
        category: input.category,
        documentIds: [],
        createdAt: now,
        updatedAt: now
      }
      collections.value.unshift(col)
      return col
    } finally {
      isLoading.value = false
    }
  }

  async function updateCollection(id: string, input: CollectionUpdateInput) {
    isLoading.value = true
    error.value = null
    try {
      const resp = await fetch(`/api/collections/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(_toSnakeCase(input))
      })
      if (resp.ok) {
        const data = await resp.json()
        const col: Collection = _toCamelCase(data)
        const idx = collections.value.findIndex(c => c.id === id)
        if (idx !== -1) collections.value[idx] = col
        if (currentCollection.value?.id === id) currentCollection.value = col
        return col
      }
    } catch (e) {
      const idx = collections.value.findIndex(c => c.id === id)
      if (idx !== -1) {
        collections.value[idx] = { ...collections.value[idx], ...input, updatedAt: new Date().toISOString() }
        return collections.value[idx]
      }
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCollection(id: string) {
    isLoading.value = true
    error.value = null
    try {
      const resp = await fetch(`/api/collections/${id}`, { method: 'DELETE' })
      if (resp.ok) {
        collections.value = collections.value.filter(c => c.id !== id)
        if (currentCollection.value?.id === id) {
          currentCollection.value = null
          collectionDocuments.value = []
          collectionSearchResults.value = []
        }
        return true
      }
    } catch (e) {
      collections.value = collections.value.filter(c => c.id !== id)
      if (currentCollection.value?.id === id) {
        currentCollection.value = null
        collectionDocuments.value = []
        collectionSearchResults.value = []
      }
      return true
    } finally {
      isLoading.value = false
    }
    return false
  }

  async function selectCollection(id: string | null) {
    if (id === null) {
      currentCollection.value = null
      collectionDocuments.value = []
      collectionSearchResults.value = []
      return
    }
    const col = collections.value.find(c => c.id === id)
    currentCollection.value = col || null
    if (col) {
      await fetchCollectionDocuments(id)
    }
  }

  async function addDocumentToCollection(collectionId: string, documentId: string) {
    isLoading.value = true
    try {
      const resp = await fetch(`/api/collections/${collectionId}/documents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: documentId })
      })
      if (resp.ok) {
        const data = await resp.json()
        const col: Collection = _toCamelCase(data)
        const idx = collections.value.findIndex(c => c.id === collectionId)
        if (idx !== -1) collections.value[idx] = col
        if (currentCollection.value?.id === collectionId) currentCollection.value = col
        return col
      }
    } catch (e) {
      const col = collections.value.find(c => c.id === collectionId)
      if (col && !col.documentIds.includes(documentId)) {
        col.documentIds.push(documentId)
        col.updatedAt = new Date().toISOString()
        return col
      }
    } finally {
      isLoading.value = false
    }
  }

  async function removeDocumentFromCollection(collectionId: string, documentId: string) {
    isLoading.value = true
    try {
      const resp = await fetch(`/api/collections/${collectionId}/documents/${documentId}`, { method: 'DELETE' })
      if (resp.ok) {
        const data = await resp.json()
        const col: Collection = _toCamelCase(data)
        const idx = collections.value.findIndex(c => c.id === collectionId)
        if (idx !== -1) collections.value[idx] = col
        if (currentCollection.value?.id === collectionId) {
          currentCollection.value = col
          collectionDocuments.value = collectionDocuments.value.filter(d => d.id !== documentId)
        }
        return col
      }
    } catch (e) {
      const col = collections.value.find(c => c.id === collectionId)
      if (col) {
        col.documentIds = col.documentIds.filter(id => id !== documentId)
        col.updatedAt = new Date().toISOString()
        collectionDocuments.value = collectionDocuments.value.filter(d => d.id !== documentId)
        return col
      }
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCollectionDocuments(collectionId: string) {
    isLoading.value = true
    try {
      const resp = await fetch(`/api/collections/${collectionId}/documents`)
      if (resp.ok) {
        const data = await resp.json()
        collectionDocuments.value = _toCamelCase(data)
      }
    } catch (e) {
      collectionDocuments.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function searchInCollection(collectionId: string, query: string, ocrStore: any) {
    collectionSearchQuery.value = query
    if (!query) {
      collectionSearchResults.value = []
      return
    }
    isLoading.value = true
    try {
      const resp = await fetch(`/api/collections/${collectionId}/search?query=${encodeURIComponent(query)}`)
      if (resp.ok) {
        const data = await resp.json()
        collectionSearchResults.value = _toCamelCase(data)
      }
    } catch (e) {
      const docs = collectionDocuments.value.length
        ? collectionDocuments.value
        : (() => {
          const col = collections.value.find(c => c.id === collectionId)
          return col ? ocrStore?.documents.filter(d => col.documentIds.includes(d.id)) || [] : []
        })()
      const q = query.toLowerCase()
      collectionSearchResults.value = docs.flatMap(d =>
        d.results
          .filter(r => r.text.toLowerCase().includes(q) || (r.corrected || '').toLowerCase().includes(q))
          .map(r => ({ documentId: d.id, documentName: d.name, result: r }))
      ) as CollectionSearchResult[]
    } finally {
      isLoading.value = false
    }
  }

  async function exportCollectionTEI(collectionId: string, name?: string) {
    isLoading.value = true
    error.value = null
    try {
      const resp = await fetch(`/api/collections/${collectionId}/export/tei`)
      if (resp.ok) {
        const xml = await resp.text()
        const blob = new Blob([xml], { type: 'application/xml' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${name || 'collection'}.xml`
        a.click()
        URL.revokeObjectURL(url)
        return true
      }
    } catch (e) {
      const col = collections.value.find(c => c.id === collectionId)
      if (col) {
        return true
      }
    } finally {
      isLoading.value = false
    }
    return false
  }

  const collectionDocumentCount = computed(() => currentCollection.value?.documentIds.length || 0)

  return {
    collections,
    currentCollection,
    collectionDocuments,
    collectionSearchResults,
    collectionSearchQuery,
    isLoading,
    error,
    collectionDocumentCount,
    loadMockCollections,
    fetchCollections,
    createCollection,
    updateCollection,
    deleteCollection,
    selectCollection,
    addDocumentToCollection,
    removeDocumentFromCollection,
    fetchCollectionDocuments,
    searchInCollection,
    exportCollectionTEI
  }
})

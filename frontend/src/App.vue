<template>
  <div class="flex h-screen">
    <!-- Left Panel with tabs -->
    <div class="w-72 bg-gray-900 p-4 flex flex-col gap-3 border-r border-gray-800">
      <h1 class="text-lg font-bold text-amber-400 text-center">古籍 OCR 标注平台</h1>

      <!-- Tabs -->
      <div class="flex gap-1 bg-gray-800 rounded p-1">
        <button @click="activeTab = 'docs'"
          class="flex-1 py-1.5 rounded text-xs font-medium transition"
          :class="activeTab === 'docs' ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white'">
          📄 文档
        </button>
        <button @click="activeTab = 'collections'"
          class="flex-1 py-1.5 rounded text-xs font-medium transition"
          :class="activeTab === 'collections' ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white'">
          📚 专题合集
        </button>
      </div>

      <!-- Documents Tab -->
      <div v-show="activeTab === 'docs'" class="flex flex-col gap-3 flex-1 overflow-hidden">
        <div>
          <label class="block bg-amber-500 text-black text-center py-2 rounded cursor-pointer hover:bg-amber-400 text-sm font-medium">
            上传古籍图片
            <input type="file" accept="image/*" @change="onUpload" class="hidden" />
          </label>
        </div>

        <button @click="store.loadMockDocument()" class="bg-gray-800 py-2 rounded text-sm hover:bg-gray-700">
          加载示例文档
        </button>

        <div class="text-xs text-gray-500 -mt-1">
          <span v-if="collectionStore.currentCollection" class="text-amber-400">
            当前专题：{{ collectionStore.currentCollection.name }}
          </span>
          <span v-else>提示：先去专题合集创建并选中专题，再回来加文档</span>
        </div>

        <!-- Search -->
        <div>
          <input v-model="store.searchQuery" @input="store.searchInDocuments(store.searchQuery)"
            placeholder="全文检索..." class="w-full bg-gray-800 rounded px-3 py-2 text-sm" />
          <div v-if="store.searchResults.length" class="mt-1 space-y-1 max-h-32 overflow-y-auto">
            <div v-for="r in store.searchResults" :key="r.id" class="bg-gray-800 rounded p-1 text-xs">
              {{ r.text }} <span class="text-gray-500">{{ (r.confidence * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>

        <!-- Document list -->
        <div class="flex-1 overflow-y-auto space-y-1">
          <div v-for="d in store.documents" :key="d.id"
            @click="store.currentDoc = d"
            class="bg-gray-800 rounded p-2 cursor-pointer text-sm group"
            :class="store.currentDoc?.id === d.id ? 'ring-1 ring-amber-500' : ''">
            <div class="flex justify-between items-start">
              <span class="truncate">{{ d.name }}</span>
              <div class="flex items-center gap-1 flex-shrink-0 ml-1">
                <button v-if="collectionStore.currentCollection && !isDocInCurrentCollection(d.id)"
                  @click.stop="addToCollection(d)"
                  class="text-xs text-green-400 hover:text-green-300 opacity-0 group-hover:opacity-100"
                  title="加入当前专题">
                  +入集
                </button>
              </div>
            </div>
            <div class="text-xs text-gray-500 mt-1">{{ d.results.length }} 行识别</div>
            <div v-if="isDocInCurrentCollection(d.id)" class="text-xs text-amber-400 mt-0.5">
              ✓ 已加入: {{ collectionStore.currentCollection.name }}
            </div>
          </div>
          <div v-if="!store.documents.length" class="text-gray-500 text-xs p-4 text-center">
            暂无文档，请上传或加载示例
          </div>
        </div>

        <!-- Export single doc -->
        <button @click="doExportSingle" :disabled="!store.currentDoc"
          class="bg-green-700 py-2 rounded text-sm hover:bg-green-600 disabled:opacity-40 disabled:cursor-not-allowed">
          导出当前文档 TEI/XML
        </button>
      </div>

      <!-- Collections Tab -->
      <div v-show="activeTab === 'collections'" class="flex-1 overflow-hidden">
        <CollectionPanel ref="collectionPanelRef" @locate-document="onLocateDocument" />
      </div>
    </div>

    <!-- Center: Image + OCR overlay -->
    <div class="flex-1 relative bg-gray-950 overflow-hidden">
      <ImageCanvas v-if="store.currentDoc" />
      <div v-else class="flex items-center justify-center h-full text-gray-600">
        请上传古籍图片或加载示例文档
      </div>
    </div>

    <!-- Right: OCR results & annotations -->
    <div class="w-80 bg-gray-900 p-4 flex flex-col gap-3 border-l border-gray-800 overflow-y-auto">
      <div class="flex justify-between items-center">
        <h3 class="text-amber-300 font-bold text-sm">OCR 识别结果</h3>
        <button v-if="collectionStore.currentCollection && store.currentDoc && !isDocInCurrentCollection(store.currentDoc.id)"
          @click="addCurrentToCollection"
          class="bg-green-800 text-green-200 px-2 py-1 rounded text-xs hover:bg-green-700">
          加入专题
        </button>
        <span v-else-if="collectionStore.currentCollection && store.currentDoc && isDocInCurrentCollection(store.currentDoc.id)"
          class="text-xs text-amber-400">
          ✓ 已入专题
        </span>
      </div>
      <div v-if="store.currentDoc" class="space-y-2">
        <div v-for="r in store.currentDoc.results" :key="r.id"
          class="bg-gray-800 rounded p-2 text-sm">
          <div class="flex justify-between">
            <span class="text-white font-medium">{{ r.text }}</span>
            <span class="text-xs px-2 py-0.5 rounded"
              :class="r.confidence > 0.9 ? 'bg-green-900 text-green-400' : 'bg-yellow-900 text-yellow-400'">
              {{ (r.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          <div class="text-xs text-gray-400 mt-1">
            简体: {{ store.convertVariant(r.text) }}
          </div>
          <input v-model="r.corrected" placeholder="人工校正..."
            class="w-full bg-gray-700 rounded px-2 py-1 text-xs mt-1" />
        </div>
      </div>
      <div v-else class="text-gray-500 text-xs">请先选择或上传文档</div>

      <h3 class="text-amber-300 font-bold text-sm mt-4">标注列表</h3>
      <div v-if="store.currentDoc" class="space-y-1">
        <div v-for="a in store.currentDoc.annotations" :key="a.id"
          class="bg-gray-800 rounded p-2 text-xs flex justify-between">
          <span>[{{ a.type }}] {{ a.label }}: {{ a.content }}</span>
          <button @click="store.removeAnnotation(a.id)" class="text-red-400 hover:underline">删除</button>
        </div>
        <div v-if="!store.currentDoc.annotations.length" class="text-gray-600 text-xs">
          在图片上拖拽框选区域添加标注
        </div>
      </div>
      <div v-else class="text-gray-500 text-xs">请先选择文档</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useOcrStore } from './store/ocr'
import { useCollectionStore } from './store/collections'
import ImageCanvas from './components/ImageCanvas.vue'
import CollectionPanel from './components/CollectionPanel.vue'
import type { Document } from './types'

const store = useOcrStore()
const collectionStore = useCollectionStore()
const activeTab = ref<'docs' | 'collections'>('docs')
const collectionPanelRef = ref<InstanceType<typeof CollectionPanel> | null>(null)

const isDocInCurrentCollection = (docId: string) => {
  return collectionStore.currentCollection?.documentIds.includes(docId) || false
}

function onUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) store.uploadAndOCR(file)
}

function doExportSingle() {
  const tei = store.exportTEI()
  if (!tei) return
  const blob = new Blob([tei], { type: 'application/xml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${store.currentDoc?.name || 'export'}.xml`
  a.click()
  URL.revokeObjectURL(url)
}

async function addToCollection(doc: Document) {
  if (!collectionStore.currentCollection) return
  await collectionStore.addDocumentToCollection(collectionStore.currentCollection.id, doc)
}

async function addCurrentToCollection() {
  if (!store.currentDoc || !collectionStore.currentCollection) return
  await addToCollection(store.currentDoc)
}

function onLocateDocument(docId: string) {
  const doc = store.documents.find(d => d.id === docId)
  if (doc) {
    store.currentDoc = doc
    activeTab.value = 'docs'
  }
}
</script>

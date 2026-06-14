<template>
  <div class="flex flex-col h-full gap-3">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-bold text-amber-400">专题合集</h2>
      <button @click="openCreateModal = true"
        class="bg-amber-500 text-black px-3 py-1 rounded text-xs font-medium hover:bg-amber-400">
        + 新建专题
      </button>
    </div>

    <div class="flex-1 overflow-y-auto space-y-2">
      <div v-for="col in collectionStore.collections" :key="col.id"
        @click="collectionStore.selectCollection(col.id)"
        class="bg-gray-800 rounded p-3 cursor-pointer text-sm"
        :class="collectionStore.currentCollection?.id === col.id ? 'ring-2 ring-amber-500' : 'hover:bg-gray-700'">
        <div class="flex justify-between items-start">
          <div class="flex-1 min-w-0">
            <div class="font-medium text-white truncate">{{ col.name }}</div>
            <div v-if="col.category" class="text-xs text-amber-400 mt-0.5">{{ col.category }}</div>
            <div v-if="col.description" class="text-xs text-gray-400 mt-1 line-clamp-2">{{ col.description }}</div>
          </div>
          <span class="text-xs text-gray-500 ml-2 flex-shrink-0">{{ col.documentIds.length }} 份</span>
        </div>
        <div class="flex gap-2 mt-2" @click.stop>
          <button @click="startEdit(col)" class="text-xs text-blue-400 hover:underline">编辑</button>
          <button @click="confirmDelete(col)" class="text-xs text-red-400 hover:underline">删除</button>
        </div>
      </div>
      <div v-if="!collectionStore.collections.length" class="text-gray-500 text-xs p-4 text-center">
        暂无专题合集，点击上方按钮新建
      </div>
    </div>

    <div v-if="collectionStore.currentCollection" class="border-t border-gray-700 pt-3 space-y-3">
      <div>
        <h3 class="text-amber-300 font-bold text-sm mb-2">
          {{ collectionStore.currentCollection.name }} · 合集内检索
        </h3>
        <input v-model="localSearchQuery"
          @input="doSearch"
          placeholder="在合集内搜索..." class="w-full bg-gray-800 rounded px-3 py-2 text-sm" />
        <div v-if="collectionStore.collectionSearchResults.length" class="mt-2 space-y-1 max-h-40 overflow-y-auto">
          <div v-for="(r, idx) in collectionStore.collectionSearchResults" :key="idx"
            class="bg-gray-800 rounded p-2 text-xs cursor-pointer hover:bg-gray-700"
            @click="locateDocument(r.documentId)">
            <div class="text-gray-400">[{{ r.documentName }}]</div>
            <div class="text-white mt-0.5">{{ highlight(r.result.text, localSearchQuery) }}</div>
          </div>
        </div>
      </div>

      <div>
        <h3 class="text-amber-300 font-bold text-sm mb-2">合集文档管理</h3>
        <div class="space-y-1 max-h-32 overflow-y-auto mb-2">
          <div v-for="d in collectionDocs" :key="d.id"
            class="bg-gray-800 rounded p-2 text-xs flex justify-between items-center">
            <span class="text-gray-300 truncate flex-1">{{ d.name }}</span>
            <button @click="removeDoc(d.id)" class="text-red-400 hover:underline ml-2 flex-shrink-0">移除</button>
          </div>
          <div v-if="!collectionDocs.length" class="text-gray-500 text-xs">
            暂无文档，从左侧文档列表添加
          </div>
        </div>
      </div>

      <button @click="doExport" class="w-full bg-green-700 py-2 rounded text-sm hover:bg-green-600">
        导出合集 TEI/XML
      </button>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="openCreateModal || editingCollection"
      class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50"
      @click.self="closeModal">
      <div class="bg-gray-900 rounded-lg p-6 w-96 border border-gray-700">
        <h3 class="text-lg font-bold text-amber-400 mb-4">
          {{ editingCollection ? '编辑专题合集' : '新建专题合集' }}
        </h3>
        <div class="space-y-3">
          <div>
            <label class="block text-sm text-gray-400 mb-1">专题名称 *</label>
            <input v-model="form.name" class="w-full bg-gray-800 rounded px-3 py-2 text-sm" placeholder="如：论语全集" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">分类</label>
            <input v-model="form.category" class="w-full bg-gray-800 rounded px-3 py-2 text-sm" placeholder="如：儒家经典 / 诗词" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">描述</label>
            <textarea v-model="form.description" rows="3"
              class="w-full bg-gray-800 rounded px-3 py-2 text-sm resize-none"
              placeholder="专题合集的说明描述..."></textarea>
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button @click="closeModal" class="flex-1 bg-gray-700 py-2 rounded text-sm hover:bg-gray-600">取消</button>
          <button @click="submitForm" :disabled="!form.name"
            class="flex-1 bg-amber-500 text-black py-2 rounded text-sm font-medium hover:bg-amber-400 disabled:opacity-50">
            {{ editingCollection ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useCollectionStore } from '../store/collections'
import { useOcrStore } from '../store/ocr'
import type { Collection } from '../types'

const emit = defineEmits<{
  (e: 'locate-document', docId: string): void
}>()

const collectionStore = useCollectionStore()
const ocrStore = useOcrStore()

const openCreateModal = ref(false)
const editingCollection = ref<Collection | null>(null)
const localSearchQuery = ref('')

const form = reactive({
  name: '',
  category: '',
  description: ''
})

const collectionDocs = computed(() => {
  if (!collectionStore.currentCollection) return []
  return ocrStore.documents.filter(d => collectionStore.currentCollection!.documentIds.includes(d.id))
})

onMounted(() => {
  collectionStore.fetchCollections()
})

watch(localSearchQuery, (q) => {
  if (collectionStore.currentCollection) {
    collectionStore.searchInCollection(collectionStore.currentCollection.id, q, ocrStore)
  }
})

function doSearch() {
  if (collectionStore.currentCollection) {
    collectionStore.searchInCollection(collectionStore.currentCollection.id, localSearchQuery.value, ocrStore)
  }
}

function startEdit(col: Collection) {
  editingCollection.value = col
  form.name = col.name
  form.category = col.category || ''
  form.description = col.description || ''
}

function closeModal() {
  openCreateModal.value = false
  editingCollection.value = null
  form.name = ''
  form.category = ''
  form.description = ''
}

async function submitForm() {
  if (!form.name) return
  if (editingCollection.value) {
    await collectionStore.updateCollection(editingCollection.value.id, {
      name: form.name || undefined,
      category: form.category || undefined,
      description: form.description || undefined
    })
  } else {
    await collectionStore.createCollection({
      name: form.name,
      category: form.category || undefined,
      description: form.description || undefined
    })
  }
  closeModal()
}

async function confirmDelete(col: Collection) {
  if (confirm(`确定删除专题合集「${col.name}」吗？`)) {
    await collectionStore.deleteCollection(col.id)
  }
}

async function removeDoc(docId: string) {
  if (!collectionStore.currentCollection) return
  await collectionStore.removeDocumentFromCollection(collectionStore.currentCollection.id, docId)
}

function locateDocument(docId: string) {
  emit('locate-document', docId)
}

async function doExport() {
  if (!collectionStore.currentCollection) return
  await collectionStore.exportCollectionTEI(
    collectionStore.currentCollection.id,
    collectionStore.currentCollection.name
  )
}

function highlight(text: string, query: string) {
  if (!query) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx === -1) return text
  return (
    text.slice(0, idx) +
    '<mark class="bg-amber-500 text-black">' + text.slice(idx, idx + query.length) + '</mark>' +
    text.slice(idx + query.length)
  )
}

defineExpose({
  addCurrentDoc: async () => {
    if (!collectionStore.currentCollection || !ocrStore.currentDoc) return
    await collectionStore.addDocumentToCollection(collectionStore.currentCollection.id, ocrStore.currentDoc.id)
  }
})
</script>

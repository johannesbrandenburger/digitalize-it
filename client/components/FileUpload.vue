<template>
  <div class="space-y-4">
    <!-- Drop Zone -->
    <div
      class="relative"
      @dragover.prevent="dragover = true"
      @dragleave.prevent="dragover = false"
      @drop.prevent="handleDrop"
    >
      <!-- Hidden File Input -->
      <input
        ref="fileInput"
        type="file"
        multiple
        accept="image/*"
        class="hidden"
        @change="handleFileSelect"
      >
      
      <!-- Upload Area -->
      <div
        :class="[
          'flex flex-col items-center justify-center min-h-[200px] rounded-lg border-2 border-dashed transition-colors',
          dragover ? 'border-blue-500 bg-blue-50' : 'border-gray-300 dark:border-gray-700',
          'dark:bg-gray-800 cursor-pointer'
        ]"
        @click="fileInput?.click()"
      >
        <div class="flex flex-col items-center justify-center p-6 text-center">
          <svg 
            class="w-12 h-12 mb-4 text-gray-400"
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              stroke-width="2" 
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <p class="mb-2 text-lg font-semibold text-gray-700 dark:text-gray-300">
            Drop your images here or click to upload
          </p>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            PNG, JPG up to 10MB
          </p>
        </div>
      </div>
    </div>
    
    <!-- Error Message -->
    <div v-if="error" class="text-red-500 text-sm">
      {{ error }}
    </div>
    
    <!-- File Previews -->
    <div v-if="files.length" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div 
        v-for="(file, index) in files" 
        :key="index" 
        class="relative group rounded-lg overflow-hidden"
      >
        <!-- Preview Image -->
        <img
          :src="previewUrls[index]"
          class="w-full h-48 object-cover"
          alt="Preview"
        />
        
        <!-- File Info Overlay -->
        <div class="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-between p-2">
          <div class="text-white text-sm truncate">
            {{ file.name }}
          </div>
          <div class="flex justify-between items-center">
            <span class="text-white text-xs">
              {{ formatFileSize(file.size) }}
            </span>
            <button
              @click.stop="removeFile(index)"
              class="p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
            >
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Actions -->
    <div v-if="files.length" class="flex justify-end space-x-4">
      <button
        @click="clearFiles"
        class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Clear All
      </button>
      <button
        @click="handleUpload"
        :disabled="uploading"
        class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <template v-if="uploading">
          <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Uploading...
        </template>
        <template v-else>
          Upload Images
        </template>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  maxFileSize?: number // in bytes, default 10MB
  maxFiles?: number // default 10
}>()

const emit = defineEmits<{
  'upload-complete': [uuids: string[]]
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const dragover = ref(false)
const files = ref<File[]>([])
const previewUrls = ref<string[]>([])
const uploading = ref(false)
const error = ref<string | null>(null)
const imageApi = useImageApi()

const MAX_FILE_SIZE = props.maxFileSize || 10 * 1024 * 1024 // 10MB
const MAX_FILES = props.maxFiles || 1024

// Utility functions
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const validateFile = (file: File): boolean => {
  // Check file type
  if (!file.type.startsWith('image/')) {
    error.value = 'Only image files are allowed'
    return false
  }
  
  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    error.value = `File size must be less than ${formatFileSize(MAX_FILE_SIZE)}`
    return false
  }
  
  return true
}

const addFiles = (newFiles: FileList | File[]) => {
  error.value = null
  
  // Check total number of files
  if (files.value.length + newFiles.length > MAX_FILES) {
    error.value = `Maximum ${MAX_FILES} files allowed`
    return
  }
  
  // Process each file
  Array.from(newFiles).forEach(file => {
    if (validateFile(file)) {
      files.value.push(file)
      previewUrls.value.push(URL.createObjectURL(file))
    }
  })
}

// Event handlers
const handleDrop = (e: DragEvent) => {
  dragover.value = false
  if (e.dataTransfer?.files) {
    addFiles(e.dataTransfer.files)
  }
}

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files) {
    addFiles(target.files)
  }
}

const removeFile = (index: number) => {
  URL.revokeObjectURL(previewUrls.value[index])
  files.value = files.value.filter((_, i) => i !== index)
  previewUrls.value = previewUrls.value.filter((_, i) => i !== index)
}

const clearFiles = () => {
  previewUrls.value.forEach(url => URL.revokeObjectURL(url))
  files.value = []
  previewUrls.value = []
  error.value = null
}

const handleUpload = async () => {
  if (!files.value.length) return
  
  uploading.value = true
  error.value = null
  
  try {
    const result = await imageApi.uploadImages(files.value)
    emit('upload-complete', result.uuids)
    clearFiles()
  } catch (err) {
    error.value = 'Upload failed. Please try again.'
    console.error('Upload failed:', err)
  } finally {
    uploading.value = false
  }
}

// Clean up preview URLs when component is unmounted
onBeforeUnmount(() => {
  previewUrls.value.forEach(url => URL.revokeObjectURL(url))
})
</script>
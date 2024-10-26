<!-- pages/index.vue -->
<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-8">Digitalize Your Photos</h1>
    
    <div class="space-y-8">
      <!-- Upload Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
        <h2 class="text-xl font-semibold mb-4">Upload Images</h2>
        <FileUpload 
          @upload-complete="handleUploadComplete"
          :max-file-size="10 * 1024 * 1024"
        />
      </div>
      
      <!-- Processed Images -->
      <div v-if="processedImages.length" class="space-y-8">
        <div
          v-for="uuid in processedImages"
          :key="uuid"
          class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg"
        >
          <ImageViewer :uuid="uuid" @delete-image="deleteImage" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

useHead({
  title: 'Digitalize it!',
  meta: [
    {
      name: 'description',
      content: 'Digitalize your photos with ease'
    }
  ]
})

const processedImages = ref<string[]>([])
const imageApi = useImageApi()

const handleUploadComplete = async (uuids: string[]) => {
  processedImages.value = await imageApi.getImages()
}

// load the already existing images from the server
onMounted(async () => {
  processedImages.value = await imageApi.getImages()
})

const deleteImage = async (uuid: string) => {
  processedImages.value = processedImages.value.filter((id) => id !== uuid)
}

</script>
<template>
    <div class="space-y-6">
      <div v-if="loading" class="flex justify-center">
        <USpinner />
      </div>
      
      <template v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Original Image -->
          <div class="space-y-4">
            <h3 class="text-lg font-semibold">Original Image</h3>
            <img
              :src="imageApi.getImageUrl(uuid, 'original')"
              class="w-full rounded-lg shadow-lg"
              alt="Original"
            />
            <UButton
              @click="detectRegions"
              :loading="detectingRegions"
              :disabled="detectingRegions"
            >
              Detect Regions
            </UButton>
          </div>
          
          <!-- Cropped Images -->
          <div v-if="croppedImages.length" class="space-y-4">
            <h3 class="text-lg font-semibold">Cropped Images</h3>
            <div class="space-y-4">
              <div
                v-for="(image, index) in croppedImages"
                :key="index"
                class="relative group"
              >
                <img
                  :src="imageApi.getImageUrl(uuid, 'cropped', index)"
                  class="w-full rounded-lg shadow-lg"
                  :alt="`Cropped ${index + 1}`"
                />
                <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <UButton
                    @click="rotateCropped(index)"
                    icon="i-heroicons-arrow-path"
                    color="white"
                    variant="solid"
                    :loading="rotatingIndex === index"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Regions Overlay -->
        <UModal v-model="showRegions">
          <div class="p-4">
            <h3 class="text-lg font-semibold mb-4">Detected Regions</h3>
            <canvas
              ref="canvasRef"
              class="w-full rounded-lg"
            />
            <div class="mt-4 flex justify-end space-x-4">
              <UButton
                @click="showRegions = false"
                color="gray"
              >
                Cancel
              </UButton>
              <UButton
                @click="handleCrop"
                :loading="cropping"
              >
                Crop Regions
              </UButton>
            </div>
          </div>
        </UModal>
      </template>
    </div>
  </template>
  
  <script setup lang="ts">
  const props = defineProps<{
    uuid: string
  }>()
  
  const imageApi = useImageApi()
  const loading = ref(true)
  const detectingRegions = ref(false)
  const cropping = ref(false)
  const showRegions = ref(false)
  const rotatingIndex = ref<number | null>(null)
  const regions = ref<any[]>([])
  const croppedImages = ref<string[]>([])
  const canvasRef = ref<HTMLCanvasElement | null>(null)
  
  onMounted(async () => {
    await loadCroppedImages()
    loading.value = false
  })
  
  const loadCroppedImages = async () => {
    try {
      const result = await imageApi.getCroppedImages(props.uuid)
      croppedImages.value = result.images
    } catch (error) {
      console.error('Failed to load cropped images:', error)
    }
  }
  
  const detectRegions = async () => {
    detectingRegions.value = true
    try {
      const result = await imageApi.getRegions(props.uuid)
      regions.value = result.regions
      showRegions.value = true
      nextTick(() => {
        drawRegions()
      })
    } catch (error) {
      console.error('Region detection failed:', error)
    } finally {
      detectingRegions.value = false
    }
  }
  
  const drawRegions = async () => {
    const canvas = canvasRef.value
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const img = new Image()
    img.src = imageApi.getImageUrl(props.uuid, 'original')
    
    img.onload = () => {
      canvas.width = img.width
      canvas.height = img.height
      
      ctx.drawImage(img, 0, 0)
      
      regions.value.forEach((region, index) => {
        ctx.beginPath()
        ctx.moveTo(region[0][0], region[0][1])
        region.slice(1).forEach(point => {
          ctx.lineTo(point[0], point[1])
        })
        ctx.closePath()
        ctx.strokeStyle = '#00ff00'
        ctx.lineWidth = 2
        ctx.stroke()
        
        // Add region number
        const centerX = region.reduce((sum, point) => sum + point[0], 0) / region.length
        const centerY = region.reduce((sum, point) => sum + point[1], 0) / region.length
        ctx.fillStyle = '#00ff00'
        ctx.font = '20px Arial'
        ctx.fillText((index + 1).toString(), centerX, centerY)
      })
    }
  }
  
  const handleCrop = async () => {
    cropping.value = true
    try {
      await imageApi.cropRegions(props.uuid, regions.value)
      await loadCroppedImages()
      showRegions.value = false
    } catch (error) {
      console.error('Cropping failed:', error)
    } finally {
      cropping.value = false
    }
  }
  
  const rotateCropped = async (index: number) => {
    rotatingIndex.value = index
    try {
      await imageApi.rotateCroppedImage(props.uuid, index)
      // Force image refresh by adding timestamp
      croppedImages.value = [...croppedImages.value]
    } catch (error) {
      console.error('Rotation failed:', error)
    } finally {
      rotatingIndex.value = null
    }
  }
</script>
  
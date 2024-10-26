<template>
  <div class="space-y-6">
    <div v-if="loading" class="flex justify-center">
      <UProgress animation="carousel" />
    </div>

    <template v-else>
      <div class="space-y-4">
        <!-- Original Image -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold">Original Image</h3>
          <img :src="imageApi.getImageUrl(uuid, 'original')" class="w-full max-w-2xl rounded-lg shadow-lg mx-auto"
            alt="Original" />
          <div class="flex justify-center space-x-4">
            <UButton @click="detectRegions" :loading="detectingRegions" :disabled="detectingRegions">
              Detect Regions
            </UButton>
            <UButton @click="deleteOriginalImage" color="red">
              Delete Image
            </UButton>
          </div>
        </div>

        <!-- Cropped Images -->
        <div v-if="croppedImages.length" class="space-y-4">
          <h3 class="text-lg font-semibold">Cropped Images</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="(image, index) in croppedImages" :key="index" class="relative group">
              <img :src="imageApi.getImageUrl(uuid, 'cropped', index)" class="w-full rounded-lg shadow-lg"
                :alt="`Cropped ${index + 1}`" />
              <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <UButton @click="rotateCropped(index)" icon="i-heroicons-arrow-path" color="white" variant="solid" class="mr-2"
                  :loading="rotatingIndex === index" />
                <UButton @click="deleteCropped(index)" icon="i-heroicons-trash" color="white" variant="solid" class="mr-2"
                  :loading="deletingIndex === index" />
                <UButton @click="downloadCropped(index)" icon="i-heroicons-arrow-down-tray" color="white" variant="solid"
                  :loading="downloadingIndex === index" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Regions Overlay -->
      <UModal v-model="showRegions" fullscreen>
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold">Adjust Regions</h3>
            <div class="flex space-x-2 items-center">
              <span class="text-sm text-gray-500">Zoom: </span>
              <UButton @click="adjustZoom(0.1)" icon="i-heroicons-plus" color="gray" variant="ghost" size="sm" />
              <UButton @click="adjustZoom(-0.1)" icon="i-heroicons-minus" color="gray" variant="ghost" size="sm" />
            </div>
          </div>

          <div class="relative overflow-auto bg-gray-100 rounded-lg" style="height: 75vh">
            <div class="relative" :style="{ transform: `scale(${zoom})`, transformOrigin: 'top left' }" ref="containerRef">
              <canvas ref="canvasRef" class="rounded-lg cursor-move" @mousedown="handleMouseDown"
                @mousemove="handleMouseMove" @mouseup="handleMouseUp" @mouseleave="handleMouseUp"
                @wheel="handleWheel" @contextmenu.prevent="addRegionOnSecondaryClick"
              />
            </div>
          </div>

          <div class="mt-4">
            <UButton @click="resetZoom" color="gray" size="sm" class="mr-4">
              Reset Zoom
            </UButton>
            <UButton @click="addRegion" color="gray" size="sm">
              Add Region
            </UButton>

            <div class="flex justify-end space-x-4">
              <UButton @click="showRegions = false" color="gray">
                Cancel
              </UButton>
              <UButton @click="handleCrop" :loading="cropping">
                Crop Regions
              </UButton>
            </div>
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

const emit = defineEmits<{
  'delete-image': [uuid: string]
}>()

import {saveAs} from 'file-saver';

const imageApi = useImageApi()
const loading = ref(true)
const detectingRegions = ref(false)
const cropping = ref(false)
const showRegions = ref(false)
const rotatingIndex = ref<number | null>(null)
const deletingIndex = ref<number | null>(null)
const downloadingIndex = ref<number | null>(null)
const regions = ref<any[]>([])
const croppedImages = ref<string[]>([])
const canvasRef = ref<HTMLCanvasElement | null>(null)
const isDragging = ref(false)
const selectedPoint = ref<{ regionIndex: number; pointIndex: number } | null>(null)
const originalImage = ref<HTMLImageElement | null>(null)
const zoom = ref(0.2)
const initialZoom = ref(1)
const isPanning = ref(false)
const lastPanPoint = ref<{ x: number; y: number } | null>(null)
const canvasContainer = ref<HTMLDivElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)

onMounted(async () => {
  await loadCroppedImages()
  loading.value = false
})

const calculateInitialZoom = () => {
  if (!containerRef.value || !originalImage.value) return 1

  const container = containerRef.value
  const image = originalImage.value

  // Get container dimensions (accounting for padding)
  const containerWidth = container.clientWidth - 48 // 24px padding on each side
  const containerHeight = container.clientHeight - 48

  // Calculate zoom ratios for both dimensions
  const widthRatio = containerWidth / image.width
  const heightRatio = containerHeight / image.height

  // Use the smaller ratio to ensure the image fits in both dimensions
  return Math.min(widthRatio, heightRatio, 1) // Cap at 1 to prevent upscaling
}

const resetZoom = () => {
  zoom.value = initialZoom.value
  drawRegions()
}

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

const adjustZoom = (delta: number) => {
  zoom.value = Math.max(0.1, Math.min(5, zoom.value + delta))
  drawRegions()
}

const handleWheel = (e: WheelEvent) => {

  // only zoom in/out if the meta key is pressed
  if (!e.metaKey) return

  e.preventDefault()

  const delta = e.deltaY > 0 ? -0.03 : 0.03
  adjustZoom(delta)
}

const addRegionOnSecondaryClick = (e: MouseEvent) => {
  if (e.button === 2) {
    e.preventDefault()
    const point = getCanvasPoint(e)
    if (point) {
      addRegion(point)
    }
  }
}

const getCanvasPoint = (e: MouseEvent) => {
  const canvas = canvasRef.value
  if (!canvas) return null

  const rect = canvas.getBoundingClientRect()
  const x = (e.clientX - rect.left) / zoom.value
  const y = (e.clientY - rect.top) / zoom.value
  return { x, y }
}

const findNearestPoint = (point: { x: number; y: number }, threshold = 10) => {
  for (let i = 0; i < regions.value.length; i++) {
    const region = regions.value[i]
    for (let j = 0; j < region.length; j++) {
      const [x, y] = region[j]
      const distance = Math.sqrt(
        Math.pow(point.x - x, 2) + Math.pow(point.y - y, 2)
      )
      if (distance < threshold / zoom.value) {
        return { regionIndex: i, pointIndex: j }
      }
    }
  }
  return null
}

const handleMouseDown = (e: MouseEvent) => {
  const point = getCanvasPoint(e)
  if (!point) return

  const nearest = findNearestPoint(point)
  if (nearest) {
    isDragging.value = true
    selectedPoint.value = nearest
  } else {
    isPanning.value = true
    lastPanPoint.value = { x: e.clientX, y: e.clientY }
  }
}

const handleMouseMove = (e: MouseEvent) => {
  const canvas = canvasRef.value
  if (!canvas) return

  if (isDragging.value && selectedPoint.value) {
    const point = getCanvasPoint(e)
    if (!point) return

    // Update the point position
    const { regionIndex, pointIndex } = selectedPoint.value
    regions.value[regionIndex][pointIndex] = [point.x, point.y]
    drawRegions()
  } else if (isPanning.value && lastPanPoint.value && canvasContainer.value) {
    const dx = e.clientX - lastPanPoint.value.x
    const dy = e.clientY - lastPanPoint.value.y

    canvasContainer.value.scrollLeft -= dx
    canvasContainer.value.scrollTop -= dy

    lastPanPoint.value = { x: e.clientX, y: e.clientY }
  }
}

const handleMouseUp = () => {
  isDragging.value = false
  isPanning.value = false
  selectedPoint.value = null
  lastPanPoint.value = null
}

const drawRegions = async () => {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  if (!originalImage.value) {
    originalImage.value = new Image()
    originalImage.value.src = imageApi.getImageUrl(props.uuid, 'original')
    originalImage.value.onload = () => {
      drawRegionsOnCanvas(ctx, canvas)
      initialZoom.value = calculateInitialZoom()
      resetZoom()
    }
  } else {
    drawRegionsOnCanvas(ctx, canvas)
  }
}

const drawRegionsOnCanvas = (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
  if (!originalImage.value) return

  // Set canvas size to image size
  canvas.width = originalImage.value.width
  canvas.height = originalImage.value.height

  // Clear and draw image
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(originalImage.value, 0, 0)

  // Draw regions
  regions.value.forEach((region, index) => {
    // Draw region outline
    ctx.beginPath()
    ctx.moveTo(region[0][0], region[0][1])

    region.slice(1).forEach(point => {
      ctx.lineTo(point[0], point[1])
    })

    ctx.closePath()
    ctx.strokeStyle = '#00ff00'
    ctx.lineWidth = 5
    ctx.stroke()

    // Draw points
    region.forEach(([x, y], pointIndex) => {
      ctx.beginPath()
      ctx.arc(x, y, 10, 0, Math.PI * 2)

      // Highlight selected point
      if (selectedPoint.value?.regionIndex === index &&
        selectedPoint.value?.pointIndex === pointIndex) {
        ctx.fillStyle = '#ff0000'
      } else {
        ctx.fillStyle = '#00ff00'
      }

      ctx.fill()
    })

    // Add region number
    const centerX = region.reduce((sum, point) => sum + point[0], 0) / region.length
    const centerY = region.reduce((sum, point) => sum + point[1], 0) / region.length
    ctx.fillStyle = '#00ff00'
    ctx.font = '20px Arial'
    ctx.fillText((index + 1).toString(), centerX, centerY)
  })
}

// listen on enter key press
window.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && showRegions.value) {
    e.preventDefault()
    handleCrop()
  }
})

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
    croppedImages.value = []
    await imageApi.rotateCroppedImage(props.uuid, index)
    await loadCroppedImages()
  } catch (error) {
    console.error('Rotation failed:', error)
  } finally {
    rotatingIndex.value = null
  }
}

const deleteCropped = async (index: number) => {
  deletingIndex.value = index
  try {
    croppedImages.value = []
    await imageApi.deleteCroppedImage(props.uuid, index)
    await loadCroppedImages()
  } catch (error) {
    console.error('Deletion failed:', error)
  } finally {
    deletingIndex.value = null
  }
}

const deleteOriginalImage = async () => {
  try {
    await imageApi.deleteImage(props.uuid)
    croppedImages.value = []
    emit('delete-image', props.uuid)
  } catch (error) {
    console.error('Deletion failed:', error)
  }
}

const downloadCropped = async (index: number) => {
  downloadingIndex.value = index
  try {
    const blob = await fetch(imageApi.getImageUrl(props.uuid, 'cropped', index)).then(res => res.blob())
    saveAs(blob, `${props.uuid}-cropped-${index + 1}.png`)
  } catch (error) {
    console.error('Download failed:', error)
  } finally {
    downloadingIndex.value = null
  }
}

const addRegion = (startPoint = { x: 0, y: 0 }) => {
  regions.value.push([ [startPoint.x, startPoint.y], [startPoint.x + 50, startPoint.y], [startPoint.x + 50, startPoint.y + 50], [startPoint.x, startPoint.y + 50] ])
  drawRegions()
}
</script>
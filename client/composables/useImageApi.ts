export const useImageApi = () => {
    const config = useRuntimeConfig()
    
    const uploadImages = async (files: File[]) => {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))
      
      const response = await fetch(`${config.public.apiBase}/upload`, {
        method: 'POST',
        body: formData
      })
      return await response.json()
    }

    const getImages = async () => {
      const response = await fetch(`${config.public.apiBase}/images`)
      return await response.json()
    }
    
    const getRegions = async (uuid: string) => {
      const response = await fetch(`${config.public.apiBase}/image/${uuid}/regions`)
      return await response.json()
    }
    
    const cropRegions = async (uuid: string, regions: any) => {
      const response = await fetch(`${config.public.apiBase}/image/${uuid}/crop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ regions })
      })
      return await response.json()
    }
    
    const getCroppedImages = async (uuid: string) => {
      const response = await fetch(`${config.public.apiBase}/image/${uuid}/cropped`)
      return await response.json()
    }
    
    const rotateCroppedImage = async (uuid: string, index: number) => {
      const response = await fetch(`${config.public.apiBase}/image/${uuid}/cropped/${index}/rotate`, {
        method: 'POST'
      })
      return await response.json()
    }

    const deleteCroppedImage = async (uuid: string, index: number) => {
      const response = await fetch(`${config.public.apiBase}/image/${uuid}/cropped/${index}`, {
        method: 'DELETE'
      })
      return await response.json()
    }
    
    const getImageUrl = (uuid: string, type: 'original' | 'cropped', index?: number) => {
      if (type === 'original') {
        return `${config.public.apiBase}/image/${uuid}/original?random=${Date.now()}`
      }
      return `${config.public.apiBase}/image/${uuid}/cropped/${index}?random=${Date.now()}`
    }
    
    return {
      uploadImages,
      getImages,
      getRegions,
      cropRegions,
      getCroppedImages,
      rotateCroppedImage,
      deleteCroppedImage,
      getImageUrl
    }
  }
  
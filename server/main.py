from typing import Union, List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import uuid
import os
import shutil
from pydantic import BaseModel
import cv2
import numpy as np

from opencv.functions import get_contour, four_point_transform

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Types
class Coordinate(BaseModel):
    x: float
    y: float

class Region(BaseModel):
    points: List[List[float]]

class RegionsRequest(BaseModel):
    regions: List[List[List[float]]]

class RegionsResponse(BaseModel):
    regions: List[List[List[float]]]

class UUIDResponse(BaseModel):
    uuids: List[str]

class CroppedImagesResponse(BaseModel):
    images: List[str]

# Constants
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Utility functions
def create_image_directory(image_uuid: str) -> str:
    """Create directory for a specific image UUID"""
    dir_path = os.path.join(DATA_DIR, image_uuid)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def save_image(file: UploadFile, image_uuid: str) -> str:
    """Save uploaded image to disk using OpenCV"""
    dir_path = create_image_directory(image_uuid)
    file_path = os.path.join(dir_path, "original.jpg")
    
    # First save the uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Read and save with OpenCV to ensure proper format
    img = cv2.imread(file_path)
    cv2.imwrite(file_path, img)
    
    return file_path


def detect_regions_opencv(image_path: str) -> List[List[List[float]]]:
    """
    Detect regions in image using the get_contour function
    """
    # Read the image
    img = cv2.imread(image_path)

    # Get the contour
    contour = get_contour(img)

    # Convert contour to list of lists
    regions = [contour.tolist()]
    
    return regions

def crop_image(image_path: str, region: List[List[float]], output_path: str):
    """Crop image using four_point_transform function"""

    img = cv2.imread(image_path)
    region = np.array(region)
    cropped = four_point_transform(img, region)
    cv2.imwrite(output_path, cropped)

def rotate_image(image_path: str):
    """Rotate image 90 degrees clockwise using OpenCV"""
    # Read the image
    img = cv2.imread(image_path)
    
    # Rotate 90 degrees clockwise
    rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    
    # Save the rotated image
    cv2.imwrite(image_path, rotated)

# Endpoints
@app.get("/")
async def read_root() -> Union[str, dict]:
    return "The API is up and running"

@app.get("/images")
async def list_images() -> List[str]:
    return os.listdir(DATA_DIR)

@app.post("/upload", response_model=UUIDResponse)
async def upload_images(files: List[UploadFile] = File(...)) -> UUIDResponse:
    uuids = []
    for file in files:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        image_uuid = str(uuid.uuid4())
        save_image(file, image_uuid)
        uuids.append(image_uuid)
    
    return UUIDResponse(uuids=uuids)

@app.get("/image/{uuid}/regions", response_model=RegionsResponse)
async def detect_regions(uuid: str) -> RegionsResponse:
    image_path = os.path.join(DATA_DIR, uuid, "original.jpg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    regions = detect_regions_opencv(image_path)
    return RegionsResponse(regions=regions)

@app.post("/image/{uuid}/crop")
async def crop_regions(uuid: str, regions_request: RegionsRequest):
    image_path = os.path.join(DATA_DIR, uuid, "original.jpg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Remove existing cropped images
    dir_path = os.path.join(DATA_DIR, uuid)
    for file in os.listdir(dir_path):
        if file.startswith("cropped_"):
            os.remove(os.path.join(dir_path, file))

    # Crop the image based on regions
    for i, region in enumerate(regions_request.regions):
        output_path = os.path.join(DATA_DIR, uuid, f"cropped_{i}.jpg")
        crop_image(image_path, region, output_path)
    
    return {"status": "success"}

@app.get("/image/{uuid}/cropped", response_model=CroppedImagesResponse)
async def list_cropped_images(uuid: str) -> CroppedImagesResponse:
    dir_path = os.path.join(DATA_DIR, uuid)
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    cropped_images = [
        f"{uuid}/cropped_{i}.jpg"
        for i in range(100)  # Arbitrary limit
        if os.path.exists(os.path.join(dir_path, f"cropped_{i}.jpg"))
    ]
    
    return CroppedImagesResponse(images=cropped_images)

@app.get("/image/{uuid}/cropped/{index}")
async def get_cropped_image(uuid: str, index: int):
    image_path = os.path.join(DATA_DIR, uuid, f"cropped_{index}.jpg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Cropped image not found")
    
    return FileResponse(image_path)

@app.get("/image/{uuid}/original")
async def get_original_image(uuid: str):
    image_path = os.path.join(DATA_DIR, uuid, "original.jpg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Original image not found")
    
    return FileResponse(image_path)

@app.post("/image/{uuid}/cropped/{index}/rotate")
async def rotate_cropped_image(uuid: str, index: int):
    image_path = os.path.join(DATA_DIR, uuid, f"cropped_{index}.jpg")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Cropped image not found")
    
    rotate_image(image_path)
    return {"status": "success"}

@app.delete("/image/{uuid}")
async def delete_image(uuid: str):
    dir_path = os.path.join(DATA_DIR, uuid)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    
    return {"status": "success"}

@app.delete("/image/{uuid}/cropped/{index}")
async def delete_cropped_image(uuid: str, index: int):
    image_path = os.path.join(DATA_DIR, uuid, f"cropped_{index}.jpg")
    if os.path.exists(image_path):
        os.remove(image_path)
    
    return {"status": "success"}
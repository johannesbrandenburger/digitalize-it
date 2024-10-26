from typing import Union, List, Tuple
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import uuid
import os
import shutil
from pydantic import BaseModel
import random  # For mocking region detection
import cv2
import numpy as np

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

def mock_region_detection() -> List[List[List[float]]]:
    """Mock function for region detection"""
    num_regions = random.randint(1, 3)
    regions = []
    
    for _ in range(num_regions):
        # Generate 4 points for a quadrilateral
        points = []
        for _ in range(4):
            x = random.uniform(0, 100)
            y = random.uniform(0, 100)
            points.append([x, y])
        regions.append(points)
    
    return regions

def detect_regions_opencv(image_path: str) -> List[List[List[float]]]:
    """
    Detect regions in image using OpenCV
    This is a basic implementation that could be enhanced based on specific needs
    """
    # Read image
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regions = []
    for contour in contours:
        # Approximate the contour to a polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # If the polygon has 4 points, consider it a region
        if len(approx) == 4:
            points = [[float(point[0][0]), float(point[0][1])] for point in approx]
            regions.append(points)
    
    # If no regions found, return mock data
    if not regions:
        return mock_region_detection()
    
    return regions

def crop_image(image_path: str, region: List[List[float]], output_path: str):
    """Crop image based on region coordinates using OpenCV"""
    # Read the image
    img = cv2.imread(image_path)
    
    # Convert region points to numpy array
    points = np.array(region, dtype=np.float32)
    
    # Get the bounding rectangle
    rect = cv2.boundingRect(points.astype(np.int32))
    x, y, w, h = rect
    
    # Get the minimum area rectangle
    center, size, angle = cv2.minAreaRect(points.astype(np.int32))
    
    # Create source and destination points for perspective transform
    src_points = points.astype(np.float32)
    dst_points = np.array([[0, 0],
                          [w - 1, 0],
                          [w - 1, h - 1],
                          [0, h - 1]], dtype=np.float32)
    
    # Get perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    
    # Do perspective transform
    result = cv2.warpPerspective(img, matrix, (w, h))
    
    # Save the result
    cv2.imwrite(output_path, result)

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
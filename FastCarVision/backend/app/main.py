import time
import uuid
import logging
from datetime import datetime
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io

from .config import settings
from .models import (
    ImageUploadResponse, 
    SearchResults, 
    HealthCheck, 
    ErrorResponse,
    CarDetection
)
from .vision import vision_model
from .scrapers import scraping_orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Real-Time Car Recognition & Web Scraper API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        models_loaded = {
            "yolo": vision_model.yolo_model is not None,
            "clip": vision_model.clip_model is not None
        }
        
        return HealthCheck(
            status="healthy",
            timestamp=datetime.now(),
            version=settings.version,
            models_loaded=models_loaded
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.post("/upload-image", response_model=ImageUploadResponse)
async def upload_car_image(file: UploadFile = File(...)):
    """
    Upload a car image for recognition and processing
    """
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read and validate image
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image file too large (max 10MB)"
            )
        
        # Process image
        image = Image.open(io.BytesIO(contents))
        
        # Detect cars in the image
        detected_cars = vision_model.process_image(image)
        
        processing_time = time.time() - start_time
        image_id = str(uuid.uuid4())
        
        logger.info(f"Processed image {image_id} in {processing_time:.2f}s, found {len(detected_cars)} cars")
        
        return ImageUploadResponse(
            message="Image processed successfully",
            image_id=image_id,
            detected_cars=detected_cars,
            processing_time=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process image"
        )

@app.post("/search-cars", response_model=SearchResults)
async def search_car_listings(car_detection: CarDetection):
    """
    Search for car listings based on detected car attributes
    """
    start_time = time.time()
    
    try:
        logger.info(f"Searching for {car_detection.make} {car_detection.model}")
        
        # Run web scraping
        listings = await scraping_orchestrator.scrape_all(car_detection)
        
        processing_time = time.time() - start_time
        
        # Get unique sources
        sources_used = list(set(listing.source for listing in listings))
        
        query = f"{car_detection.make} {car_detection.model}"
        if car_detection.year:
            query = f"{car_detection.year} {query}"
        
        logger.info(f"Found {len(listings)} listings in {processing_time:.2f}s from {len(sources_used)} sources")
        
        return SearchResults(
            query=query,
            total_results=len(listings),
            listings=listings,
            processing_time=processing_time,
            sources_used=sources_used
        )
    
    except Exception as e:
        logger.error(f"Error searching car listings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search car listings"
        )

@app.post("/process-and-search", response_model=SearchResults)
async def process_image_and_search(file: UploadFile = File(...)):
    """
    Complete pipeline: upload image, detect car, and search for listings
    """
    start_time = time.time()
    
    try:
        # Process image first
        upload_response = await upload_car_image(file)
        
        if not upload_response.detected_cars:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cars detected in the image"
            )
        
        # Use the first detected car for search
        primary_car = upload_response.detected_cars[0]
        
        # Search for listings
        search_results = await search_car_listings(primary_car)
        
        # Update processing time to include both steps
        total_processing_time = time.time() - start_time
        search_results.processing_time = total_processing_time
        
        logger.info(f"Complete pipeline finished in {total_processing_time:.2f}s")
        
        return search_results
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process image and search"
        )

@app.get("/supported-formats")
async def get_supported_formats():
    """Get supported image formats"""
    return {
        "supported_formats": settings.supported_formats,
        "max_file_size": "10MB"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.debug else "An unexpected error occurred"
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    ) 
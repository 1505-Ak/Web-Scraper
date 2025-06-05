from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CarDetection(BaseModel):
    make: str = Field(..., description="Car manufacturer")
    model: str = Field(..., description="Car model")
    year: Optional[int] = Field(None, description="Car year")
    body_type: Optional[str] = Field(None, description="Body type (sedan, SUV, etc.)")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    color: Optional[str] = Field(None, description="Primary color")

class CarListing(BaseModel):
    title: str
    price: Optional[str] = None
    year: Optional[int] = None
    make: str
    model: str
    mileage: Optional[str] = None
    location: Optional[str] = None
    dealer: Optional[str] = None
    image_url: Optional[str] = None
    listing_url: str
    source: str  # autotrader, ebay, cars.com, etc.
    scraped_at: datetime = Field(default_factory=datetime.now)
    similarity_score: Optional[float] = None

class ImageUploadResponse(BaseModel):
    message: str
    image_id: str
    detected_cars: List[CarDetection]
    processing_time: float

class SearchResults(BaseModel):
    query: str
    total_results: int
    listings: List[CarListing]
    processing_time: float
    sources_used: List[str]

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    models_loaded: Dict[str, bool]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now) 
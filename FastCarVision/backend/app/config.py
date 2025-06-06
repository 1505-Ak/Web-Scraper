import os
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Configuration
    app_name: str = "FastCarVision"
    version: str = "1.0.0"
    debug: bool = False
    
    # Image Processing
    max_image_size: int = 1024
    supported_formats: List[str] = ["jpg", "jpeg", "png", "bmp"]
    
    # Model Configuration
    car_detection_model: str = "yolov8n.pt"
    clip_model: str = "ViT-B/32"
    device: str = "cpu"  # Default to CPU
    
    # FAISS Configuration
    faiss_index_path: str = "data/car_embeddings.index"
    embedding_dim: int = 512
    
    # Web Scraping Configuration
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    user_agent: str = "FastCarVision/1.0"
    
    # Scrapers
    enable_autotrader: bool = True
    enable_ebay_motors: bool = False
    enable_cars_com: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set device based on environment and availability
        cuda_env = os.getenv("CUDA_AVAILABLE", "false").lower()
        if cuda_env == "true":
            try:
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                else:
                    print("CUDA requested but not available, using CPU")
                    self.device = "cpu"
            except ImportError:
                print("PyTorch not available, using CPU")
                self.device = "cpu"
        
        # Handle supported formats from environment if provided
        formats_env = os.getenv("SUPPORTED_FORMATS")
        if formats_env:
            self.supported_formats = [f.strip() for f in formats_env.split(",")]
    
    class Config:
        env_file = ".env"
        # Don't try to parse env vars as JSON
        use_enum_values = True

settings = Settings() 
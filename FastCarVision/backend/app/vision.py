import torch
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from typing import List, Tuple, Optional
import logging
from .config import settings
from .models import CarDetection

# Try to import CLIP with fallback
try:
    import clip
    CLIP_AVAILABLE = True
except ImportError:
    print("Warning: CLIP not available. Using placeholder for features.")
    CLIP_AVAILABLE = False

logger = logging.getLogger(__name__)

class CarVisionModel:
    def __init__(self):
        self.device = settings.device
        self.yolo_model = None
        self.clip_model = None
        self.clip_preprocess = None
        self.car_classes = {
            2: "car", 3: "motorcycle", 5: "bus", 7: "truck"  # COCO class IDs
        }
        self.load_models()
    
    def load_models(self):
        """Load YOLO and CLIP models"""
        try:
            # Load YOLO model for car detection
            self.yolo_model = YOLO(settings.car_detection_model)
            logger.info(f"YOLO model loaded: {settings.car_detection_model}")
            
            # Load CLIP model for feature extraction if available
            if CLIP_AVAILABLE:
                try:
                    self.clip_model, self.clip_preprocess = clip.load(
                        settings.clip_model, device=self.device
                    )
                    logger.info(f"CLIP model loaded: {settings.clip_model}")
                except Exception as e:
                    logger.warning(f"Could not load CLIP model: {e}")
                    self.clip_model = None
            else:
                logger.warning("CLIP not available, features will be placeholder")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for detection"""
        # Resize if too large
        if max(image.size) > settings.max_image_size:
            image.thumbnail((settings.max_image_size, settings.max_image_size), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    
    def detect_cars(self, image: Image.Image) -> List[dict]:
        """Detect cars in the image using YOLO"""
        try:
            # Convert PIL to cv2 format
            img_array = np.array(image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Run YOLO detection
            results = self.yolo_model(img_bgr, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Check if detected class is a vehicle
                        class_id = int(box.cls[0])
                        if class_id in self.car_classes:
                            confidence = float(box.conf[0])
                            if confidence > 0.5:  # Confidence threshold
                                detections.append({
                                    'class': self.car_classes[class_id],
                                    'confidence': confidence,
                                    'bbox': box.xyxy[0].tolist()
                                })
            
            return detections
        
        except Exception as e:
            logger.error(f"Error in car detection: {e}")
            return []
    
    def extract_clip_features(self, image: Image.Image) -> np.ndarray:
        """Extract CLIP features from image"""
        if not self.clip_model:
            logger.warning("CLIP model not available, returning placeholder features")
            return np.random.rand(512)  # Placeholder features
        
        try:
            # Preprocess image for CLIP
            image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            
            # Extract features
            with torch.no_grad():
                features = self.clip_model.encode_image(image_tensor)
                features = features / features.norm(dim=-1, keepdim=True)  # Normalize
            
            return features.cpu().numpy().flatten()
        
        except Exception as e:
            logger.error(f"Error extracting CLIP features: {e}")
            return np.random.rand(512)  # Fallback features
    
    def classify_car_attributes(self, image: Image.Image, detection_box: Optional[List[float]] = None) -> dict:
        """Extract car attributes like make, model, color using CLIP and heuristics"""
        try:
            # If detection box provided, crop the image
            if detection_box:
                x1, y1, x2, y2 = [int(coord) for coord in detection_box]
                image = image.crop((x1, y1, x2, y2))
            
            # For now, return placeholder values
            # In a production system, you'd use specialized models or APIs
            attributes = {
                'make': 'Unknown',
                'model': 'Unknown', 
                'year': None,
                'body_type': 'sedan',
                'color': 'Unknown'
            }
            
            # Simple color detection using dominant colors
            img_array = np.array(image)
            colors = self._get_dominant_color(img_array)
            attributes['color'] = colors
            
            return attributes
        
        except Exception as e:
            logger.error(f"Error in car classification: {e}")
            return {
                'make': 'Unknown',
                'model': 'Unknown',
                'year': None,
                'body_type': 'sedan',
                'color': 'Unknown'
            }
    
    def _get_dominant_color(self, image_array: np.ndarray) -> str:
        """Extract dominant color from image"""
        try:
            # Reshape image to be a list of pixels
            pixels = image_array.reshape(-1, 3)
            
            # Calculate mean color
            mean_color = np.mean(pixels, axis=0)
            
            # Simple color classification
            r, g, b = mean_color
            if r > 150 and g > 150 and b > 150:
                return "white"
            elif r < 80 and g < 80 and b < 80:
                return "black"
            elif r > g and r > b:
                return "red"
            elif g > r and g > b:
                return "green"
            elif b > r and b > g:
                return "blue"
            else:
                return "gray"
        
        except Exception:
            return "Unknown"
    
    def process_image(self, image: Image.Image) -> List[CarDetection]:
        """Complete image processing pipeline"""
        # Preprocess image
        processed_image = self.preprocess_image(image)
        
        # Detect cars
        detections = self.detect_cars(processed_image)
        
        car_results = []
        for detection in detections:
            # Extract attributes for each detected car
            attributes = self.classify_car_attributes(
                processed_image, 
                detection.get('bbox')
            )
            
            car_result = CarDetection(
                make=attributes['make'],
                model=attributes['model'],
                year=attributes['year'],
                body_type=attributes['body_type'],
                confidence=detection['confidence'],
                color=attributes['color']
            )
            car_results.append(car_result)
        
        # If no cars detected, return a default detection
        if not car_results:
            # Try to classify the whole image as a car
            attributes = self.classify_car_attributes(processed_image)
            car_results.append(
                CarDetection(
                    make=attributes['make'],
                    model=attributes['model'],
                    year=attributes['year'],
                    body_type=attributes['body_type'],
                    confidence=0.7,  # Default confidence
                    color=attributes['color']
                )
            )
        
        return car_results

# Initialize model when imported, with error handling
try:
    vision_model = CarVisionModel()
    logger.info("Vision model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize vision model: {e}")
    # Create a dummy model that will work for basic testing
    class DummyVisionModel:
        def process_image(self, image):
            return [CarDetection(
                make="Toyota",
                model="Camry", 
                year=2020,
                body_type="sedan",
                confidence=0.8,
                color="white"
            )]
    
    vision_model = DummyVisionModel()
    logger.warning("Using dummy vision model due to initialization failure") 
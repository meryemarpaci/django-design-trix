import requests
import base64
import io
from PIL import Image, ImageDraw
import numpy as np
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class LoRAInpaintingModel:
    """
    LoRA Inpainting Model handler using Hugging Face Inference API
    """
    
    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/meryemarpaci/sd2base-inpainting-lora"
        self.headers = {
            "Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_TOKEN', '')}"
        }
        self.loaded = True  # Always loaded since we're using API
        
    def load_model(self):
        """Check if API token is available"""
        try:
            token = os.environ.get('HUGGINGFACE_API_TOKEN')
            if not token:
                logger.error("HUGGINGFACE_API_TOKEN environment variable not set")
                return False
                
            logger.info("Hugging Face API configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure Hugging Face API: {e}")
            return False
    
    def create_mask_from_bbox(self, image_size, bbox):
        """
        Create a mask from bounding box coordinates
        bbox: (x, y, width, height)
        """
        mask = Image.new("RGB", image_size, (0, 0, 0))
        draw = ImageDraw.Draw(mask)
        x, y, w, h = bbox
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        return mask
    
    def create_mask_from_brush_strokes(self, image_size, strokes):
        """
        Create a mask from brush stroke coordinates
        strokes: list of stroke paths [(x1, y1), (x2, y2), ...]
        """
        mask = Image.new("RGB", image_size, (0, 0, 0))
        draw = ImageDraw.Draw(mask)
        
        for stroke in strokes:
            if len(stroke) > 1:
                draw.line(stroke, fill=(255, 255, 255), width=20)
        
        return mask
    
    def preprocess_image(self, image_path, target_size=(512, 512)):
        """Preprocess image for inpainting"""
        try:
            image = Image.open(image_path).convert("RGB")
            image = image.resize(target_size, Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None
    
    def image_to_base64(self, image):
        """Convert PIL Image to base64 string"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def inpaint(self, image_path, mask_data, prompt, negative_prompt="", 
                num_inference_steps=50, guidance_scale=7.5, strength=1.0):
        """
        Perform inpainting using Hugging Face Inference API
        
        Args:
            image_path: Path to the input image
            mask_data: Dictionary containing mask information
            prompt: Text prompt for inpainting
            negative_prompt: Negative prompt
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale for classifier-free guidance
            strength: How much to transform the reference image
        """
        try:
            # Check API token
            if not os.environ.get('HUGGINGFACE_API_TOKEN'):
                raise Exception("Hugging Face API token not configured")
            
            # Preprocess image
            image = self.preprocess_image(image_path)
            if image is None:
                raise Exception("Failed to preprocess image")
            
            # Create mask based on mask_data type
            if mask_data.get('type') == 'bbox':
                bbox = mask_data.get('bbox')
                mask = self.create_mask_from_bbox(image.size, bbox)
            elif mask_data.get('type') == 'brush':
                strokes = mask_data.get('strokes', [])
                mask = self.create_mask_from_brush_strokes(image.size, strokes)
            else:
                raise Exception("Invalid mask data")
            
            logger.info(f"Starting inpainting API call with prompt: '{prompt}'")
            
            # Convert images to base64
            image_b64 = self.image_to_base64(image)
            mask_b64 = self.image_to_base64(mask)
            
            # Prepare API payload
            payload = {
                "inputs": {
                    "prompt": prompt,
                    "image": image_b64,
                    "mask_image": mask_b64,
                    "negative_prompt": negative_prompt,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "strength": strength
                }
            }
            
            # Make API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60  # 60 second timeout
            )
            
            if response.status_code == 200:
                # Response is image bytes
                result_image = Image.open(io.BytesIO(response.content))
                logger.info("Inpainting completed successfully via API")
                return result_image
            else:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
        except Exception as e:
            logger.error(f"Inpainting failed: {e}")
            raise e
    
    def cleanup(self):
        """No cleanup needed for API calls"""
        logger.info("API client cleanup completed")

# Global model instance
_inpainting_model = None

def get_inpainting_model():
    """Get or create the global inpainting model instance"""
    global _inpainting_model
    if _inpainting_model is None:
        _inpainting_model = LoRAInpaintingModel()
    return _inpainting_model

def cleanup_model():
    """Cleanup the global model instance"""
    global _inpainting_model
    if _inpainting_model is not None:
        _inpainting_model.cleanup()
        _inpainting_model = None 
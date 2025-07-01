import torch
from diffusers import StableDiffusionInpaintPipeline
from peft import PeftModel
from PIL import Image, ImageDraw
import numpy as np
import cv2
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class LoRAInpaintingModel:
    """
    LoRA Inpainting Model handler for meryemarpaci/sd2base-inpainting-lora
    """
    
    def __init__(self):
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_id = "stabilityai/stable-diffusion-2-inpainting"
        self.lora_model_id = "meryemarpaci/sd2base-inpainting-lora"
        self.loaded = False
        
    def load_model(self):
        """Load the LoRA inpainting model"""
        try:
            if self.loaded:
                return True
                
            logger.info(f"Loading LoRA inpainting model on {self.device}...")
            
            # Load the base inpainting pipeline
            self.pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            # Load LoRA weights
            try:
                self.pipeline.unet = PeftModel.from_pretrained(
                    self.pipeline.unet, 
                    self.lora_model_id
                )
                logger.info("LoRA weights loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load LoRA weights: {e}. Using base model.")
            
            # Move to device
            self.pipeline = self.pipeline.to(self.device)
            
            # Enable memory efficient attention if available
            if hasattr(self.pipeline, "enable_attention_slicing"):
                self.pipeline.enable_attention_slicing()
            
            if hasattr(self.pipeline, "enable_sequential_cpu_offload") and self.device == "cuda":
                self.pipeline.enable_sequential_cpu_offload()
            
            self.loaded = True
            logger.info("LoRA inpainting model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load LoRA inpainting model: {e}")
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
    
    def inpaint(self, image_path, mask_data, prompt, negative_prompt="", 
                num_inference_steps=50, guidance_scale=7.5, strength=1.0):
        """
        Perform inpainting on the given image
        
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
            if not self.loaded:
                if not self.load_model():
                    raise Exception("Failed to load model")
            
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
            
            logger.info(f"Starting inpainting with prompt: '{prompt}'")
            
            # Perform inpainting
            result = self.pipeline(
                prompt=prompt,
                image=image,
                mask_image=mask,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                strength=strength,
                generator=torch.Generator(device=self.device).manual_seed(42)
            ).images[0]
            
            logger.info("Inpainting completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Inpainting failed: {e}")
            raise e
    
    def cleanup(self):
        """Clean up model from memory"""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.loaded = False
        logger.info("Model cleaned up from memory")

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
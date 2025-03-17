"""
Cover Designer Agent
Specializes in generating book cover images using Stability AI.
"""
import os
import logging
import requests
from typing import Dict, Any, Optional
from core.agent import Agent

logger = logging.getLogger(__name__)

class CoverDesignerAgent(Agent):
    """
    Agent specialized in creating book cover images.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Cover Designer Agent"""
        super().__init__(name="Cover Designer", config=config, llm_provider=llm_provider)
    
    def generate_cover_image(self, title: str, genre: str, outline: str, 
                           output_path: str = "cover.png", 
                           orientation: str = "portrait") -> Optional[str]:
        """
        Generate a book cover image using Stability AI
        
        Args:
            title: Book title
            genre: Book genre
            outline: Book outline
            output_path: Path to save the image
            orientation: Image orientation (portrait/landscape/square)
            
        Returns:
            Path to the generated image, or None if generation failed
        """
        logger.info(f"Generating {orientation} cover image for {genre} book: {title}")
        
        # First, generate a cover prompt using the LLM
        prompt = self._generate_cover_prompt(title, genre, outline)
        
        try:
            # Use Stability AI to generate the image
            image_path = self._create_with_stability_ai(
                prompt=prompt, 
                output_path=output_path, 
                orientation=orientation
            )
            logger.info(f"Cover image generated successfully: {image_path}")
            return image_path
        except Exception as e:
            logger.error(f"Failed to generate cover image: {e}")
            return None
    
    def _generate_cover_prompt(self, title: str, genre: str, outline: str) -> str:
        """
        Generate a detailed prompt for the cover image
        
        Args:
            title: Book title
            genre: Book genre
            outline: Book outline
            
        Returns:
            A detailed prompt for image generation
        """
        prompt_request = f"""
        Create a detailed prompt for generating a book cover for a {genre} book titled "{title}".
        
        Book Outline:
        {outline[:1000]}...
        
        The prompt should:
        1. Describe key visual elements that would make a compelling cover
        2. Specify colors, mood, and artistic style appropriate for the {genre} genre
        3. Include any important symbols or motifs from the story
        4. Be optimized for an AI image generator (Stability AI)
        5. Be approximately 100-200 words
        
        Focus on creating a visually striking, marketable, and genre-appropriate cover design.
        Return ONLY the image generation prompt, nothing else.
        """
        
        response = self.generate(prompt_request, temperature=0.7)
        logger.info(f"Generated cover prompt: {response[:100]}...")
        return response
    
    def _create_with_stability_ai(self, prompt: str, output_path: str, orientation: str = "portrait") -> str:
        """
        Generate cover image using Stability AI
        
        Args:
            prompt: The detailed image generation prompt
            output_path: Path to save the generated image
            orientation: Desired image orientation (portrait/landscape/square)
            
        Returns:
            Path to the saved image
        """
        stability_api_key = os.environ.get('STABILITY_API_KEY')
        if not stability_api_key:
            raise ValueError("Missing STABILITY_API_KEY environment variable")
        
        # Map orientation to aspect ratio
        aspect_ratio_map = {
            "portrait": "2:3",
            "landscape": "3:2",
            "square": "1:1"
        }
        aspect_ratio = aspect_ratio_map.get(orientation, "2:3")  # Default to portrait
        
        # Determine model based on quality setting in config
        quality = self.config.get("output_settings", {}).get("cover_defaults", {}).get("quality", "standard")
        model_map = {
            "standard": "sd3-medium",
            "hd": "sd3-large"
        }
        model = model_map.get(quality, "sd3-medium")
        
        # Call Stability AI API
        try:
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/core",
                headers={
                    "Authorization": f"Bearer {stability_api_key}",
                    "Accept": "image/*"
                },
                files={
                    "prompt": (None, prompt),
                    "aspect_ratio": (None, aspect_ratio),
                    "model": (None, model),
                    "output_format": (None, "png"),
                    "seed": (None, "0"),  # Use random seed
                }
            )
            
            if response.status_code == 200:
                # Save the image
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
            else:
                raise Exception(f"Error from Stability AI: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Failed to generate image with Stability AI: {e}")
            raise
    
    def analyze_color_palette(self, genre: str) -> Dict[str, Any]:
        """
        Analyze appropriate color palettes for the given genre
        
        Args:
            genre: Book genre
            
        Returns:
            Dictionary with color palette recommendations
        """
        color_prompt = f"""
        Recommend a color palette for a {genre} book cover.
        
        Provide:
        1. Primary colors (2-3 main colors)
        2. Accent colors (1-2 secondary colors)
        3. Mood/atmosphere these colors convey
        4. Examples of similar {genre} books using this palette
        
        Format your response as JSON with these categories.
        """
        
        response = self.generate(color_prompt, temperature=0.5)
        return self.parse_json_response(response, default={
            "primary_colors": ["#000000", "#FFFFFF"],
            "accent_colors": ["#888888"],
            "mood": "Default neutral palette"
        })
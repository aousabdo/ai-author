"""
LLM Provider Interface
Manages communication with different LLM providers (OpenAI, Google Gemini)
with rate limiting and error handling.
"""
import os
import time
import random
import logging
from typing import Dict, Any, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMProvider:
    """Interface for LLM providers with unified API access"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM provider interface
        
        Args:
            config: Configuration dictionary with provider settings
        """
        self.config = config
        self.providers = {}
        self._setup_providers()
        
    def _setup_providers(self):
        """Set up the available LLM providers"""
        # Check for OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.providers["openai"] = {
                    "client": OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
                    "initialized": True
                }
                logger.info("OpenAI provider initialized")
            except ImportError:
                logger.warning("OpenAI package not found. Install with 'pip install openai'")
                self.providers["openai"] = {"initialized": False}
            except Exception as e:
                logger.error(f"Error initializing OpenAI: {e}")
                self.providers["openai"] = {"initialized": False}
        else:
            logger.warning("OPENAI_API_KEY environment variable not found")
            self.providers["openai"] = {"initialized": False}
            
        # Check for Google Gemini
        if os.getenv("GOOGLE_GEMINI_API_KEY"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
                
                # Determine available models
                model_name = self.config.get("llm_settings", {}).get("providers", {}).get("gemini", {}).get("model", "gemini-1.5-pro")
                
                # Initialize the model
                model = genai.GenerativeModel(model_name)
                
                self.providers["gemini"] = {
                    "client": model,
                    "initialized": True
                }
                logger.info(f"Google Gemini provider initialized with model {model_name}")
            except ImportError:
                logger.warning("Google Generative AI package not found. Install with 'pip install google-generativeai'")
                self.providers["gemini"] = {"initialized": False}
            except Exception as e:
                logger.error(f"Error initializing Google Gemini: {e}")
                self.providers["gemini"] = {"initialized": False}
        else:
            logger.warning("GOOGLE_GEMINI_API_KEY environment variable not found")
            self.providers["gemini"] = {"initialized": False}
    
    def generate_text(self, prompt: str, 
                      provider: Optional[str] = None, 
                      max_tokens: Optional[int] = None, 
                      temperature: Optional[float] = None) -> str:
        """
        Generate text using the specified or default LLM provider
        
        Args:
            prompt: The input prompt for text generation
            provider: The LLM provider to use ('openai' or 'gemini')
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness in generation
            
        Returns:
            The generated text
            
        Raises:
            Exception: If all providers fail or none are available
        """
        # Get default provider if not specified
        if provider is None or provider == "default":
            provider = self.config.get("llm_settings", {}).get("default_provider", "openai")
        
        # Fallback chain: try specified provider, then others if it fails
        providers_to_try = [provider]
        for p in self.providers:
            if p not in providers_to_try and self.providers[p].get("initialized", False):
                providers_to_try.append(p)
        
        # Get rate limiting settings
        rate_limit_config = self.config.get("llm_settings", {}).get("rate_limit", {})
        initial_delay = rate_limit_config.get("initial_delay", 1)
        max_retries = rate_limit_config.get("max_retries", 5)
        max_delay = rate_limit_config.get("max_delay", 60)
        
        # Try each provider
        last_error = None
        for current_provider in providers_to_try:
            if not self.providers.get(current_provider, {}).get("initialized", False):
                logger.warning(f"Provider {current_provider} not initialized, skipping")
                continue
                
            # Get provider-specific settings
            provider_config = self.config.get("llm_settings", {}).get("providers", {}).get(current_provider, {})
            current_max_tokens = max_tokens or provider_config.get("max_tokens", 4000)
            current_temperature = temperature or provider_config.get("default_temperature", 0.7)
            
            # Try with retries and exponential backoff
            retries = 0
            delay = initial_delay
            
            while retries < max_retries:
                try:
                    logger.info(f"Generating text with {current_provider} (attempt {retries+1}/{max_retries})")
                    
                    if current_provider == "openai":
                        return self._generate_with_openai(prompt, current_max_tokens, current_temperature)
                    elif current_provider == "gemini":
                        return self._generate_with_gemini(prompt, current_max_tokens, current_temperature)
                    else:
                        raise ValueError(f"Unknown provider: {current_provider}")
                        
                except Exception as e:
                    retries += 1
                    last_error = e
                    
                    if retries == max_retries:
                        logger.error(f"All attempts with provider {current_provider} failed: {e}")
                        break
                    
                    logger.warning(f"Attempt {retries}/{max_retries} failed: {e}")
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    
                    # Add jitter to avoid synchronized retries
                    jitter = random.uniform(0, 0.1 * delay) 
                    time.sleep(delay + jitter)
                    
                    # Exponential backoff with a maximum delay
                    delay = min(delay * 2, max_delay)
        
        # If we get here, all providers have failed
        raise Exception(f"All providers failed to generate text. Last error: {last_error}")
    
    def _generate_with_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using OpenAI"""
        client = self.providers["openai"]["client"]
        model = self.config.get("llm_settings", {}).get("providers", {}).get("openai", {}).get("model", "gpt-4o")
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_with_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text using Google Gemini"""
        import google.generativeai as genai
        from google.api_core.exceptions import ResourceExhausted
        
        model = self.providers["gemini"]["client"]
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
        )
        
        return response.text.strip()
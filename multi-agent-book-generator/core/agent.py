"""
Base Agent Class
Defines the core functionality for all specialized agents in the system.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class Agent:
    """Base class for all specialized agents in the system"""
    
    def __init__(self, name: str, config: Dict[str, Any], llm_provider=None):
        """
        Initialize the agent
        
        Args:
            name: The agent's name
            config: The global configuration dictionary
            llm_provider: The LLM provider to use
        """
        self.name = name
        self.config = config
        self.llm_provider = llm_provider
        self.memory = {}  # Agent's working memory
        
        # Get agent-specific settings
        agent_key = name.lower().replace(' ', '_')
        self.settings = config.get("agent_settings", {}).get(agent_key, {})
        
        # Set up logging for this agent
        self.prompt_log = []
        self.save_prompts = config.get("system_settings", {}).get("save_agent_prompts", True)
        
    def generate(self, prompt: str, 
                 max_tokens: Optional[int] = None,
                 temperature: Optional[float] = None,
                 provider: Optional[str] = None) -> str:
        """
        Generate text using the agent's assigned LLM
        
        Args:
            prompt: The input prompt for text generation
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness in generation
            provider: Specific provider to use
            
        Returns:
            The generated text
        """
        # Get agent-specific settings if not overridden
        if temperature is None:
            temperature = self.settings.get("temperature")
        
        if provider is None:
            provider = self.settings.get("provider", "default")
        
        # Log the prompt if enabled
        if self.save_prompts:
            self._log_prompt(prompt)
        
        # Generate text using the LLM provider
        return self.llm_provider.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            provider=provider
        )
    
    def _log_prompt(self, prompt: str) -> None:
        """Log the prompt for debugging and analysis"""
        timestamp = datetime.now().isoformat()
        self.prompt_log.append({
            "timestamp": timestamp,
            "prompt": prompt
        })
    
    def store_memory(self, key: str, value: Any) -> None:
        """Store information in agent's memory"""
        self.memory[key] = value
        
    def retrieve_memory(self, key: str, default: Any = None) -> Any:
        """Retrieve information from agent's memory"""
        return self.memory.get(key, default)
    
    def save_prompt_log(self, output_dir: str) -> None:
        """Save the prompt log to a file"""
        if not self.save_prompts or not self.prompt_log:
            return
            
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{self.name.lower().replace(' ', '_')}_{timestamp}_prompts.json"
        
        with open(filename, 'w') as f:
            json.dump(self.prompt_log, f, indent=2)
        
        logger.info(f"Saved prompt log to {filename}")
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """
        Format a prompt template with variables
        
        Args:
            template: The prompt template string
            **kwargs: Variables to insert into the template
            
        Returns:
            The formatted prompt
        """
        return template.format(**kwargs)
    
    def parse_json_response(self, response: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parse a JSON response, with fallback for invalid JSON
        
        Args:
            response: The text response to parse as JSON
            default: Default value to return if parsing fails
            
        Returns:
            Parsed JSON as dictionary
        """
        # Set default fallback value
        if default is None:
            default = {}
            
        # Extract JSON if embedded in text
        try:
            # Try to find JSON block if response includes other text
            import re
            json_matches = re.findall(r'```json\n(.*?)\n```', response, re.DOTALL)
            
            if json_matches:
                # Use the first JSON block found
                json_str = json_matches[0]
            else:
                # Assume the entire response is JSON
                json_str = response
                
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse response as JSON: {response[:100]}...")
            return default
        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}")
            return default
    
    def check_response_quality(self, response: str, min_length: int = 10) -> bool:
        """
        Check if a response meets basic quality criteria
        
        Args:
            response: The response to check
            min_length: Minimum acceptable length
            
        Returns:
            True if the response meets quality criteria
        """
        if not response or len(response) < min_length:
            return False
            
        # Additional quality checks could be added here
        return True
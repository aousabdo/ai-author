#!/usr/bin/env python3
"""
Multi-Agent Book Generator
Main entry point for the book generation system
"""
import os
import sys
import json
import argparse
import logging
from typing import Dict, Any
from core.orchestrator import BookGenerationOrchestrator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('book_generation.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from a file or use default
    
    Args:
        config_path: Path to a JSON configuration file
        
    Returns:
        Configuration dictionary
    """
    # Default config file
    default_config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    # Try to load specified config, fall back to default
    try:
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        elif os.path.exists(default_config_path):
            with open(default_config_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning("No configuration file found. Using empty config.")
            return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.warning("Using empty config.")
        return {}

def main():
    """Main entry point for the book generation system"""
    parser = argparse.ArgumentParser(description="Generate a book using an AI multi-agent system")
    
    # Configuration and book parameters
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--style", help="Writing style for the book (e.g., 'descriptive', 'concise')")
    parser.add_argument("--description", help="High-level description of the book's plot")
    parser.add_argument("--chapters", type=int, help="Number of chapters to generate")
    parser.add_argument("--genre", help="Genre of the book (e.g., 'fantasy', 'sci-fi')")
    
    # Mode settings
    parser.add_argument("--interactive", action="store_true", help="Enable interactive mode")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = load_config(args.config)
    
    # Update config with command line arguments
    if args.style:
        config["writing_style"] = args.style
    if args.description:
        config["description"] = args.description
    if args.chapters:
        config["num_chapters"] = args.chapters
    if args.genre:
        config["genre"] = args.genre
    if args.interactive:
        config["system_settings"] = config.get("system_settings", {})
        config["system_settings"]["interactive_mode"] = True
    if args.output:
        config["output_settings"] = config.get("output_settings", {})
        config["output_settings"]["output_directory"] = args.output
    
    # Validate required config
    required_params = ["writing_style", "description", "num_chapters", "genre"]
    missing_params = [param for param in required_params if param not in config]
    
    if missing_params:
        print("Error: Missing required parameters:", ", ".join(missing_params))
        print("Please provide these parameters via command line or configuration file.")
        return 1
    
    # Create output directory
    os.makedirs(config["output_settings"]["output_directory"], exist_ok=True)
    
    # Initialize the orchestrator
    orchestrator = BookGenerationOrchestrator(config)
    
    # Run the book generation process
    print("\n=== AI Book Generator ===")
    print(f"Genre: {config['genre']}")
    print(f"Style: {config['writing_style']}")
    print(f"Chapters: {config['num_chapters']}")
    print(f"Output: {config['output_settings']['output_directory']}")
    print("=======================\n")
    
    try:
        success = orchestrator.run()
        
        if success:
            print("\n✅ Book generation completed successfully!")
            print(f"Output files are in: {config['output_settings']['output_directory']}")
            return 0
        else:
            print("\n❌ Book generation failed. Check the logs for details.")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ Book generation interrupted by user.")
        return 130
    except Exception as e:
        logger.exception("Unhandled exception during book generation")
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
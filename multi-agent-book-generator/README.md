# Multi-Agent Book Generation System

An advanced AI system for generating high-quality books using a specialized multi-agent architecture. Each agent focuses on a different aspect of the book creation process, resulting in more coherent, consistent, and engaging stories.

## Features

- **Specialized Agent System**: Each aspect of book creation handled by a dedicated expert agent
- **Advanced Continuity Checking**: Maintains consistent plot, characters, and setting
- **Sophisticated Dialogue System**: Creates natural, character-specific dialogue
- **Dynamic Pacing Control**: Ensures proper story flow and rhythm
- **Style Consistency**: Maintains consistent writing style throughout
- **Quality Assurance**: Performs comprehensive quality checks
- **Multiple Output Formats**: Generates both text and EPUB files

## Architecture

The system uses a multi-agent architecture with eight specialized agents:

1. **Plot Architect**: Creates coherent plot outlines and narrative structures
2. **Character Designer**: Develops detailed character profiles and arcs
3. **Writer**: Generates engaging prose based on outlines
4. **Continuity Checker**: Ensures narrative consistency across chapters
5. **Style Reviewer**: Maintains consistent writing style and voice
6. **Pacing Advisor**: Optimizes story flow and scene transitions
7. **Dialogue Expert**: Creates natural, character-specific dialogue
8. **Quality Analyst**: Performs final quality assessment and improvements

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key (for GPT-4/4o models)
- Google Gemini API key (optional)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/aousabdo/multi-agent-book-generator.git
   cd multi-agent-book-generator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up API keys:
   ```bash
   # On Linux/Mac
   export OPENAI_API_KEY=your_openai_api_key
   export GOOGLE_GEMINI_API_KEY=your_gemini_api_key  # Optional
   
   # On Windows
   set OPENAI_API_KEY=your_openai_api_key
   set GOOGLE_GEMINI_API_KEY=your_gemini_api_key  # Optional
   ```

## Usage

### Basic Usage

Generate a book with default settings:

```bash
python main.py --style "descriptive" --description "A thrilling adventure story about a treasure hunter who discovers an ancient artifact with mysterious powers." --chapters 10 --genre "adventure"
```

### Advanced Options

```bash
python main.py --style "literary" --description "A coming-of-age story set in rural America during the 1960s." --chapters 12 --genre "literary fiction" --interactive --output ./my_books
```

### Configuration File

You can also provide a configuration file:

```bash
python main.py --config my_config.json
```

Example `config.json`:
```json
{
  "writing_style": "descriptive",
  "description": "A science fiction novel about first contact with an alien species.",
  "num_chapters": 15,
  "genre": "science fiction",
  "system_settings": {
    "interactive_mode": true
  },
  "output_settings": {
    "output_directory": "./my_books",
    "formats": ["txt", "epub"]
  }
}
```

## Output

The system generates the following files:

- Complete book in text format
- EPUB ebook file with chapters and metadata
- Book metadata in JSON format
- Detailed generation metrics and logs

## Extending the System

### Adding New Agents

1. Create a new agent class in the `agents` directory
2. Inherit from the base `Agent` class
3. Implement specialized methods
4. Register the agent in the orchestrator

### Customizing Generation

The system is highly configurable through:

- The `config.json` file
- Command-line parameters
- Custom agent implementations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
#!/bin/bash

# Define the base project directory
PROJECT_DIR="multi-agent-book-generator"

# Define the directory structure
DIRECTORIES=(
    "$PROJECT_DIR/core"
    "$PROJECT_DIR/agents"
    "$PROJECT_DIR/utils"
    "$PROJECT_DIR/output"
)

# Define the files to create
FILES=(
    "$PROJECT_DIR/README.md"
    "$PROJECT_DIR/requirements.txt"
    "$PROJECT_DIR/main.py"
    "$PROJECT_DIR/config.json"
    "$PROJECT_DIR/core/__init__.py"
    "$PROJECT_DIR/core/agent.py"
    "$PROJECT_DIR/core/orchestrator.py"
    "$PROJECT_DIR/core/llm_provider.py"
    "$PROJECT_DIR/agents/__init__.py"
    "$PROJECT_DIR/agents/plot_architect.py"
    "$PROJECT_DIR/agents/character_designer.py"
    "$PROJECT_DIR/agents/writer.py"
    "$PROJECT_DIR/agents/continuity_checker.py"
    "$PROJECT_DIR/agents/style_reviewer.py"
    "$PROJECT_DIR/agents/pacing_advisor.py"
    "$PROJECT_DIR/agents/dialogue_expert.py"
    "$PROJECT_DIR/agents/quality_analyst.py"
    "$PROJECT_DIR/utils/__init__.py"
    "$PROJECT_DIR/utils/parsing.py"
    "$PROJECT_DIR/utils/text_processing.py"
    "$PROJECT_DIR/utils/epub_builder.py"
    "$PROJECT_DIR/output/.gitkeep"
)

# Create directories
for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
    echo "Created directory: $dir"
done

# Create empty files
for file in "${FILES[@]}"; do
    touch "$file"
    echo "Created file: $file"
done

# Add a sample JSON configuration
cat <<EOL > "$PROJECT_DIR/config.json"
{
    "book_title": "Untitled",
    "author": "Anonymous",
    "language": "English",
    "chapters": 10,
    "agents": {
        "plot_architect": true,
        "character_designer": true,
        "writer": true,
        "continuity_checker": true,
        "style_reviewer": true,
        "pacing_advisor": true,
        "dialogue_expert": true,
        "quality_analyst": true
    }
}
EOL
echo "Created sample config.json"

# Add a basic README
cat <<EOL > "$PROJECT_DIR/README.md"
# Multi-Agent Book Generator

This project utilizes multiple AI-driven agents to collaboratively generate a book, ensuring structured storytelling, character consistency, and high-quality text output.

## Installation
Run the following command to install dependencies:
\`\`\`
pip install -r requirements.txt
\`\`\`

## Usage
Execute the main script to start the book generation process:
\`\`\`
python main.py
\`\`\`
EOL
echo "Created README.md"

# Make the script executable
chmod +x "$0"

echo "Project setup complete!"

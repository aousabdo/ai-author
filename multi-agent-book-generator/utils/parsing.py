"""
Parsing utilities for processing outlines and structured data.
"""
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def parse_outline(outline: str) -> List[Dict[str, Any]]:
    """
    Parse a chapter-by-chapter outline into structured data
    
    Args:
        outline: The chapter-by-chapter outline text
        
    Returns:
        List of dictionaries, each representing a chapter
    """
    # Initialize empty list for parsed chapters
    chapters = []
    
    # Try to split by chapter blocks
    chapter_pattern = r'Chapter (\d+):\s*(.*?)(?=\n(?:Summary|Estimated))'
    chapter_matches = re.findall(chapter_pattern, outline, re.DOTALL)
    
    if not chapter_matches:
        # If no matches found, try alternative pattern without requiring chapter number
        chapter_pattern = r'(?:Chapter \d+|Chapter):\s*(.*?)(?=\n(?:Summary|Estimated))'
        alt_matches = re.findall(chapter_pattern, outline, re.DOTALL)
        
        if alt_matches:
            # Convert to format with chapter numbers
            chapter_matches = [(str(i+1), title.strip()) for i, title in enumerate(alt_matches)]
    
    # Process each chapter match
    for i, (chapter_num, title) in enumerate(chapter_matches):
        # Extract the full chapter block to get summary and word count
        chapter_block_pattern = f'Chapter {chapter_num}:.*?(?=Chapter {int(chapter_num)+1}:|$)'
        chapter_block_match = re.search(chapter_block_pattern, outline, re.DOTALL)
        
        if not chapter_block_match:
            # If no match, use a simpler approach
            parts = outline.split(f"Chapter {int(chapter_num)+1}:")[0].split(f"Chapter {chapter_num}:")[1]
            chapter_block = parts.strip()
        else:
            chapter_block = chapter_block_match.group(0)
        
        # Extract summary
        summary_pattern = r'Summary:\s*(.*?)(?=\nEstimated|$)'
        summary_match = re.search(summary_pattern, chapter_block, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""
        
        # Extract estimated word count
        word_count_pattern = r'Estimated word count:\s*(\d[,\d]*)'
        word_count_match = re.search(word_count_pattern, chapter_block)
        
        if word_count_match:
            word_count_str = word_count_match.group(1).replace(',', '')
            try:
                word_count = int(word_count_str)
            except ValueError:
                word_count = 3000  # Default if conversion fails
        else:
            word_count = 3000  # Default if not found
        
        # Create chapter dictionary
        chapter = {
            "chapter_num": int(chapter_num),
            "title": title.strip(),
            "summary": summary,
            "word_count": word_count
        }
        
        chapters.append(chapter)
    
    # If parsing failed or returned empty list, attempt a more lenient approach
    if not chapters:
        logger.warning("Standard parsing failed. Attempting lenient parsing of outline.")
        chapters = _lenient_parse_outline(outline)
    
    # Sort chapters by number (in case they were extracted out of order)
    chapters.sort(key=lambda x: x["chapter_num"])
    
    return chapters

def _lenient_parse_outline(outline: str) -> List[Dict[str, Any]]:
    """
    Fallback parser that uses more lenient rules to extract chapter information
    
    Args:
        outline: The chapter-by-chapter outline text
        
    Returns:
        List of dictionaries, each representing a chapter
    """
    chapters = []
    
    # Split by obvious chapter markers
    chapter_blocks = re.split(r'Chapter \d+|CHAPTER \d+', outline)
    
    # Remove the first element if it's empty (text before first chapter)
    if chapter_blocks and not chapter_blocks[0].strip():
        chapter_blocks = chapter_blocks[1:]
    
    for i, block in enumerate(chapter_blocks):
        if not block.strip():
            continue
            
        # Try to extract title
        title_match = re.search(r'[:\-–—]\s*([^\n]+)', block)
        title = title_match.group(1).strip() if title_match else f"Chapter {i+1}"
        
        # Try to extract summary (everything between title and word count or end)
        summary = block
        if title_match:
            summary = summary.replace(title_match.group(0), "", 1)
        
        # Remove word count information if present
        word_count_pattern = r'(?:Estimated|Target|Approximate)[^\d]*(\d[,\d]*)[^\d]*words'
        word_count_match = re.search(word_count_pattern, summary, re.IGNORECASE)
        
        word_count = 3000  # Default
        if word_count_match:
            word_count_str = word_count_match.group(1).replace(',', '')
            try:
                word_count = int(word_count_str)
            except ValueError:
                pass
            
            # Remove word count from summary
            summary = re.sub(word_count_pattern, "", summary, flags=re.IGNORECASE)
        
        # Clean up summary
        summary = summary.strip()
        
        # Create chapter dictionary
        chapter = {
            "chapter_num": i + 1,
            "title": title,
            "summary": summary,
            "word_count": word_count
        }
        
        chapters.append(chapter)
    
    return chapters

def extract_character_profiles(profiles_text: str) -> List[Dict[str, Any]]:
    """
    Extract individual character profiles from a combined text
    
    Args:
        profiles_text: Text containing multiple character profiles
        
    Returns:
        List of dictionaries, each representing a character profile
    """
    # Try to identify character blocks by name/title patterns
    character_blocks = re.split(r'\n\s*(?=\d+\.\s+|\*\*|\#\#|Character\s+\d+:|Character name:|Name:)', profiles_text)
    
    # Remove empty blocks
    character_blocks = [block.strip() for block in character_blocks if block.strip()]
    
    characters = []
    
    for block in character_blocks:
        # Try to extract character name
        name_match = re.search(r'(?:\d+\.\s+|\*\*|\#\#|Character\s+\d+:|Character name:|Name:)\s*([^\n]+)', block)
        name = name_match.group(1).strip() if name_match else "Unknown Character"
        
        # Try to extract role
        role_match = re.search(r'(?:Role|Role in story|Character role):\s*([^\n]+)', block, re.IGNORECASE)
        role = role_match.group(1).strip() if role_match else ""
        
        # Try to extract personality
        personality_match = re.search(r'(?:Personality|Traits|Character traits):\s*(.*?)(?=\n\s*\w+:|$)', block, re.IGNORECASE | re.DOTALL)
        personality = personality_match.group(1).strip() if personality_match else ""
        
        # Try to extract goals/motivations
        goals_match = re.search(r'(?:Goals|Motivations|Goals and motivations):\s*(.*?)(?=\n\s*\w+:|$)', block, re.IGNORECASE | re.DOTALL)
        goals = goals_match.group(1).strip() if goals_match else ""
        
        # Create character dictionary
        character = {
            "name": name,
            "role": role,
            "personality": personality,
            "goals": goals,
            "full_profile": block
        }
        
        characters.append(character)
    
    # If parsing failed or returned empty list, use the whole text as a single character profile
    if not characters:
        logger.warning("Character profile parsing returned no results. Using text as is.")
        characters = [{
            "name": "Main Character",
            "role": "",
            "personality": "",
            "goals": "",
            "full_profile": profiles_text
        }]
    
    return characters

def parse_feedback(feedback_text: str) -> Dict[str, Any]:
    """
    Parse feedback from QA or review agents into structured data
    
    Args:
        feedback_text: Feedback text to parse
        
    Returns:
        Dictionary with parsed feedback
    """
    # Try to parse as JSON first
    import json
    try:
        return json.loads(feedback_text)
    except json.JSONDecodeError:
        pass
    
    # If not valid JSON, parse manually
    result = {
        "issues": [],
        "suggestions": []
    }
    
    # Extract issues
    issues_match = re.search(r'(?:Issues|Problems|Errors):\s*(.*?)(?=\n\s*\w+:|$)', feedback_text, re.IGNORECASE | re.DOTALL)
    if issues_match:
        issues_text = issues_match.group(1)
        # Split by numbered or bulleted list items
        issues = re.findall(r'(?:\d+\.|\*|\-)\s*([^\n]+)', issues_text)
        result["issues"] = [issue.strip() for issue in issues if issue.strip()]
    
    # Extract suggestions
    suggestions_match = re.search(r'(?:Suggestions|Recommendations|Fixes):\s*(.*?)(?=\n\s*\w+:|$)', feedback_text, re.IGNORECASE | re.DOTALL)
    if suggestions_match:
        suggestions_text = suggestions_match.group(1)
        # Split by numbered or bulleted list items
        suggestions = re.findall(r'(?:\d+\.|\*|\-)\s*([^\n]+)', suggestions_text)
        result["suggestions"] = [suggestion.strip() for suggestion in suggestions if suggestion.strip()]
    
    # Try to extract rating if present
    rating_match = re.search(r'(?:Rating|Score|Overall):\s*(\d+(?:\.\d+)?)', feedback_text, re.IGNORECASE)
    if rating_match:
        try:
            result["rating"] = float(rating_match.group(1))
        except ValueError:
            pass
    
    return result
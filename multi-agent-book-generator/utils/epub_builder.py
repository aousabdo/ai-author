"""
EPUB building utilities for creating ebook files from generated content.
"""
import os
import logging
import markdown2
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def create_epub(title: str, author: str, chapters: List[str], chapter_titles: List[str], 
               output_path: str, cover_image_path: Optional[str] = None) -> str:
    """
    Create an EPUB file from chapters
    
    Args:
        title: Book title
        author: Book author
        chapters: List of chapter contents
        chapter_titles: List of chapter titles
        output_path: Path to save the EPUB file
        cover_image_path: Path to cover image (optional)
        
    Returns:
        Path to the created EPUB file
    """
    try:
        from ebooklib import epub
    except ImportError:
        logger.error("ebooklib not installed. Install with 'pip install ebooklib'")
        raise ImportError("ebooklib not installed. Install with 'pip install ebooklib'")
    
    # Initialize the EPUB book
    book = epub.EpubBook()
    
    # Set metadata
    book.set_identifier(f"id-{int(datetime.now().timestamp())}")
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)
    
    # Add cover image if provided
    if cover_image_path and os.path.exists(cover_image_path):
        with open(cover_image_path, 'rb') as cover_file:
            cover_image = cover_file.read()
        book.set_cover('cover.png', cover_image)
    
    # Create chapters and add them to the book
    epub_chapters = []
    
    for i, (chapter_content, chapter_title) in enumerate(zip(chapters, chapter_titles)):
        # Create chapter
        chapter_filename = f'chapter_{i+1}.xhtml'
        epub_chapter = epub.EpubHtml(title=chapter_title, file_name=chapter_filename, lang='en')
        
        # Convert chapter content to HTML
        html_content = markdown2.markdown(chapter_content)
        
        # Add chapter title heading
        epub_chapter.content = f'<h1>{chapter_title}</h1>{html_content}'
        
        # Add chapter to book
        book.add_item(epub_chapter)
        epub_chapters.append(epub_chapter)
    
    # Define Table of Contents
    book.toc = tuple(epub_chapters)
    
    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Define CSS style
    style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: Cambria, Liberation Serif, serif;
        line-height: 1.6;
        margin: 0;
        padding: 1em;
    }
    h1 {
        text-align: center;
        text-transform: uppercase;
        font-weight: 200;
        margin-bottom: 1em;
        font-size: 1.8em;
    }
    h2 {
        font-size: 1.5em;
        margin-top: 1em;
        margin-bottom: 0.5em;
    }
    p {
        margin-bottom: 0.5em;
        text-indent: 1.5em;
    }
    p:first-of-type, 
    h1 + p {
        text-indent: 0;
    }
    '''
    
    # Add CSS file
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)
    
    # Create spine
    book.spine = ['nav'] + epub_chapters
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Write the EPUB file
    epub.write_epub(output_path, book)
    
    logger.info(f"EPUB file created: {output_path}")
    return output_path

def create_chapter_previews(chapters: List[str], max_preview_words: int = 100) -> List[str]:
    """
    Create short previews for each chapter
    
    Args:
        chapters: List of chapter contents
        max_preview_words: Maximum number of words in each preview
        
    Returns:
        List of chapter previews
    """
    previews = []
    
    for chapter in chapters:
        # Get the first few words
        words = chapter.split()
        preview = ' '.join(words[:max_preview_words])
        
        # Add ellipsis if truncated
        if len(words) > max_preview_words:
            preview += '...'
            
        previews.append(preview)
    
    return previews

def create_book_description(title: str, outline: str, character_profiles: str) -> str:
    """
    Create a book description for marketing purposes
    
    Args:
        title: Book title
        outline: Book outline
        character_profiles: Character profiles
        
    Returns:
        Book description
    """
    # Extract key information from the outline
    outline_preview = outline[:1000] if len(outline) > 1000 else outline
    
    # Extract character names
    # import re
    character_names = re.findall(r'(?:Character|Name):\s*([^\n]+)', character_profiles)
    character_names = [name.strip() for name in character_names if name.strip()]
    
    # Create a description template
    description = f"""
# {title}

## About the Book

{outline_preview}

## Main Characters

{', '.join(character_names[:5])}

---

This book was generated using an AI multi-agent system.
    """
    
    return description.strip()

def convert_to_plain_text(chapters: List[str], chapter_titles: List[str], title: str, author: str) -> str:
    """
    Convert book content to plain text format
    
    Args:
        chapters: List of chapter contents
        chapter_titles: List of chapter titles
        title: Book title
        author: Book author
        
    Returns:
        Plain text version of the book
    """
    text = f"{title}\nby {author}\n\n"
    
    for i, (chapter, title) in enumerate(zip(chapters, chapter_titles)):
        text += f"Chapter {i+1}: {title}\n\n"
        text += chapter
        text += "\n\n"
    
    return text

def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content for EPUB
    
    Args:
        html_content: HTML content to sanitize
        
    Returns:
        Sanitized HTML content
    """
    # import re  # Added re import here
    
    # Remove potentially problematic tags
    disallowed_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button']
    
    for tag in disallowed_tags:
        # Remove opening tags
        html_content = re.sub(f'<{tag}[^>]*>', '', html_content, flags=re.IGNORECASE)
        # Remove closing tags
        html_content = re.sub(f'</{tag}[^>]*>', '', html_content, flags=re.IGNORECASE)
    
    return html_content
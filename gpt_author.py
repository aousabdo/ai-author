"""
AI-powered Book Generator using OpenAI, Google's Gemini API, and Stability AI

This script generates a complete book, including plot, chapters, title, and cover image,
based on user-provided parameters. It uses the OpenAI GPT-4o-mini or Google Gemini API 
for text generation and Stability AI for cover image creation.

Author: AI Assistant
Date: 2024-09-30
Dependencies: google-generativeai, ebooklib, requests, openai, markdown2
"""

import os
import time
import re
import argparse
import requests
import markdown2
import string
from ebooklib import epub
import google.generativeai as genai
import random
from google.api_core.exceptions import ResourceExhausted
from openai import OpenAI

# Configure Gemini API
GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
if not GOOGLE_GEMINI_API_KEY:
    raise ValueError("Missing GOOGLE_GEMINI_API_KEY environment variable.")
genai.configure(api_key=GOOGLE_GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-exp-0827")

# Configure OpenAI API
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def remove_first_line(text):
    """
    Remove the first line of the string if it starts with "Here" and ends with ":".

    Args:
        text (str): The input string to process.

    Returns:
        str: The processed string with the first line removed if it matches the condition.
    """
    lines = text.split('\n')
    if lines and lines[0].startswith("Here") and lines[0].strip().endswith(":"):
        return '\n'.join(lines[1:])
    return text

def generate_text(prompt, max_tokens=4000, temperature=0.7, max_retries=5, initial_delay=1, llm="openai"):
    """
    Generate text using either OpenAI or Google Gemini API with rate limiting and exponential backoff.

    Args:
        prompt (str): The input prompt for text generation.
        max_tokens (int): Maximum number of tokens to generate.
        temperature (float): Controls randomness in generation.
        max_retries (int): Maximum number of retry attempts.
        initial_delay (float): Initial delay between retries in seconds.
        llm (str): The LLM to use. Either "openai" (default) or "gemini".

    Returns:
        str: The generated text.

    Raises:
        Exception: If the API call fails after all retries.
    """
    retries = 0
    delay = initial_delay

    while retries < max_retries:
        try:
            if llm == "openai":
                print("Using OpenAI GPT-4o-mini model")
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            elif llm == "gemini":
                print("Using Google Gemini 1.5 Pro model")
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature
                    )
                )
                return response.text.strip()
            else:
                raise ValueError("Invalid LLM specified. Choose 'openai' or 'gemini'.")
        except (ResourceExhausted, Exception) as e:
            retries += 1
            if retries == max_retries:
                raise Exception(f"Failed to generate text after {max_retries} attempts: {e}")
            
            print(f"Error (attempt {retries}/{max_retries}): {e}")
            print(f"Retrying in {delay:.2f} seconds...")
            
            # Add jitter to avoid synchronized retries
            jitter = random.uniform(0, 0.1 * delay)
            time.sleep(delay + jitter)
            
            # Exponential backoff with a maximum delay of 60 seconds
            delay = min(delay * 2, 60)

    raise Exception("Unexpected error: Retry loop completed without returning or raising")

def generate_cover_prompt(plot, genre):
    try:
        response = generate_text(
            f"Plot: {plot}\n\n"
            f"Genre: {genre}\n\n"
            f"--\n\n"
            f"Describe an engaging and genre-appropriate book cover we should create, based on the plot and genre. "
            f"This should be two sentences long, maximum."
        )
        return response
    except Exception as e:
        print(f"Error generating cover prompt: {e}")
        return "A generic book cover suitable for the genre."

def generate_title(plot, genre):
    try:
        response = generate_text(
            f"Based on the following plot outline and genre, generate a captivating and genre-appropriate title for the book.\n\n"
            f"Plot Outline:\n{plot}\n\n"
            f"Genre: {genre}\n\n"
            f"Respond with the best title only, in one sentence, without any additional commentary.\n\n"
            f"Title:"
        )
        return response.strip()
    except Exception as e:
        print(f"Error generating title: {e}")
        return "Untitled"

def sanitize_filename(filename):
    """
    Sanitize the filename by removing invalid characters and limiting its length.

    Args:
        filename (str): The original filename.

    Returns:
        str: A sanitized filename safe for use in file systems.
    """
    # Remove invalid characters
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    sanitized = ''.join(c for c in filename if c in valid_chars)
    # Limit the filename length
    return sanitized[:100]

def create_cover_image(plot, orientation="portrait", quality="standard", genre="fantasy"):
    """
    Create a cover image based on the plot using DALL-E 3.

    Args:
        plot (str): The plot outline of the book.
        orientation (str): Either "portrait", "landscape", or "square". Default is "portrait".
        quality (str): Either "standard" or "hd". Default is "standard".

    Raises:
        Exception: If the OpenAI API key is missing or the API response is not successful.
    """
    # Generate the cover description from the plot
    plot = str(generate_cover_prompt(plot, genre))

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if openai_client.api_key is None:
        raise Exception("Missing OpenAI API key.")

    # Determine size based on orientation
    if orientation == "portrait":
        size = "1024x1792"
    elif orientation == "landscape":
        size = "1792x1024"
    else:  # square
        size = "1024x1024"

    # Make a request to the DALL-E 3 API to generate the cover image
    response = openai_client.images.generate(
        model="dall-e-3",
        prompt=plot,
        size=size,
        quality=quality,
        n=1,
    )

    image_url = response.data[0].url

    # Download and save the generated image
    image_response = requests.get(image_url)
    if image_response.status_code != 200:
        raise Exception("Failed to download the image")

    with open("cover.png", "wb") as f:
        f.write(image_response.content)

def create_cover_image_stability_ai(plot, orientation="portrait", quality="standard", genre="fantasy"):
    """
    Create a cover image based on the plot using Stability AI.

    Args:
        plot (str): The plot outline of the book.
        orientation (str): Either "portrait", "landscape", or "square". Default is "portrait".
        quality (str): Either "standard" or "hd". Default is "standard".
        genre (str): The genre of the book. Default is "fantasy".

    Raises:
        Exception: If the Stability AI API key is missing or the API response is not successful.
    """
    stability_api_key = os.environ.get('STABILITY_API_KEY')
    if not stability_api_key:
        raise Exception("Missing Stability AI API key.")

    # Generate the cover description from the plot
    prompt = f"Book cover for a {genre} novel. {plot}"
    # prompt = "A fantasy book cover with a dragon"

    # Map orientation to aspect ratio
    aspect_ratio_map = {
        "portrait": "2:3",
        "landscape": "3:2",
        "square": "1:1"
    }
    aspect_ratio = aspect_ratio_map.get(orientation, "1:1")

    # Map quality to model
    model_map = {
        "standard": "sd3-medium",
        "hd": "sd3-large"
    }
    model = model_map.get(quality, "sd3-medium")

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
        with open("cover.png", "wb") as f:
            f.write(response.content)
        print("Cover image generated successfully.")
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")
    
def generate_chapter_title(chapter_content):
    """
    Generate a title for a chapter based on its content.

    Args:
        chapter_content (str): The content of the chapter.

    Returns:
        str: The generated chapter title.
    """
    response = generate_text(
        f"Chapter Content:\n\n{chapter_content}\n\n"
        f"--\n\n"
        f"Generate a concise and engaging title for this chapter based on its content. Respond with the title only, nothing else."
    )
    return remove_first_line(response)

def create_epub(title, author, chapters, cover_image_path='cover.png'):
    """
    Create an EPUB file from the generated book content.

    Args:
        title (str): The title of the book.
        author (str): The author of the book.
        chapters (list): A list of chapter contents.
        cover_image_path (str, optional): Path to the cover image. Defaults to 'cover.png'.
    """
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier('id123456')
    book.set_title(title)
    book.set_language('en')
    book.add_author(author)

    # Add cover image
    with open(cover_image_path, 'rb') as cover_file:
        cover_image = cover_file.read()
    book.set_cover('cover.png', cover_image)

    # Create chapters and add them to the book
    epub_chapters = []
    for i, chapter_content in enumerate(chapters):
        chapter_title = generate_chapter_title(chapter_content)
        chapter_file_name = f'chapter_{i+1}.xhtml'
        epub_chapter = epub.EpubHtml(title=chapter_title, file_name=chapter_file_name, lang='en')

        # Convert Markdown to HTML
        html_content = markdown2.markdown(chapter_content)

        epub_chapter.content = f'<h1>{chapter_title}</h1>{html_content}'
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
    }
    h1 {
        text-align: left;
        text-transform: uppercase;
        font-weight: 200;
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

    # Save the EPUB file
    epub.write_epub(f'{title}.epub', book)

def generate_book(writing_style, book_description, num_chapters, genre):
    """
    Generate a complete book based on the given parameters.

    Args:
        writing_style (str): The desired writing style for the book.
        book_description (str): A high-level description of the book.
        num_chapters (int): The number of chapters to generate.
        genre (str): The genre of the book.

    Returns:
        tuple: A tuple containing the plot outline, full book text, and a list of chapters.
    """
    print("Generating plot outline...")
    plot_prompt = (
        f"Create a comprehensive and detailed plot outline for a {num_chapters}-chapter {genre} novel "
        f"written in the {writing_style} style. The outline should be based on the following description:\n\n"
        f"{book_description}\n\n"
        f"Include key events, character arcs, settings, and conflicts for each chapter. "
        f"Ensure the narrative flow is coherent and engaging."
    )

    try:
        plot_outline = generate_text(plot_prompt)
        print("Plot outline generated.")
    except Exception as e:
        print(f"Error generating plot outline: {e}")
        plot_outline = "Plot outline generation failed."

    chapters = []
    for i in range(num_chapters):
        print(f"Generating chapter {i+1}...")
        chapter_prompt = (
            f"Using the plot outline and previous chapters, write chapter {i+1} of the {genre} novel in the {writing_style} style.\n\n"
            f"Plot Outline:\n{plot_outline}\n\n"
            f"Previous Chapters:\n{' '.join(chapters)}\n\n"
            f"Include key events, character developments, and conflicts relevant to this chapter. "
            f"Ensure the chapter is engaging and contributes to the overall narrative.\n\n"
            f"Chapter {i+1} Content:"
        )
        try:
            chapter = generate_text(chapter_prompt, max_tokens=4000)
            chapters.append(remove_first_line(chapter))
            print(f"Chapter {i+1} generated.")
        except Exception as e:
            print(f"Error generating chapter {i+1}: {e}")
            chapters.append(f"Chapter {i+1} generation failed.")
        
        time.sleep(1)  # Add a short delay to avoid hitting rate limits

    print("Compiling the book...")
    book = "\n\n".join(chapters)
    print("Book generated!")

    return plot_outline, book, chapters

def main(writing_style, book_description, num_chapters, genre):
    """
    Main function to orchestrate the book generation process.

    Args:
        writing_style (str): The desired writing style for the book.
        book_description (str): A high-level description of the book.
        num_chapters (int): The number of chapters to generate.
        genre (str): The genre of the book.
    """
    # Generate the book
    plot_outline, book, chapters = generate_book(writing_style, book_description, num_chapters, genre)

    title = generate_title(plot_outline, genre)
    sanitized_title = sanitize_filename(title)

    # Save the book to a file
    with open(f"{sanitized_title}.txt", "w") as file:
        file.write(book)

    create_cover_image_stability_ai(plot_outline, genre)

    # Create the EPUB file
    create_epub(title, 'AI', chapters, 'cover.png')

    print(f"Book saved as '{sanitized_title}.txt' and '{title}.epub'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a book using AI")
    parser.add_argument("--style", required=True, help="The desired writing style (e.g., 'descriptive', 'concise')")
    parser.add_argument("--description", required=True, help="A high-level description of the book's plot")
    parser.add_argument("--chapters", type=int, required=True, help="The number of chapters (e.g., 10)")
    parser.add_argument("--genre", required=True, help="The genre of the book (e.g., 'fantasy', 'science fiction')")

    args = parser.parse_args()

    main(args.style, args.description, args.chapters, args.genre)

# example usage:
# python gpt_author.py --style "descriptive" --description "A story of love and loss" --chapters 10 --genre "romance"
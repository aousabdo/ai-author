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

#configure OpenAI API
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))    

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

# Example usage
if __name__ == "__main__":
    prompt = "What is the capital of France?"
    generated_text = generate_text(prompt, llm="openai")
    print(f"Generated text: {generated_text}")

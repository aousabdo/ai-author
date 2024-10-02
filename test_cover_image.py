import os
from gpt_author_gemini import create_cover_image

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Test plot for cover image generation
test_plot = "A thrilling science fiction novel about a team of astronauts who discover an ancient alien artifact on Mars. As they unravel its secrets, they trigger a chain of events that could change the fate of humanity."

print("Generating cover image...")
create_cover_image(test_plot, orientation="landscape", quality="hd")
print("Cover image generated and saved as 'cover.png'")
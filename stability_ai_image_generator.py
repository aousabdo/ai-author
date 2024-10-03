import requests
import os

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
    
    
# test
create_cover_image_stability_ai("A thrilling science fiction novel about a team of astronauts who discover an ancient alien artifact on Mars. As they unravel its secrets, they trigger a chain of events that could change the fate of humanity.", orientation="landscape", quality="hd", genre="science fiction")
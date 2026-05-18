from google import genai
from PIL import Image
import json
import os

# Initialize client with API key from environment
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("AI_GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY or AI_GOOGLE_API_KEY environment variable not set")

client = genai.Client(api_key=api_key)

def parse_receipt(image_path):

    image = Image.open(image_path)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "Extract all items from receipt image. "
            "Return JSON array with item, price, category.",
            image
        ]
    )

    return response.text
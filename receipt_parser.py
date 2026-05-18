from google import genai
from PIL import Image
import json

client = genai.Client()

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
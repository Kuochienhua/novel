import google.generativeai as genai
import os
from PIL import Image
import io

api_key = 'AIzaSyDKl4QXACRnPISYSiK_1tIjpdFQw7r1vO0'
genai.configure(api_key=api_key)

try:
    # Use the model found in the list
    model = genai.GenerativeModel('gemini-2.5-flash')
    # Prompting for image generation
    response = model.generate_content("Generate an image of a steampunk clock tower in a Japanese fishing village, watercolor style.")
    
    print("Response parts:", len(response.candidates[0].content.parts))
    for i, part in enumerate(response.candidates[0].content.parts):
        if part.inline_data:
            print(f"Part {i} is image data!")
            img = Image.open(io.BytesIO(part.inline_data.data))
            img.save("test_gemini_image.png")
        else:
            print(f"Part {i} is text: {part.text[:50]}...")
except Exception as e:
    print(f"Error: {e}")

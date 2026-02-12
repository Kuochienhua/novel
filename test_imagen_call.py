import google.generativeai as genai
import os

api_key = 'AIzaSyDKl4QXACRnPISYSiK_1tIjpdFQw7r1vO0'
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('imagen-3.0-generate-001')
    # Trying the standard way for multimodal/generative models
    # Note: Imagen usually returns an image object
    response = model.generate_content("A beautiful watercolor illustration of a steampunk clock tower in a Japanese fishing village.")
    print("Success!")
    # Check if there's an image in the response
    # response.images[0].save("test.png")
except Exception as e:
    print(f"Error: {e}")

import google.generativeai as genai
import os

api_key = 'AIzaSyDKl4QXACRnPISYSiK_1tIjpdFQw7r1vO0'
genai.configure(api_key=api_key)

try:
    # Most common image model name in the preview/beta
    model = genai.GenerativeModel('imagen-3.0-generate-001')
    print("Model found.")
except Exception as e:
    print(f"Error: {e}")

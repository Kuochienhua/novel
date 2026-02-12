import google.generativeai as genai
import os

api_key = 'AIzaSyDKl4QXACRnPISYSiK_1tIjpdFQw7r1vO0'
genai.configure(api_key=api_key)

try:
    # Testing direct call or inspection
    model = genai.GenerativeModel('imagen-4.0-fast-generate-001')
    print("Methods:", dir(model))
except Exception as e:
    print(f"Error: {e}")

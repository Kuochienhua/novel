import google.generativeai as genai
import os

api_key = 'AIzaSyDKl4QXACRnPISYSiK_1tIjpdFQw7r1vO0'
genai.configure(api_key=api_key)

print("Listing all models and their details...")
try:
    for m in genai.list_models():
        print(f"Name: {m.name}")
        print(f"Display Name: {m.display_name}")
        print(f"Supported Methods: {m.supported_generation_methods}")
        print("-" * 30)
except Exception as e:
    print(f"Error: {e}")

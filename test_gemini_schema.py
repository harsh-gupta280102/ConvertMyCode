"""
Quick test script to verify Gemini REST API payload format
"""
import requests
import json

# Test with a dummy key or test payload structure against Gemini API
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyFakeKeyForSchemaTest"
headers = {"Content-Type": "application/json"}

payload_snake = {
    "system_instruction": {
        "parts": [{"text": "Hello"}]
    },
    "contents": [{"parts": [{"text": "Hello"}]}]
}

payload_camel = {
    "systemInstruction": {
        "parts": [{"text": "Hello"}]
    },
    "contents": [{"parts": [{"text": "Hello"}]}]
}

res_snake = requests.post(url, headers=headers, json=payload_snake)
print("SNAKE_CASE response:", res_snake.status_code, res_snake.text[:200])

res_camel = requests.post(url, headers=headers, json=payload_camel)
print("CAMEL_CASE response:", res_camel.status_code, res_camel.text[:200])

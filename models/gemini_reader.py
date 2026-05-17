import google.generativeai as genai
import json
import os
from PIL import Image
import time

def read_bill_gemini(image_path: str, api_key: str) -> dict:

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-2.5-flash")

    image = Image.open(image_path)

    prompt = """
    You are a receipt/bill reading AI. Extract all information from this receipt image.
    
    Return ONLY a valid JSON object with this exact structure, no explanation, no markdown:
    {
        "items": [
            {
                "name": "item name",
                "quantity": 1,
                "price_per_item": 10000,
                "total_price": 10000
            }
        ],
        "subtotal": 100000,
        "additional_charges": [
            {
                "name": "Tax 10%",
                "amount": 10000
            }
        ],
        "total": 110000,
        "currency": "IDR"
    }
    
    Rules:
    - All prices must be numbers (no currency symbols)
    - If quantity is not shown, assume 1
    - If subtotal is not shown, calculate it from items
    - additional_charges includes tax, service charge, discount, etc.
    - Return ONLY the JSON, nothing else
    """

    start_time = time.time()

    response = model.generate_content([prompt, image])

    elapsed_time = time.time() - start_time

    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = "\n".join(raw_text.split("\n")[1:-1])

    bill_data = json.loads(raw_text)

    bill_data["inference_time"] = round(elapsed_time, 2)
    bill_data["model_used"] = "gemini-1.5-flash"

    return bill_data
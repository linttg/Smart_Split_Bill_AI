from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import torch
import json
import time
from PIL import Image

_model = None
_processor = None

def load_qwen_model():

    global _model, _processor

    if _model is None:

        model_name = "Qwen/Qwen2-VL-2B-Instruct"

        _processor = AutoProcessor.from_pretrained(model_name)

        _model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu"
        )

    return _model, _processor


def read_bill_qwen(image_path: str) -> dict:

    model, processor = load_qwen_model()

    image = Image.open(image_path).convert("RGB")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image
                },
                {
                    "type": "text",
                    "text": """Extract receipt data and return ONLY valid JSON:
{
    "items": [{"name": "string", "quantity": 1, "price_per_item": 0, "total_price": 0}],
    "subtotal": 0,
    "additional_charges": [{"name": "string", "amount": 0}],
    "total": 0,
    "currency": "IDR"
}
Return ONLY the JSON, no explanation."""
                }
            ]
        }
    ]

    text_input = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = processor(
        text=[text_input],
        images=[image],
        return_tensors="pt"
    )

    start_time = time.time()

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=512
        )

    elapsed_time = time.time() - start_time

    output_text = processor.decode(output_ids[0], skip_special_tokens=True)

    json_start = output_text.find("{")
    json_end = output_text.rfind("}") + 1

    json_str = output_text[json_start:json_end]

    bill_data = json.loads(json_str)

    bill_data["inference_time"] = round(elapsed_time, 2)
    bill_data["model_used"] = "qwen2-vl-2b-instruct"

    return bill_data
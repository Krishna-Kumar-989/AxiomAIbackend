from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import easyocr
import numpy as np
from PIL import Image
import io
import cv2
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
NEMOTRON_API_KEY = os.getenv("NEMOTRON_API_KEY")

app = Flask(__name__)
CORS(app)

reader = easyocr.Reader(["en"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["image"]
    
    try:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Convert image to OpenCV format
        image = Image.open(file).convert("RGB")
        image_np = np.array(image)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        # Perform OCR
        text_results = reader.readtext(image_bgr, detail=0)
        extracted_text = " ".join(text_results)

        return jsonify({"text": extracted_text, "image_url": f"http://localhost:5000/{filepath}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search-nemotron", methods=["POST"])
def search_nemotron():
    data = request.json
    text = data.get("text")

    if not text:
        return jsonify({"error": "Text is required"}), 400

    headers = {
        "Authorization": f"Bearer {NEMOTRON_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "messages": [{"role": "user", "content": text}],
        "temperature": 0.5,
        "top_p": 1,
        "max_tokens": 1024
    }

    try:
        response = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", json=payload, headers=headers)
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            return jsonify({"response": result["choices"][0]["message"]["content"]})

        return jsonify({"error": "No response from Nemotron"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)

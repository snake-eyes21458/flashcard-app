from flask import Flask, render_template, request, redirect, url_for
import json
import requests
import os

app = Flask(__name__)

FLASHCARD_FILE = 'flashcards.json'

def load_flashcards():
    try:
        with open(FLASHCARD_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_flashcards(cards):
    with open(FLASHCARD_FILE, 'w') as f:
        json.dump(cards, f)

@app.route('/')
def home():
    flashcards = load_flashcards()
    return render_template('index.html', flashcards=flashcards)

@app.route('/add', methods=['POST'])
def add():
    term = request.form['term']
    definition = request.form['definition']
    flashcards = load_flashcards()
    flashcards.append({'term': term, 'definition': definition})
    save_flashcards(flashcards)
    return redirect(url_for('home'))

@app.route('/clear', methods=['POST'])
def clear():
    save_flashcards([])
    return redirect(url_for('home'))

@app.route('/generate', methods=['POST'])
def generate():
    subject = request.form['subject']
    flashcards = generate_flashcards_from_ai(subject)
    save_flashcards(flashcards)
    return redirect(url_for('home'))

import textwrap

import textwrap

def generate_flashcards_from_ai(subject):
    HF_TOKEN = os.getenv("HF_TOKEN")
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}"
    }

    prompt = textwrap.dedent(f"""
        You are an AI flashcard generator. Your job is to output 3 flashcards on the topic "{subject}" in raw JSON format only, like this:
        [
          {{"term": "Example Term", "definition": "Example Definition"}},
          ...
        ]
        DO NOT include any explanation or additional text. ONLY return the JSON array.
    """)

    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

    try:
        json_data = response.json()
        print("DEBUG FULL RESPONSE:", json_data)  # For now, log what we get

        # Handle error responses (e.g., model is loading)
        if isinstance(json_data, dict) and "error" in json_data:
            return [{"term": "Error", "definition": f"Hugging Face API Error: {json_data['error']}"}]

        # Check for expected format
        if isinstance(json_data, list) and "generated_text" in json_data[0]:
            output = json_data[0]["generated_text"]
        else:
            return [{"term": "Error", "definition": "Unexpected API response structure"}]

        # Extract only JSON content
        json_start = output.find("[")
        json_end = output.rfind("]") + 1
        json_str = output[json_start:json_end]

        return json.loads(json_str)

    except Exception as e:
        return [{"term": "Error", "definition": f"Failed to parse response: {str(e)}"}]




if __name__ == '__main__':
    app.run(debug=True)

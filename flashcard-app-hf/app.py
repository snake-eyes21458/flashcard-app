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

def generate_flashcards_from_ai(subject):
    HF_TOKEN = os.getenv("HF_TOKEN")  # <-- Set this on Render
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}"
    }

    prompt = f"""
    Generate 3 flashcards in JSON format for the topic: "{subject}".
    Format:
    [
      {{"term": "Term1", "definition": "Definition1"}},
      ...
    ]
    """

    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

    try:
        output = response.json()[0]["generated_text"]
        return json.loads(output)
    except Exception as e:
        return [{"term": "Error", "definition": f"Failed to parse response: {str(e)}"}]

if __name__ == '__main__':
    app.run(debug=True)

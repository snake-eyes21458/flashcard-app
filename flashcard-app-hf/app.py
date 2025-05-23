from flask import Flask, render_template, request, redirect, url_for
import json
import os
import cohere
import textwrap

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
    term       = request.form['term']
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
    subject    = request.form['subject']
    flashcards = generate_flashcards_from_ai(subject)
    save_flashcards(flashcards)
    return redirect(url_for('home'))

def generate_flashcards_from_ai(subject):
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        return [{"term":"Error","definition":"Missing COHERE_API_KEY"}]

    co = cohere.Client(api_key)

    try:
        # Build prompt via list-of-lines to avoid any indentation issues
        lines = [
            f'Generate 3 educational flashcards about the topic: "{subject}".',
            "Format the response strictly as a JSON list like:",
            "[",
            '  {"term": "Term1", "definition": "Definition1"},',
            "  ...",
            "]",
            "Only return the JSON, nothing else."
        ]
        prompt = "\n".join(lines)

        # Send to Cohere chat
        response = co.chat(
            model="command-r",
            query=prompt,
            temperature=0.6
        )

        # Debug the raw text in your logs
        print("RAW COHERE RESPONSE:", response.text)

        # Extract the JSON array
        output     = response.text
        start_idx  = output.find("[")
        end_idx    = output.rfind("]") + 1
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON brackets found")

        json_str = output[start_idx:end_idx]
        return json.loads(json_str)

    except Exception as e:
        return [{"term": "Error", "definition": f"Failed to generate flashcards: {e}"}]


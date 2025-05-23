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
        return [{"term": "Error", "definition": "Missing COHERE_API_KEY"}]

    co = cohere.Client(api_key)

    # Build a clean, un-indented prompt
    prompt_lines = [
        f'Generate 3 educational flashcards about the topic: "{subject}".',
        "Return ONLY a JSON array, formatted like:",
        "[",
        '  {"term": "Term1", "definition": "Definition1"},',
        "  ...",
        "]",
    ]
    prompt = "\n".join(prompt_lines)

    try:
        # Use a generate model (supported by generate())
        response = co.generate(
            model="command-xlarge-nightly",  # ← this one works with generate()
            prompt=prompt,
            max_tokens=200,
            temperature=0.6,
        )

        # Grab the raw text
        output = response.generations[0].text
        print("RAW COHERE OUTPUT:", output)   # check your logs

        # Extract the JSON substring
        start = output.find("[")
        end   = output.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("Could not find JSON in AI output")

        json_str = output[start:end]
        return json.loads(json_str)

    except Exception as e:
        return [{"term": "Error", "definition": f"Failed to generate flashcards: {e}"}]



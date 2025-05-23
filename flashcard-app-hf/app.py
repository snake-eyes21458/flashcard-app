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

    # Build a simple, un‐indented prompt
    prompt = (
        f'Generate 3 educational flashcards about the topic: "{subject}".\n'
        "Return them _only_ as a JSON array in this format:\n"
        "[\n"
        '  {"term": "Term1", "definition": "Definition1"},\n'
        "  ...\n"
        "]\n"
    )

    try:
        # 1) Pass it in a list under `messages`
        response = co.chat(
            model="command-r",
            messages=[
                {"role": "system", "content": "You are an AI that creates flashcards."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.6
        )

        # 2) Extract the actual text from the first choice
        output = response.choices[0].message.content
        print("RAW COHERE RESPONSE:", output)   # check your logs

        # 3) Slice out the JSON
        start = output.find("[")
        end   = output.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found")

        json_str = output[start:end]
        return json.loads(json_str)

    except Exception as e:
        return [{"term": "Error", "definition": f"Failed to generate flashcards: {e}"}]



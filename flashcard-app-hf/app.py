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
    api_key = os.getenv("COHERE_API_KEY")
    co = cohere.Client(api_key)

    prompt = (
    f"Generate 3 educational flashcards about the topic: \"{subject}\".\n"
    "Format the response strictly as a JSON list like:\n"
    "[\n"
    "  {{\"term\": \"Term1\", \"definition\": \"Definition1\"}},\n"
    "  ...\n"
    "]\n"
    "Only return the JSON, nothing else."
)


    try:
        response = co.generate(
            model="command-r",
            prompt=prompt,
            max_tokens=300,
            temperature=0.6,
        )

        output = response.generations[0].text
        json_start = output.find("[")
        json_end = output.rfind("]") + 1
        json_str = output[json_start:json_end]

        return json.loads(json_str)

    except Exception as e:
        return [{"term": "Error", "definition": f"Failed to generate flashcards: {str(e)}"}]

if __name__ == '__main__':
    app.run(debug=True)

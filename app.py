from flask import Flask, make_response, request, jsonify, redirect, session, url_for
from flask_cors import CORS
import openai
import wikipediaapi
import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document
from PIL import Image
import pytesseract
import io
import pandas as pd
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key')
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Initialize OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Wikipedia API instance with user-agent
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='MyAppName/1.0 (myemail@example.com)'
)

# Path to the client secrets file
CLIENT_SECRETS_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
SCOPES = ['https://www.googleapis.com/auth/calendar']

flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri='http://localhost:5000/api/callback'
)

# Dummy data for bots
def get_bots_from_db():
    # Replace this with actual database access code in the future
    return [
        {
            'id': 1,
            'name': 'Sample Bot 1',
            'base_bot': 'Base Bot 1',
            'prompt': 'Prompt 1',
            'public_access': True,
            'related_bots': False,
            'show_prompt': True,
        },
        {
            'id': 2,
            'name': 'Sample Bot 2',
            'base_bot': 'Base Bot 2',
            'prompt': 'Prompt 2',
            'public_access': False,
            'related_bots': True,
            'show_prompt': False,
        }
    ]

@app.route('/api/authorize')
def authorize():
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/api/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session['state'] == request.args['state']:
        return jsonify({'error': 'State mismatch'}), 500

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('index'))

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_calendar_service():
    if 'credentials' not in session:
        return None
    credentials = Credentials(**session['credentials'])
    return build('calendar', 'v3', credentials=credentials)

@app.route('/api/create-event', methods=['POST'])
def create_event():
    calendar_service = get_calendar_service()
    if calendar_service is None:
        return redirect(url_for('authorize'))

    try:
        data = request.json
        workflow = data['workflow']
        start_time = data['start_time']
        end_time = data['end_time']
        event = {
            'summary': 'Skill Daily Workflow',
            'description': workflow,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        event = calendar_service.events().insert(calendarId='primary', body=event).execute()
        session['credentials'] = credentials_to_dict(calendar_service._credentials)  # Save the credentials again
        return jsonify({'event': event}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-bot', methods=['POST'])
def create_bot():
    try:
        form_data = request.form
        name = form_data['name']
        base_bot = form_data['base_bot']
        prompt = form_data['prompt']
        public_access = form_data.get('public_access') == 'true'
        related_bots = form_data.get('related_bots') == 'true'
        show_prompt = form_data.get('show_prompt') == 'true'

        knowledge_base_files = request.files.getlist('knowledge_base')
        knowledge_base = []
        for file in knowledge_base_files:
            knowledge_base.append(file.read())  # Read file content

        # Here you would normally save the bot to your database
        # For demonstration, we are returning the bot details as a response
        new_bot = {
            'name': name,
            'base_bot': base_bot,
            'prompt': prompt,
            'public_access': public_access,
            'related_bots': related_bots,
            'show_prompt': show_prompt,
            'knowledge_base': knowledge_base
        }

        return jsonify({'bot': new_bot, 'message': 'Bot created successfully!'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/my-bots', methods=['GET'])
def get_my_bots():
    try:
        my_bots = get_bots_from_db()
        return jsonify({'bots': my_bots}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/retrieve-content', methods=['POST'])
def retrieve_content():
    try:
        data = request.json
        subtopic = data.get('subtopic', '')
        page = wiki_wiki.page(subtopic)
        if page.exists():
            summary = page.summary
            return jsonify({'content': summary})
        else:
            return jsonify({'error': 'Subtopic not found on Wikipedia'}), 404
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/summarize', methods=['POST'])
def summarize():
    data = request.json
    text = data['text']
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Summarize the following text:\n\n{text}",
        max_tokens=50
    )
    return jsonify({'summary': response.choices[0].text.strip()})

@app.route('/api/highlight', methods=['POST'])
def highlight():
    data = request.json
    text = data['text']
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Highlight the key points in the following text:\n\n{text}",
        max_tokens=50
    )
    return jsonify({'highlights': response.choices[0].text.strip().split('\n')})

@app.route('/api/sentiment-analysis', methods=['POST'])
def sentiment_analysis():
    data = request.json
    text = data['text']
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Perform a sentiment analysis on the following text:\n\n{text}",
        max_tokens=50
    )
    return jsonify({'sentiment': response.choices[0].text.strip()})

@app.route('/api/automate-task', methods=['POST'])
def automate_task():
    data = request.json
    task = data['task']
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Automate the following task step-by-step:\n\n{task}",
        max_tokens=150
    )
    return jsonify({'automated_steps': response.choices[0].text.strip().split('\n')})

@app.route('/api/generate-topics', methods=['POST', 'OPTIONS'])
def generate_topics():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
        topic = data.get('topic', '')
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Generate topics related to: {topic}",
            max_tokens=100
        )
        generated_topics = response.choices[0].text.strip().split('\n')
        return jsonify({'topics': generated_topics}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-subtopics', methods=['POST'])
def generate_subtopics():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
        topic = data.get('topic', '')
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Generate a list of subtopics for the topic: {topic}",
            max_tokens=150
        )
        subtopics = response.choices[0].text.strip().split('\n')
        return jsonify({'subtopics': subtopics}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-modules', methods=['POST'])
def generate_modules():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
        subtopic = data.get('subtopic', '')
        num_modules = data.get('num_modules', 1)
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Generate {num_modules} modules for the subtopic: {subtopic}",
            max_tokens=150
        )
        modules = response.choices[0].text.strip().split('\n')
        return jsonify({'modules': modules}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-overview', methods=['POST'])
def generate_overview():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
        modules = data.get('modules', [])
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Generate an overview for the following modules: {modules}",
            max_tokens=150
        )
        overview = response.choices[0].text.strip()
        return jsonify({'overview': overview}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
        modules = data.get('modules', [])
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Generate quiz questions for the following modules: {modules}",
            max_tokens=150
        )
        quiz_questions = response.choices[0].text.strip().split('\n')
        return jsonify({'questions': quiz_questions}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    data = request.json
    query = data['query']
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Answer the following query:\n\n{query}",
        max_tokens=150
    )
    response_text = response.choices[0].text.strip()
    return jsonify({'response': response_text})

@app.route('/api/generate-workflow', methods=['POST'])
def generate_workflow():
    try:
        data = request.json
        text = data['text']
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"Generate a daily workflow for the following task:\n\n{text}",
            max_tokens=200
        )
        workflow = response.choices[0].text.strip()
        return jsonify({'workflow': workflow}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule-workflow', methods=['POST'])
def schedule_workflow():
    calendar_service = get_calendar_service()
    if calendar_service is None:
        return redirect(url_for('authorize'))

    try:
        data = request.json
        workflow = data['workflow']
        start_time = data['start_time']
        end_time = data['end_time']
        event = {
            'summary': 'Skill Daily Workflow',
            'description': workflow,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        event = calendar_service.events().insert(calendarId='primary', body=event).execute()
        session['credentials'] = credentials_to_dict(calendar_service._credentials)  # Save the credentials again
        return jsonify({'event': event}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        file_type = file.content_type

        if 'pdf' in file_type:
            text = extract_pdf_text(io.BytesIO(file.read()))
        elif 'word' in file_type or 'officedocument' in file_type:
            doc = Document(io.BytesIO(file.read()))
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif 'image' in file_type:
            image = Image.open(io.BytesIO(file.read()))
            text = pytesseract.image_to_string(image)
        elif 'text' in file_type:
            text = file.read().decode('utf-8')
        elif 'excel' in file_type:
            df = pd.read_excel(file)
            text = df.to_string()
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        return jsonify({'text': text}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return 'Welcome to the Google Calendar API integration!'

if __name__ == '__main__':
    app.run(debug=True, port=5000)

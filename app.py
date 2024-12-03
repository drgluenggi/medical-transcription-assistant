from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from openai import OpenAI
from dotenv import load_dotenv
import tempfile
import time
import json
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Load databases
with open('medications_db.json', 'r') as f:
    MEDICATIONS_DB = json.load(f)

with open('patient_db.json', 'r') as f:
    PATIENT_DB = json.load(f)

with open('prescription_template.html', 'r') as f:
    PRESCRIPTION_TEMPLATE = f.read()

def extract_patient_name(text):
    """Extract patient's last name using GPT."""
    try:
        name_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract only the patient's last name from the text. Respond with ONLY the last name, nothing else. If no patient name is found, respond with 'NONE'."},
                {"role": "user", "content": text}
            ],
            temperature=0
        )
        
        last_name = name_response.choices[0].message.content.strip()
        return None if last_name == 'NONE' else last_name
        
    except Exception as e:
        app.logger.error(f"Error extracting patient name: {str(e)}")
        return None

def find_patient_by_last_name(last_name):
    """Find patient in database by last name."""
    if not last_name:
        return None
        
    for patient in PATIENT_DB['patients']:
        if patient['last_name'].lower() == last_name.lower():
            return patient
    return None

def analyze_transcript_for_medications(text):
    """Analyze transcription for medication mentions and add recommendations."""
    enhanced_text = text
    medications_found = []
    
    for med_name, med_info in MEDICATIONS_DB['medications'].items():
        # Check for medication name or brand names
        search_terms = [med_name] + med_info['brand_names']
        for term in search_terms:
            if term.lower() in text.lower():
                medications_found.append({
                    'name': med_name,
                    'info': med_info
                })
                break
    
    if medications_found:
        enhanced_text += "\n\nMEDICATION RECOMMENDATIONS:\n"
        for med in medications_found:
            enhanced_text += f"\n{med['name'].upper()}:\n"
            enhanced_text += f"- Timing: {med['info']['timing_recommendations']['meal_relation']}\n"
            enhanced_text += f"- Foods to Avoid: {med['info']['timing_recommendations']['foods_to_avoid']}\n"
            enhanced_text += f"- Maximum Daily Dose: {med['info']['max_daily_dose']}\n"
            enhanced_text += "- Warnings:\n  * " + "\n  * ".join(med['info']['warnings']) + "\n"
    
    return enhanced_text, medications_found

def generate_prescription(medication_info, patient_info):
    """Generate a prescription HTML document."""
    prescription_data = {
        'patient_name': f"{patient_info['first_name']} {patient_info['last_name']}",
        'patient_dob': datetime.strptime(patient_info['dob'], '%Y-%m-%d').strftime('%m/%d/%Y'),
        'medical_record_number': patient_info['mrn'],
        'current_date': datetime.now().strftime('%m/%d/%Y'),
        'medication_name': medication_info['name'].title(),
        'dosage': medication_info['info']['typical_dosages'][0],
        'instructions': medication_info['info']['frequency'],
        'quantity': '30',
        'refills': '0',
        'special_instructions': (
            f"{medication_info['info']['timing_recommendations']['meal_relation']}\n"
            f"Patient allergies: {', '.join(patient_info['allergies']) if patient_info['allergies'] else 'None reported'}"
        )
    }

    # Replace template variables
    prescription_html = PRESCRIPTION_TEMPLATE
    for key, value in prescription_data.items():
        prescription_html = prescription_html.replace('{{' + key + '}}', str(value))

    return prescription_html


@app.route('/get_patient_info', methods=['POST'])
def get_patient_info():
    data = request.json
    last_name = data.get('last_name')
    
    if not last_name:
        return jsonify(None)
        
    patient = find_patient_by_last_name(last_name)
    return jsonify(patient)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    temp_file_path = None
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        
        # Generate a unique temporary file path
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f'audio_{int(time.time())}.webm')
        
        # Save the file
        audio_file.save(temp_file_path)
        
        # Process the audio file
        with open(temp_file_path, 'rb') as audio:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="text"
            )

        # Format using ChatGPT
        formatted_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Format the following transcription text appropriately with proper punctuation and paragraphing."},
                {"role": "user", "content": transcript}
            ]
        )

        formatted_text = formatted_response.choices[0].message.content

        # Extract patient name and find in database
        patient_last_name = extract_patient_name(formatted_text)
        patient = find_patient_by_last_name(patient_last_name)
        
        # Analyze for medications and generate recommendations
        enhanced_text, medications_found = analyze_transcript_for_medications(formatted_text)
        
        if patient:
            enhanced_text = f"Patient: {patient['first_name']} {patient['last_name']} (MRN: {patient['mrn']})\n\n" + enhanced_text
        
        response_data = {
            'transcription': enhanced_text,
            'prescriptions': [],
            'patient_found': bool(patient)
        }

        # Generate prescriptions for found medications
        if medications_found and patient:
            for med in medications_found:
                prescription_html = generate_prescription(med, patient)
                response_data['prescriptions'].append({
                    'medication': med['name'],
                    'html': prescription_html
                })
        elif medications_found:
            response_data['message'] = "Medications found but no patient identified in transcription."
        
        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error processing audio: {str(e)}")
        return jsonify({'error': 'Error processing audio'}), 500

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                app.logger.error(f"Error removing temporary file: {str(e)}")
                pass

if __name__ == '__main__':
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    app.run(debug=True)
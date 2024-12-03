# Medical Transcription Assistant

A web-based application that transcribes medical consultations, identifies medications, and automatically generates prescription documents. Built with Flask and OpenAI's APIs, this tool helps healthcare providers streamline their documentation process.

## Features

- 🎤 Real-time audio transcription using OpenAI's Whisper API
- 🤖 Intelligent text processing with GPT-4
- 💊 Automatic medication identification and recommendation generation
- 📝 Automated prescription document generation
- 🔍 Patient database integration
- ⚡ Real-time patient information lookup

## Technology Stack

- **Backend:** Python, Flask
- **AI/ML:** OpenAI APIs (GPT-4, Whisper)
- **Frontend:** HTML, JavaScript
- **Data Storage:** JSON-based database
- **Environment Management:** python-dotenv

## Prerequisites

- Python 3.8+
- OpenAI API key
- Modern web browser with audio recording capabilities

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/medical-transcription-assistant.git
cd medical-transcription-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`
3. Start recording your medical consultation
4. The application will:
   - Transcribe the audio
   - Identify patient information
   - Detect mentioned medications
   - Generate relevant recommendations
   - Create prescription documents if applicable

## Project Structure

```
medical-transcription-assistant/
├── app.py                     # Main Flask application
├── medications_db.json        # Medication database
├── patient_db.json           # Patient records database
├── prescription_template.html # HTML template for prescriptions
├── static/                   # Static files (CSS, JS, images)
├── templates/                # HTML templates
└── requirements.txt          # Python dependencies
```

## Security Considerations

This application handles sensitive medical information. For production use, please ensure:

- Proper authentication and authorization
- HIPAA compliance measures
- Secure storage of patient data
- Encrypted data transmission
- Regular security audits

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is intended to assist medical professionals and should not be used as a replacement for professional medical judgment. Always verify generated prescriptions and recommendations before use.
from flask import Flask, request, jsonify, send_from_directory
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configure the generative AI model
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not found.")
        model = None
    else:
        print("Successfully loaded GOOGLE_API_KEY.")
        genai.configure(api_key=api_key)
        # Using a specific, stable model version
        model = genai.GenerativeModel('gemini-1.0-pro')
except Exception as e:
    print(f"Error configuring Generative AI: {e}")
    model = None

def extract_video_id(url):
    """Extracts the YouTube video ID from a URL."""
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    return match.group(1) if match else None

def generate_summary_from_ai(transcript):
    """Generates a structured summary using the Google AI model."""
    if not model:
        raise Exception("Generative AI model not configured.")

    prompt = f"""
    You are an expert analyst for startup founders. Analyze the following video transcript and provide a structured summary.

    Transcript:
    "{transcript}"

    Based on the transcript, provide the following in a JSON format:
    1.  "summary": A concise, easy-to-read summary of the video's content.
    2.  "lessons": An array of the most important, actionable lessons from the video.
    3.  "relevance": A paragraph explaining why these lessons are specifically relevant to a startup founder.
    4.  "learn": An array of key topics, skills, or concepts mentioned that the founder should focus on learning.

    Your response must be a valid JSON object.
    """
    
    response = model.generate_content(prompt)
    raw_text = response.text
    print("--- RAW AI RESPONSE ---")
    print(raw_text)
    print("-----------------------")
    
    try:
        # Clean up the response to ensure it's valid JSON
        cleaned_response_text = raw_text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_response_text)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print("Failed to parse the AI's response as JSON.")
        raise Exception("The AI returned an invalid response format.")

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/summarize', methods=['POST'])
def summarize_video():
    """
    API endpoint to receive a YouTube URL, fetch the transcript,
    and return an AI-generated summary.
    """
    data = request.get_json()
    youtube_url = data.get('url')

    if not youtube_url:
        return jsonify({'error': 'URL is required'}), 400

    video_id = extract_video_id(youtube_url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    try:
        print(f"Fetching transcript for video ID: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([item['text'] for item in transcript_list])
        print("Transcript fetched successfully. Sending to AI model...")

        # Generate summary using the AI model
        ai_response = generate_summary_from_ai(transcript_text)
        print("AI response received.")
        
        return jsonify(ai_response)

    except Exception as e:
        print(f"An error occurred: {e}") # Log the full error to the terminal
        return jsonify({'error': str(e)}), 500

# This block is for local development only
if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5001, threads=1)
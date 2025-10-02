from flask import Flask, request, render_template, redirect, url_for, flash, send_file, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
import threading
import time

# Try to import processing modules, fallback to demo mode if not available
try:
    from utils.video_processor import VideoProcessor
    from utils.transcriber import Transcriber
    from utils.translator import Translator
    from utils.subtitle_generator import SubtitleGenerator
    FULL_PROCESSING = True
    print("All dependencies loaded. Full processing mode enabled.")
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Running in demo mode. Install requirements.txt for full functionality.")
    FULL_PROCESSING = False

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Create directories
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/processed', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('utils', exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}

# Global dict to track processing status
processing_status = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)

    file = request.files['file']
    source_language = request.form.get('source_language', 'auto')

    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        file_extension = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{unique_id}.{file_extension}"

        filepath = os.path.join('static/uploads', new_filename)
        file.save(filepath)

        # Initialize processing status
        processing_status[unique_id] = {
            'status': 'uploaded',
            'progress': 0,
            'message': 'File uploaded successfully',
            'original_filename': filename,
            'source_language': source_language
        }

        # Start processing in background
        if FULL_PROCESSING:
            thread = threading.Thread(target=process_video, args=(unique_id, filepath, source_language))
        else:
            thread = threading.Thread(target=process_video_demo, args=(unique_id, filepath, source_language))
        thread.daemon = True
        thread.start()

        return redirect(url_for('processing', task_id=unique_id))
    else:
        flash('Invalid file format. Please upload a video file.')
        return redirect(url_for('index'))

@app.route('/processing/<task_id>')
def processing(task_id):
    return render_template('processing.html', task_id=task_id)

@app.route('/status/<task_id>')
def status(task_id):
    return jsonify(processing_status.get(task_id, {'status': 'not_found'}))

@app.route('/download/<task_id>')
def download(task_id):
    if task_id in processing_status and processing_status[task_id]['status'] == 'completed':
        output_path = processing_status[task_id]['output_path']
        original_filename = processing_status[task_id]['original_filename']

        # Create zip file with video + subtitle
        import zipfile
        name_without_ext = os.path.splitext(original_filename)[0]
        zip_filename = f"{name_without_ext}_with_subtitles.zip"
        zip_path = os.path.join('static/processed', zip_filename)

        # Get paths for video and subtitle
        srt_path = output_path.replace('.mp4', '.srt')

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add video file
            video_name = f"{name_without_ext}_translated.mp4"
            zipf.write(output_path, video_name)

            # Add subtitle file if exists
            if os.path.exists(srt_path):
                subtitle_name = f"{name_without_ext}_translated.srt"
                zipf.write(srt_path, subtitle_name)

            # Add instructions
            instructions = """How to use the subtitles:

1. VLC Player (Recommended):
   - Open the video file in VLC Player
   - Go to Subtitle > Add Subtitle File
   - Select the .srt file
   - Subtitles will appear automatically!

2. Other Video Players:
   - Most video players support SRT files
   - Make sure the video and SRT file have the same name
   - Place them in the same folder

3. Video Editors:
   - Import both video and SRT file
   - The subtitles will be automatically synchronized

Your video now has English subtitles for every spoken word!
"""
            zipf.writestr("README_How_to_use_subtitles.txt", instructions)

        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
    else:
        flash('File not ready for download')
        return redirect(url_for('index'))

def process_video(task_id, filepath, source_language):
    """Full video processing with speech recognition and translation"""
    try:
        # Update status
        processing_status[task_id]['status'] = 'processing'
        processing_status[task_id]['progress'] = 10
        processing_status[task_id]['message'] = 'Extracting audio...'

        # Initialize processors
        video_processor = VideoProcessor()
        transcriber = Transcriber()
        translator = Translator()
        subtitle_generator = SubtitleGenerator()

        # Extract audio
        try:
            audio_path = video_processor.extract_audio(filepath)
            print(f"Audio extracted to: {audio_path}")
            processing_status[task_id]['progress'] = 30
            processing_status[task_id]['message'] = 'Transcribing speech...'
        except Exception as audio_error:
            print(f"Audio extraction error: {audio_error}")
            raise Exception(f"Failed to extract audio: {audio_error}")

        # Transcribe audio
        try:
            transcription = transcriber.transcribe(audio_path, source_language)
            print(f"Transcription completed with {len(transcription)} segments")
        except Exception as transcribe_error:
            print(f"Transcription error: {transcribe_error}")
            # Clean up audio file on error
            if os.path.exists(audio_path):
                os.remove(audio_path)
            raise Exception(f"Failed to transcribe audio: {transcribe_error}")
        processing_status[task_id]['progress'] = 60
        processing_status[task_id]['message'] = 'Translating to English...'

        # Translate to English
        translated_segments = translator.translate_segments(transcription)
        processing_status[task_id]['progress'] = 75
        processing_status[task_id]['message'] = 'Optimizing subtitle timing...'

        # Optimize subtitle timing for better audio-video sync
        optimized_segments = subtitle_generator.merge_short_segments(translated_segments)
        optimized_segments = subtitle_generator.split_long_segments(optimized_segments)

        processing_status[task_id]['progress'] = 80
        processing_status[task_id]['message'] = 'Generating subtitles...'

        # Generate subtitle file with optimized timing
        srt_path = subtitle_generator.create_srt(optimized_segments, task_id)
        processing_status[task_id]['progress'] = 90
        processing_status[task_id]['message'] = 'Adding subtitles to video...'

        # Add subtitles to video
        output_path = video_processor.add_subtitles(filepath, srt_path, task_id)

        # Cleanup temporary files
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(filepath):
            os.remove(filepath)

        processing_status[task_id]['status'] = 'completed'
        processing_status[task_id]['progress'] = 100
        processing_status[task_id]['message'] = 'Video processing completed! Download includes video + SRT subtitle file.'
        processing_status[task_id]['output_path'] = output_path
        processing_status[task_id]['subtitle_info'] = 'Subtitles are provided as separate SRT file. Open video in VLC Player and load the SRT file for subtitles.'

    except Exception as e:
        processing_status[task_id]['status'] = 'error'
        processing_status[task_id]['message'] = f'Error: {str(e)}'
        print(f"Error processing video {task_id}: {str(e)}")

def process_video_demo(task_id, filepath, source_language):
    """Demo version - simulates processing and creates sample subtitle"""
    try:
        # Update status - simulating processing steps
        processing_status[task_id]['status'] = 'processing'
        processing_status[task_id]['progress'] = 10
        processing_status[task_id]['message'] = 'Extracting audio...'
        time.sleep(2)

        processing_status[task_id]['progress'] = 30
        processing_status[task_id]['message'] = 'Transcribing speech...'
        time.sleep(3)

        processing_status[task_id]['progress'] = 60
        processing_status[task_id]['message'] = 'Translating to English...'
        time.sleep(2)

        processing_status[task_id]['progress'] = 80
        processing_status[task_id]['message'] = 'Generating subtitles...'
        time.sleep(1)

        # Create sample subtitle file
        srt_content = """1
00:00:01,000 --> 00:00:05,000
Welcome to the video translation demo

2
00:00:05,000 --> 00:00:10,000
This is a sample subtitle in English

3
00:00:10,000 --> 00:00:15,000
Your video processing is complete!

"""
        srt_path = os.path.join('static/processed', f'subtitles_{task_id}.srt')
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        processing_status[task_id]['progress'] = 90
        processing_status[task_id]['message'] = 'Adding subtitles to video...'
        time.sleep(2)

        # For demo, just copy the original file
        output_filename = f"translated_{task_id}.mp4"
        output_path = os.path.join('static/processed', output_filename)

        # Copy original file to processed folder
        import shutil
        shutil.copy2(filepath, output_path)

        # Cleanup upload file
        if os.path.exists(filepath):
            os.remove(filepath)

        processing_status[task_id]['status'] = 'completed'
        processing_status[task_id]['progress'] = 100
        processing_status[task_id]['message'] = 'Video processing completed!'
        processing_status[task_id]['output_path'] = output_path

    except Exception as e:
        processing_status[task_id]['status'] = 'error'
        processing_status[task_id]['message'] = f'Error: {str(e)}'
        print(f"Error processing video {task_id}: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
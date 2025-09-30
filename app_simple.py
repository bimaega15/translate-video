from flask import Flask, request, render_template, redirect, url_for, flash, send_file, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Create directories
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/processed', exist_ok=True)

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

        # Start processing in background (demo version)
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

        # Clean filename for download
        name_without_ext = os.path.splitext(original_filename)[0]
        download_filename = f"{name_without_ext}_translated.mp4"

        return send_file(output_path, as_attachment=True, download_name=download_filename)
    else:
        flash('File not ready for download')
        return redirect(url_for('index'))

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
    print("Starting Video Translation Demo App...")
    print("Open your browser and go to: http://localhost:5000")
    print("Note: This is a demo version. Install dependencies for full functionality.")
    app.run(debug=True, host='0.0.0.0', port=5000)
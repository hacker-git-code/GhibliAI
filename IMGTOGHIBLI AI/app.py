import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
import threading
import time

from ghibli_transformer import GhibliTransformer

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'}

# Ensure upload and result directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# Initialize the transformer
transformer = GhibliTransformer()

# Track processing status
processing_tasks = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate a unique ID for this task
    task_id = str(uuid.uuid4())
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
    file.save(file_path)
    
    # Determine if it's an image or video
    file_ext = os.path.splitext(filename)[1].lower()
    is_video = file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    # Get transformation settings
    strength = float(request.form.get('strength', 0.7))
    steps = int(request.form.get('steps', 20))
    
    # Set up the result path
    result_filename = f"{task_id}_ghibli{file_ext}"
    result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
    
    # Update task status
    processing_tasks[task_id] = {
        'status': 'processing',
        'progress': 0,
        'original_filename': filename,
        'result_filename': result_filename,
        'start_time': time.time(),
        'is_video': is_video
    }
    
    # Process in background thread
    def process_file():
        try:
            if is_video:
                transformer.transform_video(
                    file_path, 
                    result_path,
                    progress_callback=lambda p: update_progress(task_id, p)
                )
            else:
                transformer.transform_image(file_path, result_path, strength=strength, steps=steps)
                update_progress(task_id, 100)
            
            processing_tasks[task_id]['status'] = 'completed'
            processing_tasks[task_id]['end_time'] = time.time()
            processing_tasks[task_id]['processing_time'] = processing_tasks[task_id]['end_time'] - processing_tasks[task_id]['start_time']
            
            # Clean up original file to save space
            if os.path.exists(file_path):
                os.remove(file_path)
                
        except Exception as e:
            processing_tasks[task_id]['status'] = 'failed'
            processing_tasks[task_id]['error'] = str(e)
    
    threading.Thread(target=process_file).start()
    
    return jsonify({
        'task_id': task_id,
        'message': 'File uploaded and processing started',
        'is_video': is_video
    })

def update_progress(task_id, progress):
    if task_id in processing_tasks:
        processing_tasks[task_id]['progress'] = progress

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if task_id not in processing_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = processing_tasks[task_id]
    response = {
        'status': task['status'],
        'progress': task['progress'],
        'original_filename': task['original_filename'],
        'result_filename': task['result_filename'],
        'is_video': task.get('is_video', False)
    }
    
    if task['status'] == 'completed':
        response['result_url'] = url_for('get_result', filename=task['result_filename'])
        if 'processing_time' in task:
            response['processing_time'] = task['processing_time']
    
    if task['status'] == 'failed' and 'error' in task:
        response['error'] = task['error']
    
    return jsonify(response)

@app.route('/result/<filename>')
def get_result(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/cleanup', methods=['POST'])
def cleanup_old_tasks():
    """Clean up old tasks and files to free up disk space"""
    current_time = time.time()
    cleanup_age = 3600  # 1 hour
    
    for task_id in list(processing_tasks.keys()):
        task = processing_tasks[task_id]
        
        # Skip tasks that are still processing
        if task['status'] == 'processing':
            continue
            
        # Check if task is old enough to clean up
        if 'end_time' in task and (current_time - task['end_time']) > cleanup_age:
            # Remove result file
            result_path = os.path.join(app.config['RESULT_FOLDER'], task['result_filename'])
            if os.path.exists(result_path):
                os.remove(result_path)
                
            # Remove task from dictionary
            del processing_tasks[task_id]
    
    return jsonify({'status': 'cleanup completed'})

if __name__ == '__main__':
    print("Starting GhibliAI server...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)

"""
Basic GhibliAI Application
A streamlined version of the GhibliAI tool
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
import torch
from PIL import Image
from diffusers import StableDiffusionPipeline
import numpy as np

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload and result directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# Global variable to track if model is loaded
model_loaded = False
pipe = None

def load_model():
    """Load the Stable Diffusion model."""
    global pipe, model_loaded
    
    if model_loaded:
        return
    
    print("Loading model (this may take a moment)...")
    
    # Use CPU for compatibility
    device = "cpu"
    print(f"Using device: {device}")
    
    # Load a smaller model for faster loading
    model_id = "CompVis/stable-diffusion-v1-4"
    
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        safety_checker=None
    )
    pipe = pipe.to(device)
    
    model_loaded = True
    print("Model loaded successfully!")

@app.route('/')
def index():
    return render_template('basic.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Generate a unique ID for this task
    task_id = str(uuid.uuid4())
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{task_id}_{filename}")
    file.save(file_path)
    
    # Only process images
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        return jsonify({'error': 'Only image files are supported'}), 400
    
    # Set up the result path
    result_filename = f"{task_id}_ghibli{file_ext}"
    result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
    
    # Process the image (simplified version)
    try:
        # Load the model if not already loaded
        if not model_loaded:
            load_model()
        
        # Load the image
        init_image = Image.open(file_path).convert("RGB")
        init_image = init_image.resize((512, 512))
        
        # Save a dummy result for testing (in a real app, we'd use the model)
        # This is just to test the workflow without waiting for model download
        init_image.save(result_path)
        
        return jsonify({
            'success': True,
            'message': 'Image processed successfully',
            'result_url': url_for('get_result', filename=result_filename)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/result/<filename>')
def get_result(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("Starting Basic GhibliAI server...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)

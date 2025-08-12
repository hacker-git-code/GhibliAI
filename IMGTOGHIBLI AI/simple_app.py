"""
Simple GhibliAI Application
A simplified version of the GhibliAI tool for testing
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'results'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('simple.html')

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("Starting Simple GhibliAI server...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)

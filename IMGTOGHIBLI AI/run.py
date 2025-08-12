"""
GhibliAI Runner Script
This script provides a simple way to run the GhibliAI application.
"""

import os
import sys
import webbrowser
from time import sleep

def check_dependencies():
    """Check if all dependencies are installed."""
    try:
        import torch
        import flask
        import diffusers
        import transformers
        import moviepy
        print("All required dependencies are installed.")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Installing dependencies...")
        os.system("pip install -r requirements.txt")
        print("Please restart the application after installation.")
        return False

def main():
    """Main entry point for the application."""
    print("=" * 50)
    print("Welcome to GhibliAI - Studio Ghibli Style Transformer")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    # Import app after dependencies check
    from app import app
    
    # Start the server
    port = 5000
    print(f"\nStarting GhibliAI server on port {port}...")
    print(f"Open your browser to: http://localhost:{port}")
    
    # Open browser automatically
    webbrowser.open(f"http://localhost:{port}")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()

# GhibliAI - Image and Video Transformation Tool

GhibliAI is a powerful tool that transforms your images and videos into the iconic Studio Ghibli art style using advanced AI techniques. This project uses a fine-tuned diffusion model to achieve high-quality Ghibli-style transformations.

## Features

- Transform images into Studio Ghibli art style
- Transform videos into Studio Ghibli art style (frame by frame)
- Simple and intuitive web interface
- High-quality transformations
- Fast processing with GPU acceleration (when available)

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Download the model weights (will be done automatically on first run)

## Usage

1. Start the web server:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`
3. Upload an image or video
4. Click "Transform" and wait for the magic to happen!

## Technical Details

GhibliAI uses a fine-tuned Stable Diffusion model that has been specifically trained to generate Studio Ghibli style art. The model preserves the content and composition of the original image while applying the distinctive Ghibli aesthetic.

For videos, the tool processes each frame individually while maintaining temporal consistency.

## License

MIT License

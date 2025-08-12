import os
import torch
from PIL import Image
import numpy as np
from tqdm import tqdm
import cv2
from diffusers import StableDiffusionImg2ImgPipeline, DPMSolverMultistepScheduler
import moviepy.editor as mp
from huggingface_hub import hf_hub_download
import time

class GhibliTransformer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load models on first use
        self.image_pipe = None
        
        # Model initialization is deferred until first use to save memory
        
    def _ensure_models_loaded(self):
        """Ensures all required models are loaded."""
        if self.image_pipe is None:
            print("Loading models (this may take a moment on first run)...")
            
            # Load the Stable Diffusion img2img pipeline with Ghibli fine-tuning
            # We'll use a model fine-tuned for Ghibli style
            self.image_pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                "nitrosocke/Ghibli-Diffusion", 
                safety_checker=None,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            # Use faster scheduler
            self.image_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.image_pipe.scheduler.config,
                algorithm_type="dpmsolver++",
                solver_order=2
            )
            
            # Move to device and optimize
            self.image_pipe.to(self.device)
            if self.device == "cuda":
                self.image_pipe.enable_xformers_memory_efficient_attention()
                self.image_pipe.enable_model_cpu_offload()
            
            print("Models loaded successfully!")
    
    def transform_image(self, input_path, output_path, strength=0.7, steps=20):
        """Transform a single image to Ghibli style with optimized settings."""
        self._ensure_models_loaded()
        
        # Load the image
        init_image = Image.open(input_path).convert("RGB")
        
        # Resize to optimal size for faster processing
        width, height = init_image.size
        max_size = 768
        
        if width > height:
            if width > max_size:
                new_width = max_size
                new_height = int(height * (max_size / width))
        else:
            if height > max_size:
                new_height = max_size
                new_width = int(width * (max_size / height))
            else:
                new_width, new_height = width, height
                
        if width != new_width or height != new_height:
            init_image = init_image.resize((new_width, new_height))
        
        # Generate Ghibli-style image with optimized parameters
        prompt = "studio ghibli style, ghibli anime style, hayao miyazaki style, detailed, vibrant colors"
        negative_prompt = "low quality, bad anatomy, worst quality, low resolution, blurry"
        
        # Use fewer steps for faster generation
        result = self.image_pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=init_image,
            strength=strength,  # Lower strength = faster processing and more preservation of original
            num_inference_steps=steps,  # Fewer steps = faster processing
            guidance_scale=7.0,
        ).images[0]
        
        # Save the result
        result.save(output_path)
        return output_path
    
    def transform_video(self, input_path, output_path, fps=None, progress_callback=None):
        """Transform a video to Ghibli style frame by frame with optimized settings."""
        self._ensure_models_loaded()
        
        # Load the video
        video = mp.VideoFileClip(input_path)
        if fps is None:
            fps = min(video.fps, 24)  # Cap at 24fps for faster processing
        
        # Create a temporary directory for frames
        temp_dir = "temp_frames"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Calculate frame interval (process every nth frame for speed)
        duration = video.duration
        total_frames = int(duration * fps)
        
        # For longer videos, process fewer frames
        if total_frames > 300:  # More than 10 seconds at 30fps
            frame_interval = max(1, int(total_frames / 300))
            print(f"Processing every {frame_interval}th frame for speed")
        else:
            frame_interval = 1
        
        # Extract frames
        frames = []
        frame_times = []
        
        for i, time_point in enumerate(np.arange(0, duration, 1/fps)):
            if i % frame_interval == 0:
                frame_path = os.path.join(temp_dir, f"frame_{i:04d}.jpg")
                video.save_frame(frame_path, t=time_point)
                frames.append(frame_path)
                frame_times.append(time_point)
                
                if progress_callback:
                    # Report 40% progress for extraction phase
                    progress_callback(int(40 * (i + 1) / total_frames))
        
        # Transform each frame with optimized settings
        transformed_frames = []
        for i, frame_path in enumerate(tqdm(frames, desc="Transforming frames")):
            output_frame_path = os.path.join(temp_dir, f"ghibli_frame_{i:04d}.jpg")
            self.transform_image(frame_path, output_frame_path, strength=0.65, steps=15)
            transformed_frames.append(output_frame_path)
            
            if progress_callback:
                # Report 40-90% progress for transformation phase
                progress_callback(40 + int(50 * (i + 1) / len(frames)))
        
        # Create video from transformed frames
        clips = []
        for i, (frame_path, time_point) in enumerate(zip(transformed_frames, frame_times)):
            # Create a clip for each frame with the correct duration
            if i < len(frame_times) - 1:
                duration = frame_times[i+1] - time_point
            else:
                duration = 1/fps
                
            clip = mp.ImageClip(frame_path).set_duration(duration)
            clips.append(clip)
        
        # Concatenate clips
        concat_clip = mp.concatenate_videoclips(clips, method="compose")
        
        # Add original audio
        if video.audio:
            concat_clip = concat_clip.set_audio(video.audio)
        
        # Write output video with optimized settings
        if progress_callback:
            progress_callback(90)
            
        concat_clip.write_videofile(
            output_path, 
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            preset='faster'  # Use faster preset for quicker encoding
        )
        
        if progress_callback:
            progress_callback(100)
        
        # Clean up temporary files
        for f in frames + transformed_frames:
            if os.path.exists(f):
                os.remove(f)
        
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)
        
        return output_path

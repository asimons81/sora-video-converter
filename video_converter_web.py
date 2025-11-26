import streamlit as st
import subprocess
import os
import tempfile
import json
from pathlib import Path

# --- Configuration ---
st.set_page_config(page_title="1080p Converter", page_icon="🎬")

def get_video_dimensions(input_path):
    """Uses ffprobe to get video width and height."""
    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-select_streams", "v:0", 
        "-show_entries", "stream=width,height", 
        "-of", "json", 
        str(input_path)
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        info = json.loads(result.stdout)
        width = int(info['streams'][0]['width'])
        height = int(info['streams'][0]['height'])
        return width, height
    except Exception as e:
        st.error(f"Error reading video info: {e}")
        return None, None

def convert_video(input_path, output_path):
    """Converts video to 1080p (Landscape or Portrait)."""
    width, height = get_video_dimensions(input_path)
    if width is None:
        return False

    if width >= height:
        target_w, target_h = 1920, 1080 # Landscape
    else:
        target_w, target_h = 1080, 1920 # Portrait

    # FFmpeg filter: Scale to fit box, pad with black to fill box
    filter_str = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2"

    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-vf", filter_str,
        "-c:v", "libx264",
        "-crf", "23",     # Balanced quality
        "-preset", "fast", # Faster encoding for cloud
        "-c:a", "copy",
        str(output_path)
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"FFmpeg conversion failed.")
        return False

# --- UI Layout ---
st.title("🎬 1080p Video Standardizer")
st.write("Upload videos from your phone or computer to automatically crop/pad them to 1080p.")

uploaded_files = st.file_uploader("Choose videos", type=['mp4', 'mov', 'avi', 'mkv'], accept_multiple_files=True)

if uploaded_files:
    st.write(f"**{len(uploaded_files)} files queued.**")
    
    if st.button("Start Conversion"):
        progress_bar = st.progress(0)
        
        # Create a temporary directory to store files during processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # 1. Save uploaded file to temp disk
                input_file_path = temp_path / uploaded_file.name
                output_filename = f"1080p_{uploaded_file.name}"
                output_file_path = temp_path / output_filename
                
                with open(input_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 2. Process
                status_text = st.empty()
                status_text.text(f"Converting: {uploaded_file.name}...")
                
                success = convert_video(input_file_path, output_file_path)
                
                # 3. Create Download Link
                if success:
                    with open(output_file_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download {output_filename}",
                            data=f,
                            file_name=output_filename,
                            mime="video/mp4"
                        )
                    status_text.success(f"Finished: {uploaded_file.name}")
                
                # Update progress bar
                progress_bar.progress((i + 1) / len(uploaded_files))
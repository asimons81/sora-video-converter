import streamlit as st
import subprocess
import os
import tempfile
import json
from pathlib import Path

# --- Configuration ---
st.set_page_config(page_title="1080p Converter", page_icon="✨", layout="centered")

# --- Modern UI Styling ---
st.markdown("""
    <style>
    /* Header styling */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        text-align: center;
        padding-bottom: 0.5rem;
    }
    
    /* Subheader styling */
    .description {
        text-align: center;
        color: #6c757d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Main Action Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 600;
        height: 3rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }
    
    /* Success/Result Cards */
    .result-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid #e9ecef;
    }
    </style>
    """, unsafe_allow_html=True)

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
        return False

# --- UI Layout ---

# Header Section
st.markdown("<h1>✨ Video Standardizer</h1>", unsafe_allow_html=True)
st.markdown("<p class='description'>Upload your videos to automatically format them to standard 1080p.</p>", unsafe_allow_html=True)

# Main Interface
with st.container():
    uploaded_files = st.file_uploader("", type=['mp4', 'mov', 'avi', 'mkv'], accept_multiple_files=True)

if uploaded_files:
    st.write("---")
    # Center the action button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # type="primary" gives it the accent color
        start_btn = st.button(f"🚀 Convert {len(uploaded_files)} Videos", type="primary")
    
    if start_btn:
        progress_bar = st.progress(0)
        status_area = st.empty()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # UI Status Update
                status_area.caption(f"Processing {i+1}/{len(uploaded_files)}: {uploaded_file.name}...")
                
                # 1. Save uploaded file
                input_file_path = temp_path / uploaded_file.name
                output_filename = f"1080p_{uploaded_file.name}"
                output_file_path = temp_path / output_filename
                
                with open(input_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 2. Process
                success = convert_video(input_file_path, output_file_path)
                
                # 3. Create Result Card
                if success:
                    with open(output_file_path, "rb") as f:
                        # Create a nice layout for the result
                        with st.container():
                            c1, c2 = st.columns([3, 2])
                            with c1:
                                st.success(f"Ready: {output_filename}")
                            with c2:
                                st.download_button(
                                    label="⬇️ Download",
                                    data=f,
                                    file_name=output_filename,
                                    mime="video/mp4",
                                    key=f"dl_{i}",
                                    use_container_width=True
                                )
                else:
                    st.error(f"Failed to process {uploaded_file.name}")
                
                # Update progress
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_area.empty()
            st.balloons()

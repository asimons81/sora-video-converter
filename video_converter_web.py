import streamlit as st
import subprocess
import os
import tempfile
import json
from pathlib import Path

# --- Configuration ---
st.set_page_config(
    page_title="TRT Video Standardizer", 
    page_icon="🎬", 
    layout="centered"
)

# --- Brand Configuration ---
BRAND_COLOR = "#4fb7a0"
BRAND_HOVER = "#3caea3" # Slightly darker for hover effects

# --- Modern UI Styling (Tony Reviews Things Theme) ---
st.markdown(f"""
    <style>
    /* Main Background adjustments if needed */
    .stApp {{
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }}

    /* Header styling */
    h1 {{
        color: #2c3e50;
        font-weight: 800;
        text-align: center;
        letter-spacing: -1px;
        padding-bottom: 0.5rem;
    }}
    
    /* Subheader/Description styling */
    .description {{
        text-align: center;
        color: #6c757d;
        font-size: 1.15rem;
        margin-bottom: 3rem;
        font-weight: 300;
    }}
    
    /* Branding Accent Line */
    .brand-divider {{
        height: 4px;
        width: 60px;
        background-color: {BRAND_COLOR};
        margin: 0 auto 20px auto;
        border-radius: 2px;
    }}

    /* Primary Action Button Styling */
    div.stButton > button:first-child {{
        background-color: {BRAND_COLOR};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        height: 3.5rem;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(79, 183, 160, 0.2);
    }}
    
    div.stButton > button:first-child:hover {{
        background-color: {BRAND_HOVER};
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(79, 183, 160, 0.3);
        color: white;
    }}
    
    div.stButton > button:first-child:active {{
        transform: translateY(0);
    }}

    /* Success/Result Cards */
    .result-card {{
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }}
    
    /* File Uploader Customization */
    [data-testid='stFileUploader'] {{
        border-radius: 12px;
    }}
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
st.markdown("<h1>Video Standardizer</h1>", unsafe_allow_html=True)
st.markdown("<div class='brand-divider'></div>", unsafe_allow_html=True)
st.markdown("<p class='description'>Format your Sora generations for the Tony Reviews Things feed.</p>", unsafe_allow_html=True)

# Main Interface
with st.container():
    uploaded_files = st.file_uploader("Drop your raw files here", type=['mp4', 'mov', 'avi', 'mkv'], accept_multiple_files=True)

if uploaded_files:
    st.write("---")
    # Center the action button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # The styling for this button is handled in the CSS injection above
        start_btn = st.button(f"🚀 Process {len(uploaded_files)} Videos")
    
    if start_btn:
        progress_bar = st.progress(0)
        status_area = st.empty()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # UI Status Update
                status_area.info(f"Processing **{uploaded_file.name}** ({i+1}/{len(uploaded_files)})...")
                
                # 1. Save uploaded file
                input_file_path = temp_path / uploaded_file.name
                output_filename = f"TRT_1080p_{uploaded_file.name}"
                output_file_path = temp_path / output_filename
                
                with open(input_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 2. Process
                success = convert_video(input_file_path, output_file_path)
                
                # 3. Create Result Card
                if success:
                    with open(output_file_path, "rb") as f:
                        # Create a nice layout for the result
                        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                        c1, c2 = st.columns([3, 2])
                        with c1:
                            st.success(f"✅ Ready: {output_filename}")
                        with c2:
                            st.download_button(
                                label="⬇️ Download Video",
                                data=f,
                                file_name=output_filename,
                                mime="video/mp4",
                                key=f"dl_{i}",
                                use_container_width=True
                            )
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error(f"❌ Failed to process {uploaded_file.name}")
                
                # Update progress
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_area.empty()
            st.balloons()

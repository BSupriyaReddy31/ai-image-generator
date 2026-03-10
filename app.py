import streamlit as st
import google.generativeai as genai
import requests
import io
import urllib.parse
import urllib.request
import random
import concurrent.futures
from PIL import Image, ImageDraw, ImageFont
import os
from dotenv import load_dotenv

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Image Studio", page_icon="✨", layout="wide")

# --- SESSION STATE MEMORY ---
if "generated_images" not in st.session_state:
    st.session_state.generated_images = []
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# --- SOFT "NATURAL" CSS ---
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"], h1, h2, h3, p, label, .stButton>button { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #fafafa; color: #1a1a1a !important; }
    .main-header { text-align: center; margin-top: 2rem; margin-bottom: 0.5rem; color: #111827; font-weight: 700; font-size: 3rem;}
    .sub-header { text-align: center; color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stTextArea textarea { background-color: #ffffff !important; border: 2px solid #e5e7eb !important; border-radius: 16px !important; padding: 15px !important; font-size: 1.1rem !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    .stTextArea textarea:focus { border-color: #6366f1 !important; box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important; }
    .stTextInput input { border-radius: 10px !important; border: 1px solid #e5e7eb !important; }
    .stButton>button { background-color: #6366f1; color: #ffffff !important; border: none; border-radius: 12px; font-weight: 600; font-size: 1.1rem; width: 100%; padding: 12px; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2); }
    .stButton>button:hover { background-color: #4f46e5; transform: translateY(-2px); box-shadow: 0 6px 16px rgba(99, 102, 241, 0.3); }
    .image-card { background: #ffffff; padding: 15px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #f3f4f6; margin-top: 1rem; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- SETUP API KEYS ---
load_dotenv()
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    gemini_api_key = os.getenv("GEMINI_API_KEY")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
text_model = genai.GenerativeModel('gemini-2.5-flash')

# --- FEATURE 1: WATERMARK / TEXT ENGINE ---
def apply_overlay_text(image, text, position):
    if not text:
        return image
    
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    # Download a bold, professional font dynamically
    try:
        font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Black.ttf"
        font_response = urllib.request.urlopen(font_url)
        font = ImageFont.truetype(io.BytesIO(font_response.read()), size=120)
    except Exception:
        font = ImageFont.load_default() # Fallback

    # Calculate text size using the modern method
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    img_w, img_h = img_copy.size
    
    # Determine coordinates
    padding = 50
    if position == "Center":
        x = (img_w - text_w) / 2
        y = (img_h - text_h) / 2
    elif position == "Top Right":
        x = img_w - text_w - padding
        y = padding
    elif position == "Bottom Left":
        x = padding
        y = img_h - text_h - padding
    elif position == "Bottom Center":
        x = (img_w - text_w) / 2
        y = img_h - text_h - padding
    else:
        x, y = padding, padding

    # Draw Text (with a slight black shadow for readability)
    shadow_offset = 5
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    return img_copy

# --- FEATURE 3: PARALLEL IMAGE GENERATION ---
def fetch_single_image(prompt, seed):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return Image.open(io.BytesIO(res.content))
    except Exception:
        pass
    return None

def generate_magic_variations(user_input, overlay_text, text_position):
    # 1. Gemini writes the master prompt
    system_prompt = f"The user wants an image of: '{user_input}'. Write a highly detailed, descriptive paragraph prompt for a next-generation AI image model. Focus heavily on lighting, textures, and realism. Do not include introductory text."
    try:
        enhanced_prompt = text_model.generate_content(system_prompt).text.strip()
    except Exception:
        enhanced_prompt = f"A highly detailed, photorealistic image of {user_input}, 8k resolution, professional lighting."

    # 2. Generate 3 unique seeds for the variations
    seeds = [random.randint(1, 999999) for _ in range(3)]
    images = []

    # 3. Fetch all 3 images at the exact same time (Parallel Processing)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_single_image, enhanced_prompt, seed) for seed in seeds]
        for future in concurrent.futures.as_completed(futures):
            img = future.result()
            if img:
                # Apply the text overlay if the user requested it!
                final_img = apply_overlay_text(img, overlay_text, text_position)
                images.append(final_img)
    
    return images

# --- APP LAYOUT ---
st.markdown("<h1 class='main-header'>✨ AI Image Studio Pro</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Generate 3 magic variations instantly.</p>", unsafe_allow_html=True)

# Central Search Bar
user_idea = st.text_area("What would you like to create?", 
                         key="user_prompt", 
                         placeholder="e.g., A breathtaking advertisement poster for a dance show...", 
                         height=100, label_visibility="collapsed")

# Advanced Tools (Cleanly hidden in an expander)
with st.expander("🛠️ Add Brand Overlay Text (Optional)"):
    col_text, col_pos = st.columns(2)
    with col_text:
        overlay_text = st.text_input("Text to Stamp", placeholder="e.g., AATA")
    with col_pos:
        text_position = st.selectbox("Text Position", ["Center", "Top Right", "Bottom Center", "Bottom Left", "Top Left"])

# Generate Button
st.markdown("<br>", unsafe_allow_html=True)
_, center_col, _ = st.columns([1, 2, 1]) 
with center_col:
    if st.button("✨ Generate 3 Variations", type="primary"):
        if not st.session_state.user_prompt:
            st.warning("Please describe what you want to generate first!")
        else:
            st.session_state.is_generating = True

# Results Section
if st.session_state.is_generating:
    with st.spinner("🎨 Generating 3 unique masterpieces simultaneously..."):
        results = generate_magic_variations(st.session_state.user_prompt, overlay_text, text_position)
        
        if not results:
            st.error("Error: Could not connect to image server.")
        else:
            st.session_state.generated_images = results
            
    st.session_state.is_generating = False

# Display the Grid!
if st.session_state.generated_images:
    st.markdown("### Your Variations")
    cols = st.columns(3) # Create a 3-column grid
    
    for i, img in enumerate(st.session_state.generated_images):
        with cols[i]:
            st.markdown("<div class='image-card'>", unsafe_allow_html=True)
            st.image(img, use_container_width=True)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            
            st.download_button(
                label=f"📥 Download V{i+1}",
                data=buf.getvalue(),
                file_name=f"ai_studio_v{i+1}.png",
                mime="image/png",
                use_container_width=True,
                key=f"dl_btn_{i}"
            )
            st.markdown("</div>", unsafe_allow_html=True)

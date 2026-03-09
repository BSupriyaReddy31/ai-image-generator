import streamlit as st
import google.generativeai as genai
import requests
import io
from PIL import Image
import os
from dotenv import load_dotenv

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Image Studio", page_icon="✨", layout="centered")

# --- SESSION STATE MEMORY ---
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False

# --- SOFT "NATURAL" CSS ---
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"], h1, h2, h3, p, label, .stButton>button {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp { background-color: #fafafa; color: #1a1a1a !important; }
    
    .main-header { text-align: center; margin-top: 2rem; margin-bottom: 0.5rem; color: #111827; font-weight: 700; font-size: 3rem;}
    .sub-header { text-align: center; color: #6b7280; font-size: 1.1rem; margin-bottom: 3rem; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    .stTextArea textarea {
        background-color: #ffffff !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 16px !important;
        padding: 15px !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
    }

    .stButton>button {
        background-color: #6366f1; color: #ffffff !important;
        border: none; border-radius: 12px; font-weight: 600; font-size: 1.1rem;
        width: 100%; padding: 12px; transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    }
    .stButton>button:hover {
        background-color: #4f46e5; transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.3);
    }
    
    .image-card {
        background: #ffffff; padding: 20px; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #f3f4f6;
        margin-top: 2rem;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- SETUP API KEYS ---
load_dotenv()
try:
    hf_api_key = st.secrets["HF_API_KEY"]
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    hf_api_key = os.getenv("HF_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
text_model = genai.GenerativeModel('gemini-2.5-flash')

# --- INVISIBLE AI LOGIC ---
def render_image(user_input):
    # 1. Gemini engineers the perfect prompt
    system_prompt = f"The user wants an image of: '{user_input}'. Write a highly detailed, descriptive paragraph prompt for a next-generation AI image model. Include precise details about lighting, camera angle, atmosphere, and EXACT text placement if the user requested text. Do not include introductory text."
    
    try:
        enhanced_prompt = text_model.generate_content(system_prompt).text.strip()
    except Exception:
        enhanced_prompt = f"A highly detailed, photorealistic image of {user_input}, 8k resolution, professional lighting."

    # 2. The Ultimate Free API bypass (Pollinations AI)
    import urllib.parse
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    
    # We request a clean 1024x1024 image with no logos
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            return f"Error {response.status_code}: The free image server is currently busy."
    except Exception as e:
        return "Error: Could not connect to the free image server."

# --- APP LAYOUT (Top-to-Bottom Flow) ---
st.markdown("<h1 class='main-header'>✨ AI Image Studio</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Describe your vision. Let AI do the rest.</p>", unsafe_allow_html=True)

user_idea = st.text_area("What would you like to create?", 
                         key="user_prompt", 
                         placeholder="e.g., A breathtaking advertisement poster with the word 'AATA' in the center...", 
                         height=100, label_visibility="collapsed")

# 2. Generate Button
st.markdown("<br>", unsafe_allow_html=True)
_, center_col, _ = st.columns([1, 2, 1]) 
with center_col:
    if st.button("✨ Generate Masterpiece", type="primary"):
        if not st.session_state.user_prompt:
            st.warning("Please describe what you want to generate first!")
        else:
            st.session_state.is_generating = True

# 3. Results Section
if st.session_state.is_generating:
    with st.spinner("🎨 Weaving the pixels together using FLUX.1..."):
        result = render_image(st.session_state.user_prompt)
        
        if isinstance(result, str):
            st.error(result)
        else:
            st.session_state.current_image = result
            
    st.session_state.is_generating = False

if st.session_state.current_image:
    st.markdown("<div class='image-card'>", unsafe_allow_html=True)
    st.image(st.session_state.current_image, use_container_width=True)
    
    buf = io.BytesIO()
    st.session_state.current_image.save(buf, format="PNG")
    
    _, dl_col, _ = st.columns([1, 1, 1])
    with dl_col:
        st.download_button(
            label="📥 Download High-Res",
            data=buf.getvalue(),
            file_name="ai_studio_render.png",
            mime="image/png",
            use_container_width=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

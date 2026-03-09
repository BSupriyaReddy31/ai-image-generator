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
if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""
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
    
    /* Center the main title nicely */
    .main-header { text-align: center; margin-top: 2rem; margin-bottom: 0.5rem; color: #111827; font-weight: 700; font-size: 3rem;}
    .sub-header { text-align: center; color: #6b7280; font-size: 1.1rem; margin-bottom: 3rem; }

    /* Hide default header/footer */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    /* Make the text area look like a modern search/prompt bar */
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

    /* Soft, friendly generate button */
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
    
    /* Inspiration Chips (Secondary Buttons) */
    .inspiration-row .stButton>button {
        background-color: #f3f4f6; color: #4b5563 !important;
        border: 1px solid #e5e7eb; border-radius: 20px; font-weight: 500; font-size: 0.9rem;
        padding: 5px 15px; box-shadow: none; margin-top: 0;
    }
    .inspiration-row .stButton>button:hover { background-color: #e5e7eb; color: #111827 !important; transform: none; }
    
    /* Image Display Card */
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
    system_prompt = f"The user wants an image of: '{user_input}'. Write a detailed, comma-separated prompt for Stable Diffusion XL. Include professional photography terms, lighting, and high quality keywords. Do not include introductory text."
    
    try:
        enhanced_prompt = text_model.generate_content(system_prompt).text.strip()
    except Exception:
        enhanced_prompt = f"Professional high quality photo of {user_input}, 8k resolution, highly detailed."

    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {
        "inputs": enhanced_prompt,
        "parameters": {
            "negative_prompt": "ugly, deformed, bad anatomy, weird legs, bad hands, missing fingers, blurry, text, watermark, low quality",
            "guidance_scale": 7.5 
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            return f"Error: API returned {response.status_code}"
    except Exception as e:
        return "Error: Could not connect to image server."

# --- CALLBACK FUNCTIONS ---
def set_prompt(text):
    st.session_state.prompt_input = text

# --- APP LAYOUT (Top-to-Bottom Flow) ---
st.markdown("<h1 class='main-header'>✨ AI Image Studio</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Describe your vision. Let AI do the rest.</p>", unsafe_allow_html=True)

# 1. The Prompt Bar
user_idea = st.text_area("What would you like to create?", 
                         value=st.session_state.prompt_input, 
                         placeholder="e.g., A floating glowing orb in a dark forest...", 
                         height=100, label_visibility="collapsed")

# 2. Inspiration Chips (Natural guidance for the user)
st.markdown("<div class='inspiration-row'>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.button("☕ Cozy Coffee", on_click=set_prompt, args=("A cozy cup of coffee on a wooden table, rainy window background",))
with col2:
    st.button("🎧 Tech Gadget", on_click=set_prompt, args=("Sleek minimalist wireless headphones, neon studio lighting",))
with col3:
    st.button("🌿 Organic Skincare", on_click=set_prompt, args=("A glass bottle of skincare serum on a wet stone, natural sunlight",))
with col4:
    st.button("🚀 Cyberpunk City", on_click=set_prompt, args=("A futuristic cyberpunk street at night, glowing neon signs, rainy",))
st.markdown("</div>", unsafe_allow_html=True)

# 3. Generate Button
st.markdown("<br>", unsafe_allow_html=True)
_, center_col, _ = st.columns([1, 2, 1]) # Center the button
with center_col:
    if st.button("✨ Generate Masterpiece", type="primary"):
        if not user_idea:
            st.warning("Please describe what you want to generate first!")
        else:
            st.session_state.is_generating = True

# 4. Results Section (Appears naturally below)
if st.session_state.is_generating:
    with st.spinner("🎨 Weaving the pixels together..."):
        result = render_image(user_idea)
        
        if isinstance(result, str):
            st.error(result)
        else:
            st.session_state.current_image = result
            st.session_state.prompt_input = user_idea # Lock in the text they typed
            
    st.session_state.is_generating = False

if st.session_state.current_image:
    st.markdown("<div class='image-card'>", unsafe_allow_html=True)
    st.image(st.session_state.current_image, use_container_width=True)
    
    # Clean download button right below the image
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

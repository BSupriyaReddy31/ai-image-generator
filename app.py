import streamlit as st
import google.generativeai as genai
import requests
import io
from PIL import Image
import os
from dotenv import load_dotenv

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Image Studio", page_icon="🖼️", layout="wide")

# --- SESSION STATE MEMORY ---
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "image_history" not in st.session_state:
    st.session_state.image_history = [] 

# --- CLEAN MINIMALIST CSS ---
custom_css = """
<style>
    /* Modern, clean font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"], h1, h2, h3, p, label, .stButton>button {
        font-family: 'Inter', sans-serif !important;
    }

    /* Clean white and light gray background */
    .stApp { background-color: #f8f9fa; color: #1f2937 !important; }
    
    /* Clean headers */
    h1 { color: #111827; font-weight: 600; padding-bottom: 0px; }
    p { color: #6b7280; font-size: 1.1rem; }

    /* Hide standard streamlit elements */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    /* Simple, clean white cards with soft shadows */
    .clean-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    .clean-card h3 { margin-top: 0; color: #374151; font-size: 1.3rem; margin-bottom: 15px;}

    /* Minimalist inputs */
    .stTextInput input, .stTextArea textarea {
        background-color: #f9fafb !important;
        border: 1px solid #d1d5db !important;
        color: #111827 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }

    /* Modern Blue Primary Button */
    .stButton>button {
        background-color: #2563eb; color: #ffffff !important;
        border: none; border-radius: 8px; font-weight: 500;
        width: 100%; padding: 10px; margin-top: 15px; transition: 0.2s;
    }
    .stButton>button:hover { background-color: #1d4ed8; }
    
    /* Secondary Download Button */
    .stDownloadButton>button {
        background-color: #ffffff; color: #374151 !important;
        border: 1px solid #d1d5db; border-radius: 8px; font-weight: 500;
        width: 100%; padding: 10px; transition: 0.2s;
    }
    .stDownloadButton>button:hover { background-color: #f3f4f6; color: #111827 !important; }

    /* Clean Tabs */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #e5e7eb; gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #6b7280 !important; padding: 10px 0; background: transparent; border: none; font-weight: 500;}
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #2563eb !important; border-bottom: 2px solid #2563eb; }
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
    # 1. Gemini secretly makes the prompt better for the user
    system_prompt = f"The user wants an image of: '{user_input}'. Write a detailed, comma-separated prompt for Stable Diffusion XL. Include professional photography terms, lighting, and high quality keywords. Do not include introductory text."
    
    try:
        enhanced_prompt = text_model.generate_content(system_prompt).text.strip()
    except Exception:
        enhanced_prompt = f"Professional high quality photo of {user_input}, 8k resolution, highly detailed."

    # 2. Hugging Face generates the image using standard safe settings
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    payload = {
        "inputs": enhanced_prompt,
        "parameters": {
            "negative_prompt": "ugly, deformed, bad anatomy, weird legs, bad hands, missing fingers, blurry, text, watermark, low quality",
            "guidance_scale": 7.5 # Locked to standard creativity
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

# --- APP LAYOUT ---
st.title("AI Image Studio")
st.markdown("<p style='margin-bottom: 30px;'>Instantly generate professional product photos and marketing assets.</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Create Image", "History"])

with tab1:
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with col1:
        st.markdown("<div class='clean-card'>", unsafe_allow_html=True)
        st.markdown("<h3>Image Details</h3>", unsafe_allow_html=True)
        
        # Stripped down to just one highly intuitive input box
        user_idea = st.text_area(
            "What do you want to generate?", 
            placeholder="e.g., A minimalist black coffee cup on a marble table with bright morning lighting",
            height=120
        )
        
        generate_btn = st.button("Generate Image")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='clean-card' style='text-align: center;'>", unsafe_allow_html=True)
        
        if generate_btn:
            if not user_idea:
                st.warning("Please describe what you want to generate.")
            elif not hf_api_key or not gemini_api_key:
                st.error("API Keys are missing from secrets.")
            else:
                with st.spinner("Generating image..."):
                    result = render_image(user_idea)
                    
                    if isinstance(result, str):
                        st.error("Something went wrong with the image server. Please try again.")
                    else:
                        st.session_state.current_image = result
                        st.session_state.image_history.insert(0, {"prompt": user_idea, "image": result})

        if st.session_state.current_image:
            st.image(st.session_state.current_image, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            buf = io.BytesIO()
            st.session_state.current_image.save(buf, format="PNG")
            st.download_button(
                label="Download Image",
                data=buf.getvalue(),
                file_name="ai_generated_image.png",
                mime="image/png"
            )
        else:
            st.markdown("<p style='padding: 60px 0;'>Your image will appear here.</p>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='clean-card'>", unsafe_allow_html=True)
    st.markdown("<h3>Session History</h3>", unsafe_allow_html=True)
    
    if not st.session_state.image_history:
        st.markdown("<p>No images generated in this session yet.</p>", unsafe_allow_html=True)
    else:
        for i, record in enumerate(st.session_state.image_history):
            with st.expander(f"Prompt: {record['prompt'][:50]}..."):
                st.image(record['image'], use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st
import requests
import io
from PIL import Image
import os
from dotenv import load_dotenv

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Brand Ad Generator", page_icon="🎨", layout="wide")

# --- SESSION STATE MEMORY ---
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "image_history" not in st.session_state:
    st.session_state.image_history = [] 

# --- CUSTOM CSS (Visily Pastel Theme) ---
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], h1, h2, h3, .stApp label, .stTabs [data-baseweb="tab"], .stButton>button {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp { background-color: #debafe; color: #261c2c !important; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #c8a3e8; }

    #title-container { text-align: center; padding-bottom: 20px; margin-top: 10px; }
    #title-container h1 { font-size: 3.5rem; font-weight: 700; color: #30153e; margin-bottom: 0.2rem; letter-spacing: -1px; }
    #title-container p { color: #4a3b52; font-size: 1.1rem; margin-top: 0; font-weight: 400; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    .glowing-card {
        border-radius: 12px; padding: 25px; margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(48, 21, 62, 0.08); transition: transform 0.2s ease;
    }
    
    #details-card { background-color: #ffffff; border: 1px solid #f0e6fc; }
    #draft-card { background-color: #30153e; border: none; text-align: center; }
    
    #details-card h2 { font-size: 1.6rem; color: #30153e !important; margin-bottom: 1rem; font-weight: 700; }
    #draft-card h2 { font-size: 1.6rem; color: #fcfaff !important; margin-bottom: 1rem; font-weight: 700; }

    .stTextInput label, .stSelectbox label, .stTextArea label { color: #4a3b52 !important; font-weight: 500 !important; }
    [data-testid="stNotification"] { background-color: #fcfaff !important; border-left: 4px solid #592eff !important; }
    [data-testid="stNotification"] p { color: #4a3b52 !important; }

    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important; color: #261c2c !important; 
        border-radius: 8px !important; border: 1px solid #d3bcf2 !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus { border-color: #592eff !important; box-shadow: 0 0 0 2px rgba(89, 46, 255, 0.2) !important; }

    .stButton>button, .stDownloadButton>button {
        background-color: #592eff; color: #ffffff !important; border: none; border-radius: 8px;
        font-weight: 600; font-size: 1.1rem; width: 100%; padding: 8px; margin-top: 10px; transition: all 0.2s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #4620d4; transform: translateY(-1px); box-shadow: 0 4px 15px rgba(89, 46, 255, 0.3);
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 20px; background-color: transparent; border-bottom: 1px solid #c8a3e8; padding-bottom: 0; margin-bottom: 25px; }
    .stTabs [data-baseweb="tab"] { color: #4a3b52 !important; padding: 10px 10px; background-color: transparent; border: none; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #592eff !important; border-bottom: 3px solid #592eff; font-weight: 600; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- SETUP & CONFIGURATION ---
load_dotenv()
# NOTE: You will need to add HF_API_KEY to your Streamlit secrets or .env file!
try:
    hf_api_key = st.secrets["HF_API_KEY"]
except (KeyError, FileNotFoundError):
    hf_api_key = os.getenv("HF_API_KEY")

# --- AI LOGIC (STABLE DIFFUSION VIA HUGGING FACE) ---
def generate_brand_image(product, brand_colors, vibe):
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    
    # 1. The Positive Prompt (What we WANT)
    master_prompt = f"Professional photography of a {product}. The primary brand colors are {brand_colors}. The visual style and vibe is {vibe}. 8k resolution, highly detailed, marketing advertisement, commercial studio lighting, clean elegant background."
    
    # 2. The Negative Prompt (What we DO NOT WANT)
    # This stops the AI from generating clumsy limbs, extra fingers, or weird distortions!
    negative_prompt = "ugly, deformed, clumsy, extra limbs, bad anatomy, distorted proportions, weird legs, bad hands, missing fingers, blurry, text, watermark, low quality, cartoon, mutated"
    
    # 3. The Payload (Sending both to the API)
    payload = {
        "inputs": master_prompt,
        "parameters": {
            "negative_prompt": negative_prompt
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            image_bytes = response.content
            return Image.open(io.BytesIO(image_bytes))
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Exception: {str(e)}"

# --- STRUCTURAL LAYOUT ---
st.markdown("""
    <div id='title-container'>
        <h1>AI Brand Ad Generator</h1>
        <p>Turn simple products into studio-quality marketing assets instantly.</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["✨ Generate Ad", "🗄️ Image History"])

with tab1:
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with col1:
        st.markdown("<div class='glowing-card' id='details-card'><h2>Brand Details</h2>", unsafe_allow_html=True)
        st.info("Define the visual identity for your product advertisement.")
        
        product_name = st.text_input("What is the product?", placeholder="e.g., A sleek stainless steel coffee thermos")
        brand_colors = st.text_input("Core Brand Colors", placeholder="e.g., Matte Black and Neon Green")
        vibe = st.selectbox("Visual Vibe & Style", ["Minimalist & Modern", "Cyberpunk / Futuristic", "Corporate & Trustworthy", "Playful & Vibrant", "Luxury & Elegant"])
        
        generate_btn = st.button("Generate Ad Image", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glowing-card' id='draft-card'><h2>Your Generated Asset</h2>", unsafe_allow_html=True)
        
        if generate_btn:
            if not product_name or not brand_colors:
                st.warning("⚠️ Please fill out the product name and brand colors.")
            elif not hf_api_key:
                st.error("🚨 Missing HF_API_KEY. Please add your free Hugging Face token to your secrets!")
            else:
                with st.spinner("🎨 AI is rendering your studio-quality image..."):
                    result = generate_brand_image(product_name, brand_colors, vibe)
                    
                    if isinstance(result, str) and (result.startswith("Error") or result.startswith("Exception")):
                        st.error(f"🚨 API Issue: {result}")
                    else:
                        st.session_state.current_image = result
                        # Save to session history
                        st.session_state.image_history.insert(0, {
                            "product": product_name,
                            "vibe": vibe,
                            "image": result
                        })

        if st.session_state.current_image:
            st.success("✅ Image rendered successfully!")
            
            # Display the image
            st.image(st.session_state.current_image, use_container_width=True)
            
            st.divider()
            
            # --- NEW: Download Button Logic ---
            # Convert PIL image to bytes for downloading
            buf = io.BytesIO()
            st.session_state.current_image.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 Download High-Res Image",
                data=byte_im,
                file_name=f"brand_ad_{product_name.replace(' ', '_')}.png",
                mime="image/png"
            )
        else:
            st.markdown("<p style='color: #bfa6e8; margin-top: 50px;'>Your generated advertisement will appear here...</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glowing-card' style='background-color: #ffffff; border: 1px solid #f0e6fc;'><h2>Current Session History</h2>", unsafe_allow_html=True)
    st.caption("These images are saved temporarily. They will be securely erased when you close this window.")
    
    if not st.session_state.image_history:
        st.info("No images generated yet. Head over to the 'Generate Ad' tab to render one!")
    else:
        for i, record in enumerate(st.session_state.image_history):
            with st.expander(f"🖼️ Product: {record['product']} | 🎭 Style: {record['vibe']}"):
                st.image(record['image'], use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)






































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

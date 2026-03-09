import streamlit as st
import google.generativeai as genai
import requests
import io
from PIL import Image
import os
import urllib.parse
from dotenv import load_dotenv

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Brand Ad Generator Pro", page_icon="🎨", layout="wide")

# --- SESSION STATE MEMORY ---
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "current_enhanced_prompt" not in st.session_state:
    st.session_state.current_enhanced_prompt = ""
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
    .stTextInput label, .stSelectbox label, .stTextArea label, .stSlider label { color: #4a3b52 !important; font-weight: 600 !important; }
    [data-testid="stNotification"] { background-color: #fcfaff !important; border-left: 4px solid #592eff !important; }
    [data-testid="stNotification"] p { color: #4a3b52 !important; }
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important; color: #261c2c !important; 
        border-radius: 8px !important; border: 1px solid #d3bcf2 !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #592eff; color: #ffffff !important; border: none; border-radius: 8px;
        font-weight: 600; font-size: 1.1rem; width: 100%; padding: 8px; margin-top: 10px; transition: all 0.2s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #4620d4; transform: translateY(-1px); box-shadow: 0 4px 15px rgba(89, 46, 255, 0.3);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- SETUP & CONFIGURATION ---
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

# --- FEATURE 1: GEMINI AUTO-PROMPT ENHANCER ---
def enhance_prompt_with_gemini(product, brand_colors, vibe):
    system_prompt = f"""
    You are an expert AI image generation prompt engineer. 
    The user wants an advertisement image for: '{product}'. 
    The brand colors are: '{brand_colors}'. 
    The vibe is: '{vibe}'. 
    
    Write a highly detailed, comma-separated prompt for Stable Diffusion XL. Include professional photography terms, lighting details (e.g., volumetric lighting, studio softbox), camera angles, and rendering techniques (e.g., 8k resolution, octane render). 
    DO NOT include any introductory text, just return the raw prompt.
    """
    try:
        response = text_model.generate_content(system_prompt)
        return response.text.strip()
    except Exception as e:
        # Fallback to a basic prompt if Gemini fails
        return f"Professional photography of a {product}, brand colors {brand_colors}, style {vibe}, 8k resolution, highly detailed, commercial studio lighting."

# --- AI LOGIC: STABLE DIFFUSION WITH ADVANCED PARAMETERS ---
def generate_brand_image(master_prompt, width, height, cfg_scale):
    API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_api_key}"}
    
    negative_prompt = "ugly, deformed, clumsy, extra limbs, bad anatomy, distorted proportions, weird legs, bad hands, missing fingers, blurry, text, watermark, low quality, cartoon, mutated"
    
    payload = {
        "inputs": master_prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "width": width,       # FEATURE 2: Custom Aspect Ratios
            "height": height,
            "guidance_scale": cfg_scale # FEATURE 3: Creativity Slider
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Exception: {str(e)}"

# --- STRUCTURAL LAYOUT ---
st.markdown("""
    <div id='title-container'>
        <h1>AI Brand Ad Generator Pro</h1>
        <p>Multi-Model Pipeline: Gemini Prompt Engineering + SDXL Image Rendering.</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["✨ Generate Ad", "🗄️ Image History"])

with tab1:
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with col1:
        st.markdown("<div class='glowing-card' id='details-card'><h2>Brand Details</h2>", unsafe_allow_html=True)
        
        product_name = st.text_input("What is the product?", placeholder="e.g., A sleek stainless steel coffee thermos")
        brand_colors = st.text_input("Core Brand Colors", placeholder="e.g., Matte Black and Neon Green")
        vibe = st.selectbox("Visual Vibe & Style", ["Minimalist & Modern", "Cyberpunk / Futuristic", "Corporate & Trustworthy", "Playful & Vibrant", "Luxury & Elegant"])
        
        st.divider()
        st.markdown("#### ⚙️ Advanced Settings")
        
        # FEATURE 2: Aspect Ratio Selector
        format_choice = st.selectbox("Ad Format (Aspect Ratio)", [
            "Instagram Square (1:1)", 
            "TikTok / Reels (9:16)", 
            "Web Banner (16:9)"
        ])
        
        # FEATURE 3: Creativity Slider (CFG Scale)
        cfg_scale = st.slider("AI Creativity Level (Guidance Scale)", min_value=1.0, max_value=20.0, value=7.5, step=0.5, 
                              help="Lower = AI goes wild/artistic. Higher = AI strictly follows your prompt.")
        
        generate_btn = st.button("Generate Ad Image", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glowing-card' id='draft-card'><h2>Your Generated Asset</h2>", unsafe_allow_html=True)
        
        if generate_btn:
            if not product_name or not brand_colors:
                st.warning("⚠️ Please fill out the product name and brand colors.")
            elif not hf_api_key or not gemini_api_key:
                st.error("🚨 Missing API Keys. Ensure both HF_API_KEY and GEMINI_API_KEY are in your secrets!")
            else:
                # Determine dimensions based on user choice
                if format_choice == "Instagram Square (1:1)":
                    w, h = 1024, 1024
                elif format_choice == "TikTok / Reels (9:16)":
                    w, h = 768, 1344
                else: # Web Banner
                    w, h = 1344, 768

                with st.spinner("🧠 Step 1: Gemini is engineering the perfect prompt..."):
                    enhanced_prompt = enhance_prompt_with_gemini(product_name, brand_colors, vibe)
                    st.session_state.current_enhanced_prompt = enhanced_prompt
                
                with st.spinner(f"🎨 Step 2: SDXL is rendering your {format_choice} image..."):
                    result = generate_brand_image(enhanced_prompt, w, h, cfg_scale)
                    
                    if isinstance(result, str) and (result.startswith("Error") or result.startswith("Exception")):
                        st.error(f"🚨 API Issue: {result}")
                    else:
                        st.session_state.current_image = result
                        st.session_state.image_history.insert(0, {
                            "product": product_name,
                            "format": format_choice,
                            "image": result,
                            "prompt": enhanced_prompt
                        })

        if st.session_state.current_image:
            st.success("✅ Multi-Model Render Complete!")
            
            # Show the user what Gemini secretly wrote for them!
            with st.expander("👁️ View the Gemini-Enhanced Prompt"):
                st.write(st.session_state.current_enhanced_prompt)
            
            st.image(st.session_state.current_image, use_container_width=True)
            
            st.divider()
            buf = io.BytesIO()
            st.session_state.current_image.save(buf, format="PNG")
            
            st.download_button(
                label="📥 Download High-Res Ad",
                data=buf.getvalue(),
                file_name=f"brand_ad_{product_name.replace(' ', '_')}.png",
                mime="image/png"
            )
        else:
            st.markdown("<p style='color: #bfa6e8; margin-top: 50px;'>Your generated advertisement will appear here...</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='glowing-card' style='background-color: #ffffff; border: 1px solid #f0e6fc;'><h2>Current Session History</h2>", unsafe_allow_html=True)
    
    if not st.session_state.image_history:
        st.info("No images generated yet.")
    else:
        for i, record in enumerate(st.session_state.image_history):
            with st.expander(f"🖼️ {record['product']} | {record['format']}"):
                st.caption(f"**Prompt Used:** {record['prompt']}")
                st.image(record['image'], use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from PIL import Image
from io import BytesIO

# Set wide layout for responsiveness
st.set_page_config(layout="wide", page_title="Gemini AI Image Generator", page_icon="🎨")

# --- UI Title ---
st.title("🎨 Google Gemini AI Image Generator")

# --- App Instructions ---
st.markdown("""
---
🧠 **Before You Use the App**  
To generate images with Google Gemini AI, you need to provide your own Google AI Studio API key.

👉 [Get your free Google AI Studio API key here](https://google.com)
---
""")

# --- API Key Input ---
api_key = st.text_input("🔐 Enter your Google API Key", type="password")
if not api_key:
    st.warning("Please enter your API key to continue.")
    st.stop()

# --- Configure Client ---
try:
    client = genai.Client(api_key=api_key)  
except Exception as e:
    st.error(f"❌ Failed to authenticate with API key: {e}")
    st.stop()

# --- Layout with columns ---
col1, col2 = st.columns([3, 1])

with col1:
    prompt = st.text_area("📝 Enter your image prompt here", height=150, placeholder="A high-tech cyberpunk city at sunset with neon reflections...")

with col2:
    with st.expander("🎨 Options", expanded=True):
        tier = st.radio("API Account Tier", ["Free Tier (Generative)", "Paid Tier (Premium Imagen)"])
        
        style = st.selectbox(
            "Artistic Style",
            ["Any", "Photorealistic", "Pixel Art", "Vector Art", "3D Render", "Isometric",
             "Cartoon", "Fantasy Art", "Cyberpunk", "Steampunk", "Watercolor", "Oil Painting",
             "Concept Art", "Low Poly", "Line Art", "Ink Drawing", "Pencil Drawing",
             "Minimalist", "Surrealism", "Abstract", "Neon Glow", "Flat Design"]
        )

        aspect = st.selectbox(
            "Aspect Ratio",
            ["Any", "Square (1:1)", "Portrait (9:16)", "Landscape (16:9)"]
        )

        img_format = st.selectbox("Output Format", ["PNG", "JPEG"])

# --- Map User Selections to SDK Parameters ---
aspect_ratio_map = {
    "Any": "1:1",
    "Square (1:1)": "1:1",
    "Portrait (9:16)": "9:16",
    "Landscape (16:9)": "16:9"
}
sdk_aspect_ratio = aspect_ratio_map.get(aspect, "1:1")

# --- Construct Style Hints ---
style_hint = f"in {style} style" if style != "Any" else ""

# --- Generate Image Action ---
if st.button("🚀 Generate Image", use_container_width=True):
    if not prompt.strip():
        st.warning("⚠️ Please enter a prompt.")
    else:
        MAX_RETRIES = 2
        COOLDOWN_SECONDS = 26
        attempt = 0
        success = False

        while attempt <= MAX_RETRIES and not success:
            with st.spinner("Generating image..." if attempt == 0 else f"Retrying generation (Attempt {attempt+1}/{MAX_RETRIES+1})..."):
                try:
                    if tier == "Free Tier (Generative)":
                        free_tier_prompt = f"Return an IMAGE part only showing exactly: {prompt.strip()}. {style_hint}. DO NOT return any text explanations."
                        
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[free_tier_prompt],
                            config=types.GenerateContentConfig(
                                response_modalities=["IMAGE"]
                            )
                        )
                        
                        found_image = False
                        if response.candidates and response.candidates.content.parts:
                            for part in response.candidates.content.parts:
                                if part.inline_data:
                                    image = Image.open(BytesIO(part.inline_data.data))
                                    st.image(image, caption="🖼 Generated Image (Free Tier)", use_container_width=True)
                                    
                                    img_bytes = BytesIO()
                                    file_format = "JPEG" if img_format.upper() == "JPG" else img_format.upper()
                                    image.save(img_bytes, format=file_format)
                                    img_bytes.seek(0)

                                    st.download_button(
                                        label="⬇️ Download Image",
                                        data=img_bytes,
                                        file_name=f"gemini_image.{img_format.lower()}",
                                        mime=f"image/{img_format.lower()}",
                                        key=f"dl_free_{time.time()}"
                                    )
                                    st.success("✅ Image generated successfully via Free Tier!")
                                    found_image = True
                                    success = True
                                    break
                                
                                elif part.text:
                                    st.error("⚠️ **The Free AI Model returned text instead of a picture.**")
                                    st.info(f"**AI Response:** {part.text}\n\n*Tip: Try rephrasing your prompt to be simpler, or choose concrete objects rather than abstract feelings.*")
                                    found_image = True
                                    success = True  
                                    break

                        if not found_image:
                            st.error("❌ The free image model did not return any readable data. Please adjust your prompt context.")
                            break 
                    
                    else:
                        full_paid_prompt = f"{prompt.strip()}, {style_hint}".strip(", ")
                        result = client.models.generate_images(
                            model="imagen-3.0-generate-002",
                            prompt=full_paid_prompt,
                            config=types.GenerateImagesConfig(
                                number_of_images=1,
                                aspect_ratio=sdk_aspect_ratio,
                                output_mime_type=f"image/{img_format.lower()}",
                            )
                        )

                        found_image = False
                        if result.generated_images:
                            for gen_img in result.generated_images:
                                image = Image.open(BytesIO(gen_img.image.image_bytes))
                                st.image(image, caption="🖼 Generated Image (Premium Tier)", use_container_width=True)

                                img_bytes = BytesIO()
                                file_format = "JPEG" if img_format.upper() == "JPG" else img_format.upper()
                                image.save(img_bytes, format=file_format)
                                img_bytes.seek(0)

                                st.download_button(
                                    label="⬇️ Download Image",
                                    data=img_bytes,
                                    file_name=f"gemini_image.{img_format.lower()}",
                                    mime=f"image/{img_format.lower()}",
                                    key=f"dl_paid_{time.time()}"
                                )

                                st.success("✅ Premium Image generated successfully!")
                                found_image = True
                                success = True

                        if not found_image:
                            st.error("❌ No image payload found. Try a simpler or clearer description.")
                            break
                            
                except APIError as api_err:
                    if api_err.code == 429:
                        if "limit: 0" in str(api_err.message) or "quota" in str(api_err.message).lower():
                            st.error("🚫 **Daily Free Quota Fully Exhausted!**")
                            st.info("Google has paused this free key's rate limits for the day. To resolve this, create a **completely new API Key inside a new project** in Google AI Studio, or enable billing on your Google account.")
                            break
                        
                        elif attempt < MAX_RETRIES:
                            attempt += 1
                            cooldown_message = st.warning(f"⏳ **Rate Limit Exceeded (429)**. Cooldown triggered. Automatically retrying in {COOLDOWN_SECONDS} seconds...")
                            countdown_progress = st.progress(1.0)
                            
                            for remaining in range(COOLDOWN_SECONDS, 0, -1):
                                cooldown_message.warning(f"⏳ **Rate Limit Exceeded (429)**. Shared free servers are busy. Automatically retrying in **{remaining}** seconds...")
                                countdown_progress.progress(remaining / COOLDOWN_SECONDS)
                                time.sleep(1)
                                
                            cooldown_message.empty()
                            countdown_progress.empty()
                        else:
                            st.error("❌ Tried to generate multiple times, but the free tier servers remain busy. Please try again in a moment.")
                            break
                    else:
                        st.error(f"❌ Google API Error ({api_err.code}): {api_err.message}")
                        break
                except Exception as e:
                    st.error(f"❌ Unexpected Script Error: {e}")
                    break

# --- Prompt Tips ---
st.markdown("---")
st.markdown("""
### 💡 Prompt Writing Tips
Be descriptive and include:
- **Subjects & Actions**: What is happening in the scene?
- **Atmosphere**: Lighting (e.g., *cinematic light*, *golden hour*), mood, and color palette.
- **Composition**: Camera perspective (e.g., *macro closeup*, *aerial landscape photography*).
""")

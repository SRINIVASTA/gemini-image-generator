import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# Set wide layout for responsiveness
st.set_page_config(layout="wide")

# --- UI Title ---
st.title("🎨 Google Gemini AI Image Generator")

# --- App Instructions ---
st.markdown("""
---

🧠 **Before You Use the App**  
To generate images with Google Gemini AI, you'll need to provide your own API key. This keeps your usage secure and personalized.

🔐 **Required API Key:**  
`GOOGLE_API_KEY` → used to access Google Gemini AI

👉 [Get your API key here](https://lnkd.in/gYwg2sTJ)

---
""")


# --- API Key Input ---
api_key = st.text_input("🔐 Enter your Google API Key", type="password")
if not api_key:
    st.warning("Please enter your API key to continue.")
    st.stop()

# --- Configure Client ---
try:
    # The new genai package expects setting the env variable or alternative auth
    # If your genai version supports configure, uncomment the next line:
    # genai.configure(api_key=api_key)
    client = genai.Client(api_key=api_key)  # Pass API key directly to Client if supported
except Exception as e:
    st.error(f"❌ Failed to authenticate with API key: {e}")
    st.stop()

# --- Layout with columns ---
col1, col2 = st.columns([3, 1])

with col1:
    prompt = st.text_area("📝 Enter your image prompt here", height=150)

with col2:
    with st.expander("🎨 Options"):
        style = st.selectbox(
            "Choose Artistic Style",
            ["Any", "Photorealistic", "Pixel Art", "Vector Art", "3D Render", "Isometric",
             "Cartoon", "Fantasy Art", "Cyberpunk", "Steampunk", "Watercolor", "Oil Painting",
             "Concept Art", "Low Poly", "Line Art", "Ink Drawing", "Pencil Drawing",
             "Minimalist", "Surrealism", "Abstract", "Neon Glow", "Flat Design"]
        )

        aspect = st.selectbox(
            "Choose Aspect Ratio Hint",
            ["Any", "Square (1:1)", "Portrait (9:16)", "Landscape (16:9)"]
        )

        img_format = st.selectbox("Choose Output Format", ["PNG", "JPEG"])

# --- Construct Final Prompt ---
style_hint = f"in {style} style" if style != "Any" else ""
aspect_hint = f"aspect ratio {aspect}" if aspect != "Any" else ""
full_prompt = f"{prompt.strip()}, {style_hint}, {aspect_hint}".strip(", ")

# --- Generate Image ---
if st.button("🚀 Generate Image"):
    if not prompt.strip():
        st.warning("⚠️ Please enter a prompt.")
    else:
        with st.spinner("Generating image..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp-image-generation",
                    contents=[full_prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=['TEXT', 'IMAGE']
                    )
                )

                found_image = False
                for part in response.candidates[0].content.parts:
                    if part.text:
                        st.write(part.text)
                    elif part.inline_data:
                        image = Image.open(BytesIO(part.inline_data.data))
                        st.image(image, caption="🖼 Generated Image", use_container_width=True)

                        # Save image for download
                        img_bytes = BytesIO()
                        file_format = img_format.upper()
                        if file_format == "JPG":
                            file_format = "JPEG"
                        image.save(img_bytes, format=file_format)
                        img_bytes.seek(0)

                        st.download_button(
                            label="⬇️ Download Image",
                            data=img_bytes,
                            file_name=f"gemini_image.{img_format.lower()}",
                            mime=f"image/{img_format.lower()}"
                        )

                        st.success("✅ Image generated successfully!")
                        found_image = True

                if not found_image:
                    st.error("❌ No image found. Try a simpler or clearer prompt.")
            except Exception as e:
                st.error(f"❌ Error during image generation: {e}")

# --- Prompt Tips ---
st.markdown("---")
st.markdown("""
### 💡 Prompt Writing Tips

Be descriptive and include:
- **Subjects**, **actions**, **colors**, **style**, **mood**, **lighting**, **composition**

**Examples**:
- "A majestic dragon flying over snow-capped mountains, fantasy art style" - without option
- "A cozy coffee shop at sunset, watercolor painting, warm light" - without option
- "A cozy coffee shop at sunset, warm light" - with option


---

**Style Options:** Pixel Art, 3D Render, Oil Painting, etc.  
**Aspect Ratios:** Square, Portrait, Landscape  
**Formats:** PNG or JPEG

*These are just hints to the AI. Results may vary.*
""")

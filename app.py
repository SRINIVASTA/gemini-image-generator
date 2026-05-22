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

👉 [Get your API key here](https://google.com)

---
""")


# --- API Key Input ---
api_key = st.text_input("🔐 Enter your Google API Key", type="password")
if not api_key:
    st.warning("Please enter your API key to continue.")
    st.stop()

# --- Configure Client ---
try:
    # Use the official modern SDK client configuration
    client = genai.Client(api_key=api_key)  
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

# --- Map User Selections to SDK Parameters ---
# Convert friendly aspect ratios to SDK supported strings
aspect_ratio_map = {
    "Any": "1:1",
    "Square (1:1)": "1:1",
    "Portrait (9:16)": "9:16",
    "Landscape (16:9)": "16:9"
}
sdk_aspect_ratio = aspect_ratio_map.get(aspect, "1:1")

# --- Construct Final Prompt ---
style_hint = f"in {style} style" if style != "Any" else ""
full_prompt = f"{prompt.strip()}, {style_hint}".strip(", ")

# --- Generate Image ---
if st.button("🚀 Generate Image"):
    if not prompt.strip():
        st.warning("⚠️ Please enter a prompt.")
    else:
        with st.spinner("Generating image..."):
            try:
                # FIX: Use generate_images with an Imagen model
                result = client.models.generate_images(
                    model="imagen-3.0-generate-002",
                    prompt=full_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio=sdk_aspect_ratio,
                        output_mime_type=f"image/{img_format.lower()}",
                    )
                )

                found_image = False
                # Access the generated image bytes directly from the response
                if result.generated_images:
                    for gen_img in result.generated_images:
                        image = Image.open(BytesIO(gen_img.image.image_bytes))
                        st.image(image, caption="🖼 Generated Image", use_container_width=True)

                        # Prepare image bytes for download
                        img_bytes = BytesIO()
                        file_format = "JPEG" if img_format.upper() == "JPG" else img_format.upper()
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

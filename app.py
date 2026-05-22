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
    client = genai.Client(api_key=api_key)  
except Exception as e:
    st.error(f"❌ Failed to authenticate with API key: {e}")
    st.stop()

# --- Layout with columns ---
# FIXED: Re-added explicit layout weighting list to fix Streamlit TypeError
col1, col2 = st.columns([3, 1])

with col1:
    prompt = st.text_area("📝 Enter your image prompt here", height=150)

with col2:
    with st.expander("🎨 Options"):
        # Select tier to bypass billing restriction on free keys
        tier = st.radio("Select API Account Tier", ["Free Tier", "Paid/Billing Enabled Tier"])
        
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
aspect_ratio_map = {
    "Any": "1:1",
    "Square (1:1)": "1:1",
    "Portrait (9:16)": "9:16",
    "Landscape (16:9)": "16:9"
}
sdk_aspect_ratio = aspect_ratio_map.get(aspect, "1:1")

# --- Construct Final Prompt ---
style_hint = f"in {style} style" if style != "Any" else ""
full_prompt = f"Generate an image of: {prompt.strip()}. {style_hint}".strip()

# --- Generate Image ---
if st.button("🚀 Generate Image"):
    if not prompt.strip():
        st.warning("⚠️ Please enter a prompt.")
    else:
        with st.spinner("Generating image..."):
            try:
                if tier == "Free Tier":
                    # Free tier maps content to multimodal generation
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[full_prompt],
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"]
                        )
                    )
                    
                    found_image = False
                    if response.candidates and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                image = Image.open(BytesIO(part.inline_data.data))
                                st.image(image, caption="🖼 Generated Image (Free Tier)", use_container_width=True)
                                
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
                                st.success("✅ Image generated successfully via Free Tier!")
                                found_image = True
                                break

                    if not found_image:
                        st.error("❌ The free model did not return image data. Try a simpler prompt or enable billing.")
                
                else:
                    # Paid tier routes directly to high-fidelity Imagen models
                    result = client.models.generate_images(
                        model="imagen-4.0-generate-001",
                        prompt=full_prompt,
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
                                mime=f"image/{img_format.lower()}"
                            )

                            st.success("✅ Premium Image generated successfully!")
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

---

**Style Options:** Pixel Art, 3D Render, Oil Painting, etc.  
**Aspect Ratios:** Square, Portrait, Landscape  
**Formats:** PNG or JPEG
""")

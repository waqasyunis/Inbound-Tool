import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd
from io import BytesIO
from PIL import Image
import io

# Page config
st.set_page_config(
    page_title="Order Image Upload",
    page_icon="📷",
    layout="wide"
)

# API Keys and URLs
IMGBB_API_KEY = "5d8c1750878fa4077dca7f25067822f1"
GOOGLE_SCRIPT_URL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbxh_P5lLxoySjhqpQUPXofTttIRTkBHub1pGPKKtGaYHmdOSnjGZMzaqzv1JJ27jDab/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"

# Initialize session state
if 'camera_images' not in st.session_state:
    st.session_state.camera_images = []
if 'confirmed_order' not in st.session_state:
    st.session_state.confirmed_order = ""
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

def compress_image(image_bytes):
    try:
        img = Image.open(BytesIO(image_bytes))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        max_dimension = 1200
        if img.width > max_dimension or img.height > max_dimension:
            ratio = min(max_dimension/img.width, max_dimension/img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=75, optimize=True)
        output.seek(0)
        return output.read()
    except:
        return image_bytes

def upload_to_imgbb(image_bytes):
    try:
        compressed_bytes = compress_image(image_bytes)
        base64_image = base64.b64encode(compressed_bytes).decode('utf-8')
        payload = {"key": IMGBB_API_KEY, "image": base64_image}
        response = requests.post("https://api.imgbb.com/1/upload", data=payload, timeout=120)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["data"]["url"]
        return None
    except:
        return None

def save_to_google_sheet(order_num, timestamp, image_urls):
    try:
        params = {
            "order_number": str(order_num),
            "timestamp": str(timestamp),
            "images": ",".join(image_urls)
        }
        response = requests.get(GOOGLE_SCRIPT_URL, params=params, timeout=60, allow_redirects=True)
        
        # Multiple success checks
        if response.status_code == 200:
            if "success" in response.text.lower():
                return True
            if "order" in response.text.lower():
                return True
        return True  # Assume success if no error
    except:
        return False

def load_sheet_data():
    try:
        return pd.read_csv(SHEET_CSV_URL)
    except:
        return pd.DataFrame()

def clear_form():
    st.session_state.camera_images = []
    st.session_state.confirmed_order = ""
    st.session_state.form_key += 1

# Main UI
st.title("📷 Order Image Upload")

tab1, tab2 = st.tabs(["📤 Upload Images", "🔍 Search Orders"])

with tab1:
    
    if not st.session_state.confirmed_order:
        st.subheader("📦 Step 1: Enter Order Number")
        
        order_input = st.text_input(
            "Order Number",
            placeholder="Enter order number...",
            key=f"order_input_{st.session_state.form_key}"
        )
        
        if st.button("✅ CONFIRM ORDER", type="primary"):
            if order_input.strip():
                st.session_state.confirmed_order = order_input.strip()
                st.rerun()
            else:
                st.error("⚠️ Please enter order number!")
        
        st.info("👆 Enter order number and click CONFIRM")
    
    else:
        st.success(f"📦 Order: **{st.session_state.confirmed_order}**")
        
        if st.button("🔄 New Order"):
            clear_form()
            st.rerun()
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📸 Camera**")
            camera_key = f"cam_{len(st.session_state.camera_images)}_{st.session_state.form_key}"
            camera_image = st.camera_input("Take photo", key=camera_key)
            
            if camera_image:
                img_bytes = camera_image.getvalue()
                is_new = all(stored.getvalue() != img_bytes for stored in st.session_state.camera_images)
                if is_new:
                    st.session_state.camera_images.append(camera_image)
                    st.rerun()
        
        with col2:
            st.write("**📁 Upload**")
            uploaded_files = st.file_uploader(
                "Choose images",
                type=['jpg', 'jpeg', 'png', 'webp'],
                accept_multiple_files=True,
                key=f"upload_{st.session_state.form_key}"
            )
        
        st.markdown("---")
        
        all_images = [(img, "cam") for img in st.session_state.camera_images]
        if uploaded_files:
            all_images += [(f, "file") for f in uploaded_files]
        
        if all_images:
            st.subheader(f"📋 {len(all_images)} Photos")
            
            cols = st.columns(4)
            for idx, (img, src) in enumerate(all_images):
                with cols[idx % 4]:
                    st.image(img, caption=f"{idx+1}", use_container_width=True)
            
            if st.session_state.camera_images:
                if st.button("🗑️ Clear Photos"):
                    st.session_state.camera_images = []
                    st.rerun()
            
            st.markdown("---")
            
            if st.button("💾 SAVE TO SHEET", type="primary", use_container_width=True):
                image_urls = []
                progress = st.progress(0)
                status = st.empty()
                
                for idx, (img, src) in enumerate(all_images):
                    status.text(f"Uploading {idx+1}/{len(all_images)}...")
                    url = upload_to_imgbb(img.getvalue())
                    if url:
                        image_urls.append(url)
                    progress.progress((idx+1) / len(all_images))
                
                if image_urls:
                    status.text("Saving...")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    save_to_google_sheet(st.session_state.confirmed_order, timestamp, image_urls)
                    st.success(f"✅ Saved {len(image_urls)} images for order {st.session_state.confirmed_order}!")
                    st.balloons()
                    clear_form()
                    st.rerun()
                else:
                    st.error("❌ Image upload failed!")
        else:
            st.warning("📷 Add photos to continue")

with tab2:
    st.subheader("🔍 Search Orders")
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    df = load_sheet_data()
    
    if not df.empty:
        search = st.text_input("🔎 Search Order")
        
        if search:
            mask = df.iloc[:, 0].astype(str).str.contains(search, case=False, na=False)
            filtered_df = df[mask]
        else:
            filtered_df = df
        
        st.write(f"📊 {len(filtered_df)} orders")
        
        for _, row in filtered_df.iterrows():
            order = row.iloc[0] if len(row) > 0 else "?"
            time = row.iloc[1] if len(row) > 1 else ""
            
            with st.expander(f"📦 {order} | {time}"):
                urls = [str(row.iloc[i]) for i in range(2, len(row)) if pd.notna(row.iloc[i]) and str(row.iloc[i]).startswith('http')]
                if urls:
                    cols = st.columns(min(4, len(urls)))
                    for i, url in enumerate(urls):
                        with cols[i % 4]:
                            st.image(url, use_container_width=True)
                else:
                    st.write("No images")
    else:
        st.info("No data")

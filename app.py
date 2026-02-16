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
GOOGLE_SCRIPT_URL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbwZr2SZRYY4GA0T_vTSrIhyuR6RDKLdu_3jLteC468jHb6FlOmaBFa8ptc_8vE2Zdzz/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"

# Initialize session state
if 'camera_images' not in st.session_state:
    st.session_state.camera_images = []
if 'order_number' not in st.session_state:
    st.session_state.order_number = ""
if 'form_key' not in st.session_state:
    st.session_state.form_key = 0

def compress_image(image_bytes, max_size_kb=400):
    """Compress image if too large"""
    try:
        img = Image.open(BytesIO(image_bytes))
        
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        max_dimension = 1200
        if img.width > max_dimension or img.height > max_dimension:
            ratio = min(max_dimension/img.width, max_dimension/img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        quality = 75
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        
        output.seek(0)
        return output.read()
    except Exception as e:
        return image_bytes

def upload_to_imgbb(image_bytes):
    """Upload image to ImgBB and return URL"""
    try:
        compressed_bytes = compress_image(image_bytes)
        base64_image = base64.b64encode(compressed_bytes).decode('utf-8')
        
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64_image
        }
        
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["data"]["url"]
        return None
            
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def save_to_google_sheet(order_num, timestamp, image_urls):
    """Save order data to Google Sheet"""
    try:
        params = {
            "order_number": order_num,
            "timestamp": timestamp,
            "images": ",".join(image_urls)
        }
        
        response = requests.get(GOOGLE_SCRIPT_URL, params=params, timeout=30)
        
        if "success" in response.text.lower():
            return True
        return False
            
    except Exception as e:
        st.error(f"Sheet save error: {str(e)}")
        return False

def load_sheet_data():
    """Load data from Google Sheet"""
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except:
        return pd.DataFrame()

def clear_form():
    """Clear entire form"""
    st.session_state.camera_images = []
    st.session_state.order_number = ""
    st.session_state.form_key += 1

# Main UI
st.title("📷 Order Image Upload")

tab1, tab2 = st.tabs(["📤 Upload Images", "🔍 Search Orders"])

with tab1:
    # Clear Form button at top
    col_clear, col_space = st.columns([1, 4])
    with col_clear:
        if st.button("🔄 NEW ORDER", type="secondary"):
            clear_form()
            st.rerun()
    
    # Order number input with dynamic key
    order_number = st.text_input(
        "📦 Order Number", 
        value=st.session_state.order_number,
        placeholder="Enter order number...",
        key=f"order_input_{st.session_state.form_key}"
    )
    
    # Update session state
    st.session_state.order_number = order_number
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📸 Camera")
        
        camera_key = f"camera_{len(st.session_state.camera_images)}_{st.session_state.form_key}"
        camera_image = st.camera_input("Take photo", key=camera_key)
        
        if camera_image:
            img_bytes = camera_image.getvalue()
            is_new = True
            for stored in st.session_state.camera_images:
                if stored.getvalue() == img_bytes:
                    is_new = False
                    break
            
            if is_new:
                st.session_state.camera_images.append(camera_image)
                st.rerun()
    
    with col2:
        st.subheader("📁 File Upload")
        uploaded_files = st.file_uploader(
            "Choose images",
            type=['jpg', 'jpeg', 'png', 'webp'],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state.form_key}"
        )
    
    st.markdown("---")
    
    # Combine all images
    all_images = []
    
    for img in st.session_state.camera_images:
        all_images.append(("camera", img))
    
    if uploaded_files:
        for f in uploaded_files:
            all_images.append(("file", f))
    
    # Display preview
    if all_images:
        st.subheader(f"📋 Preview ({len(all_images)} images)")
        
        cols = st.columns(4)
        for idx, (source, img) in enumerate(all_images):
            with cols[idx % 4]:
                st.image(img, caption=f"{'📸' if source == 'camera' else '📁'} {idx + 1}", use_container_width=True)
        
        if st.session_state.camera_images:
            if st.button("🗑️ Clear Camera Photos"):
                st.session_state.camera_images = []
                st.rerun()
    
    st.markdown("---")
    
    # Save button
    if st.button("💾 SAVE TO SHEET", type="primary", use_container_width=True):
        if not order_number.strip():
            st.error("⚠️ Please enter an order number!")
        elif not all_images:
            st.error("⚠️ Please add at least one image!")
        else:
            image_urls = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, (source, img) in enumerate(all_images):
                status_text.text(f"Uploading image {idx + 1} of {len(all_images)}...")
                
                img_bytes = img.getvalue() if hasattr(img, 'getvalue') else img.read()
                url = upload_to_imgbb(img_bytes)
                
                if url:
                    image_urls.append(url)
                progress_bar.progress((idx + 1) / len(all_images))
            
            if image_urls:
                status_text.text("Saving to Google Sheet...")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if save_to_google_sheet(order_number.strip(), timestamp, image_urls):
                    st.success(f"✅ Successfully saved {len(image_urls)} images for order {order_number}!")
                    st.balloons()
                    
                    # Clear form after successful save
                    clear_form()
                    st.rerun()
                else:
                    st.error("❌ Failed to save to Google Sheet!")
            else:
                st.error("❌ Upload failed! No images were uploaded successfully.")

with tab2:
    st.subheader("🔍 Search Orders")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    df = load_sheet_data()
    
    if not df.empty:
        search_term = st.text_input("🔎 Search by Order Number", placeholder="Enter order number to search...")
        
        if search_term:
            mask = df.iloc[:, 0].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = df[mask]
        else:
            filtered_df = df
        
        st.write(f"📊 Found {len(filtered_df)} orders")
        
        for idx, row in filtered_df.iterrows():
            order_num = row.iloc[0] if len(row) > 0 else "Unknown"
            timestamp = row.iloc[1] if len(row) > 1 else ""
            
            with st.expander(f"📦 Order: {order_num} | 🕐 {timestamp}"):
                image_urls = [str(row.iloc[i]) for i in range(2, len(row)) if pd.notna(row.iloc[i]) and str(row.iloc[i]).startswith('http')]
                
                if image_urls:
                    cols = st.columns(min(4, len(image_urls)))
                    for i, url in enumerate(image_urls):
                        with cols[i % 4]:
                            st.image(url, caption=f"Image {i+1}", use_container_width=True)
                else:
                    st.write("No images found")
    else:
        st.info("No data found in sheet")

import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd

IMGBB_API_KEY = "5d8c1750878fa4077dca7f25067822f1"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/edit"
GOOGLE_SCRIPT_URL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbxr8ln0ybYa1jMYARnhEybCH4EvXV46CplDA-zVoqVRoAJGTxwGZr5-FsLEv5elsClT/exec"

st.set_page_config(page_title="Order Image Tool", page_icon="📸", layout="centered")

if 'camera_images' not in st.session_state:
    st.session_state.camera_images = []

if 'current_order' not in st.session_state:
    st.session_state.current_order = ""

def upload_to_imgbb(image_bytes):
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": IMGBB_API_KEY, "image": base64.b64encode(image_bytes).decode('utf-8')}
    try:
        response = requests.post(url, payload)
        if response.status_code == 200:
            return response.json()["data"]["url"]
        return None
    except:
        return None

def save_to_google_sheet(order_number, timestamp, image_urls):
    try:
        params = {
            "order_number": str(order_number),
            "timestamp": str(timestamp),
            "images": ",".join(image_urls)
        }
        
        response = requests.get(GOOGLE_SCRIPT_URL, params=params, timeout=30)
        
        if response.status_code == 200:
            try:
                result = response.json()
                return result.get('status') == 'success'
            except:
                return True
        return False
        
    except:
        return False

def load_sheet_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except:
        return pd.DataFrame()

def get_images_for_order(order_number):
    df = load_sheet_data()
    if df.empty:
        return []
    order_df = df[df['Order_Number'].astype(str) == str(order_number)]
    if order_df.empty:
        return []
    image_cols = [col for col in order_df.columns if col.startswith('Image_')]
    images = []
    for col in image_cols:
        val = order_df[col].values[0]
        if pd.notna(val) and str(val).strip():
            images.append(str(val).strip())
    return images

def clear_camera_images():
    st.session_state.camera_images = []

st.title("📸 Order Image Tool")
st.markdown("---")

tab1, tab2 = st.tabs(["📤 Upload Images", "🔍 Search Orders"])

with tab1:
    st.header("Upload Images")
    order_number = st.text_input("📦 Order Number", placeholder="Enter order number...")
    
    if order_number != st.session_state.current_order:
        st.session_state.current_order = order_number
        st.session_state.camera_images = []
    
    if order_number:
        st.success(f"Order: **{order_number}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📸 Camera (Multiple Photos)")
            
            if st.session_state.camera_images:
                st.info(f"📷 {len(st.session_state.camera_images)} photo(s) captured")
            
            camera_key = f"camera_{len(st.session_state.camera_images)}"
            camera_image = st.camera_input("Take photo", key=camera_key)
            
            if camera_image is not None:
                img_bytes = camera_image.getvalue()
                if not any(stored.getvalue() == img_bytes for stored in st.session_state.camera_images):
                    st.session_state.camera_images.append(camera_image)
                    st.rerun()
            
            if st.session_state.camera_images:
                if st.button("🗑️ Clear All Photos", type="secondary"):
                    clear_camera_images()
                    st.rerun()
        
        with col2:
            st.markdown("#### 📁 Upload Files")
            uploaded_files = st.file_uploader(
                "Choose images", 
                type=['png', 'jpg', 'jpeg'], 
                accept_multiple_files=True
            )
        
        all_images = []
        
        for img in st.session_state.camera_images:
            all_images.append(("camera", img))
        
        if uploaded_files:
            for file in uploaded_files:
                all_images.append(("upload", file))
        
        if all_images:
            st.markdown("### 👁️ Preview:")
            st.write(f"**Total: {len(all_images)}** (📷 {len(st.session_state.camera_images)} | 📁 {len(uploaded_files) if uploaded_files else 0})")
            
            cols = st.columns(min(len(all_images), 4))
            for idx, (source, img) in enumerate(all_images):
                with cols[idx % 4]:
                    icon = "📷" if source == "camera" else "📁"
                    st.image(img, caption=f"{icon} {idx+1}", use_container_width=True)
            
            if st.button("💾 SAVE TO SHEET", type="primary", use_container_width=True):
                with st.spinner("Uploading images..."):
                    progress_bar = st.progress(0)
                    uploaded_urls = []
                    total = len(all_images)
                    
                    for idx, (source, img) in enumerate(all_images):
                        img_bytes = img.getvalue()
                        url = upload_to_imgbb(img_bytes)
                        if url:
                            uploaded_urls.append(url)
                        progress_bar.progress((idx + 1) / total)
                    
                    if uploaded_urls:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        with st.spinner("Saving to Google Sheet..."):
                            success = save_to_google_sheet(order_number, timestamp, uploaded_urls)
                        
                        if success:
                            st.success(f"✅ {len(uploaded_urls)} images saved to Google Sheet!")
                            st.balloons()
                            
                            st.markdown("#### ✅ Saved Data:")
                            preview_data = {"Order_Number": [order_number], "Timestamp": [timestamp]}
                            for idx, url in enumerate(uploaded_urls):
                                preview_data[f"Image_{idx+1}"] = [url]
                            preview_df = pd.DataFrame(preview_data)
                            st.dataframe(preview_df, use_container_width=True)
                            
                            st.markdown(f"[📋 View Google Sheet]({GOOGLE_SHEET_URL})")
                            
                            st.session_state.camera_images = []
                        else:
                            st.error("❌ Failed to save to Google Sheet!")
                            st.info("Manual backup - copy this:")
                            copy_text = f"{order_number}\t{timestamp}"
                            for url in uploaded_urls:
                                copy_text += f"\t{url}"
                            st.code(copy_text, language=None)
                    else:
                        st.error("❌ Image upload failed!")
    else:
        st.warning("⚠️ Enter Order Number first")

with tab2:
    st.header("Search Order Images")
    search_order = st.text_input("🔍 Search Order Number", placeholder="Enter order to search...")
    
    if st.button("Search", type="primary"):
        if search_order:
            with st.spinner("Searching..."):
                images = get_images_for_order(search_order)
            if images:
                st.success(f"✅ Found {len(images)} images for Order #{search_order}")
                cols = st.columns(3)
                for idx, url in enumerate(images):
                    with cols[idx % 3]:
                        st.image(url, caption=f"Image {idx+1}", use_container_width=True)
            else:
                st.warning(f"⚠️ No images found for Order #{search_order}")
    
    st.markdown("---")
    if st.button("📊 Load All Orders"):
        with st.spinner("Loading..."):
            df = load_sheet_data()
        if not df.empty:
            image_cols = [col for col in df.columns if col.startswith('Image_')]
            if image_cols:
                df['Total_Images'] = df[image_cols].notna().sum(axis=1)
            else:
                df['Total_Images'] = 0
            summary = df[['Order_Number', 'Timestamp', 'Total_Images']].copy()
            summary.columns = ['Order_Number', 'Upload_Date', 'Total_Images']
            st.dataframe(summary, use_container_width=True)
        else:
            st.warning("No data found")

import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd

IMGBB_API_KEY = "5d8c1750878fa4077dca7f25067822f1"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/edit"
GOOGLE_SCRIPT_URL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbxr7XlctBd6fQLEkCe-8NBVO66UqzQjlqa3VAHUpGRkWth0ZcE0qCnCiLS_uw-j43Fx/exec"

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

def save_to_google_sheet(order_num, timestamp, image_urls):
    try:
        # Build URL with parameters
        full_url = f"{GOOGLE_SCRIPT_URL}?order_number={order_num}&timestamp={timestamp}&images={','.join(image_urls)}"
        
        response = requests.get(full_url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('status') == 'success'
        return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def load_sheet_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except:
        return pd.DataFrame()

def clear_camera_images():
    st.session_state.camera_images = []

st.title("📸 Order Image Tool")
st.markdown("---")

tab1, tab2 = st.tabs(["📤 Upload Images", "🔍 Search Orders"])

with tab1:
    st.header("Upload Images")
    order_input = st.text_input("📦 Order Number", placeholder="Enter order number...", key="order_input")
    
    if order_input != st.session_state.current_order:
        st.session_state.current_order = order_input
        st.session_state.camera_images = []
    
    if order_input:
        st.success(f"Order: **{order_input}**")
        
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
                # Get order number at time of clicking
                current_order = order_input
                
                st.info(f"Saving Order: **{current_order}**")
                
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
                            success = save_to_google_sheet(current_order, timestamp, uploaded_urls)
                        
                        if success:
                            st.success(f"✅ Order **{current_order}** - {len(uploaded_urls)} images saved!")
                            st.balloons()
                            
                            st.markdown(f"[📋 View Google Sheet]({GOOGLE_SHEET_URL})")
                            
                            st.session_state.camera_images = []
                        else:
                            st.error("❌ Failed to save to Google Sheet!")
                    else:
                        st.error("❌ Image upload failed!")
    else:
        st.warning("⚠️ Enter Order Number first")

with tab2:
    st.header("Search Order Images")
    search_order = st.text_input("🔍 Search Order Number", placeholder="Enter order to search...")
    
    if st.button("Search", type="primary"):
        if search_order:
            df = load_sheet_data()
            if not df.empty:
                order_df = df[df['Order_Number'].astype(str) == str(search_order)]
                if not order_df.empty:
                    st.success(f"✅ Found Order #{search_order}")
                    st.dataframe(order_df)
                else:
                    st.warning(f"⚠️ No data found for Order #{search_order}")
            else:
                st.warning("No data in sheet")
    
    st.markdown("---")
    if st.button("📊 Load All Orders"):
        df = load_sheet_data()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No data found")

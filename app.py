import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd
import urllib.parse

IMGBB_API_KEY = "5d8c1750878fa4077dca7f25067822f1"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/edit"
GOOGLE_SCRIPT_URL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbwZr2SZRYY4GA0T_vTSrIhyuR6RDKLdu_3jLteC468jHb6FlOmaBFa8ptc_8vE2Zdzz/exec"

st.set_page_config(page_title="Order Image Tool", page_icon="📸", layout="centered")

if 'camera_images' not in st.session_state:
    st.session_state.camera_images = []

if 'current_order' not in st.session_state:
    st.session_state.current_order = ""

def upload_to_imgbb(image_bytes):
    url = "https://api.imgbb.com/1/upload"
    try:
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            "key": IMGBB_API_KEY,
            "image": image_base64
        }
        response = requests.post(url, data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["data"]["url"]
        return None
    except:
        return None

def save_to_google_sheet(order_num, timestamp, image_urls):
    try:
        order_encoded = urllib.parse.quote(str(order_num))
        timestamp_encoded = urllib.parse.quote(str(timestamp))
        images_encoded = urllib.parse.quote(",".join(image_urls))
        
        full_url = f"{GOOGLE_SCRIPT_URL}?order_number={order_encoded}&timestamp={timestamp_encoded}&images={images_encoded}"
        
        response = requests.get(full_url, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
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
                current_order = order_input
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                uploaded_urls = []
                total = len(all_images)
                
                for idx, (source, img) in enumerate(all_images):
                    status_text.text(f"Uploading image {idx+1} of {total}...")
                    img_bytes = img.getvalue()
                    url = upload_to_imgbb(img_bytes)
                    if url:
                        uploaded_urls.append(url)
                    progress_bar.progress((idx + 1) / total)
                
                if uploaded_urls:
                    status_text.text("Saving to Google Sheet...")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    success = save_to_google_sheet(current_order, timestamp, uploaded_urls)
                    
                    status_text.empty()
                    st.success(f"✅ Order **{current_order}** - {len(uploaded_urls)} images saved!")
                    st.balloons()
                    st.markdown(f"[📋 View Google Sheet]({GOOGLE_SHEET_URL})")
                    st.session_state.camera_images = []
                else:
                    status_text.empty()
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

import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd

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
    try:
        url = "https://api.imgbb.com/1/upload"
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        payload = {"key": IMGBB_API_KEY, "image": image_base64}
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
        params = {
            "order_number": order_num,
            "timestamp": timestamp,
            "images": ",".join(image_urls)
        }
        response = requests.get(GOOGLE_SCRIPT_URL, params=params, timeout=30)
        return response.status_code == 200
    except:
        return False

def load_sheet_data():
    try:
        return pd.read_csv(SHEET_CSV_URL)
    except:
        return pd.DataFrame()

def clear_camera_images():
    st.session_state.camera_images = []

st.title("📸 Order Image Tool")
st.markdown("---")

tab1, tab2 = st.tabs(["📤 Upload Images", "🔍 Search Orders"])

with tab1:
    st.header("Upload Images")
    order_input = st.text_input("📦 Order Number", placeholder="Enter order number...")
    
    if order_input != st.session_state.current_order:
        st.session_state.current_order = order_input
        st.session_state.camera_images = []
    
    if order_input:
        st.success(f"Order: **{order_input}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📸 Camera")
            if st.session_state.camera_images:
                st.info(f"📷 {len(st.session_state.camera_images)} photo(s)")
            
            camera_image = st.camera_input("Take photo", key=f"cam_{len(st.session_state.camera_images)}")
            
            if camera_image:
                img_bytes = camera_image.getvalue()
                if not any(s.getvalue() == img_bytes for s in st.session_state.camera_images):
                    st.session_state.camera_images.append(camera_image)
                    st.rerun()
            
            if st.session_state.camera_images and st.button("🗑️ Clear Photos"):
                clear_camera_images()
                st.rerun()
        
        with col2:
            st.markdown("#### 📁 Upload")
            uploaded_files = st.file_uploader("Choose images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        all_images = [(img, "cam") for img in st.session_state.camera_images]
        if uploaded_files:
            all_images += [(f, "file") for f in uploaded_files]
        
        if all_images:
            st.markdown(f"### 👁️ Preview ({len(all_images)} images)")
            cols = st.columns(min(len(all_images), 4))
            for idx, (img, src) in enumerate(all_images):
                with cols[idx % 4]:
                    st.image(img, caption=f"{'📷' if src == 'cam' else '📁'} {idx+1}", use_container_width=True)
            
            if st.button("💾 SAVE TO SHEET", type="primary", use_container_width=True):
                progress = st.progress(0)
                urls = []
                
                for idx, (img, _) in enumerate(all_images):
                    url = upload_to_imgbb(img.getvalue())
                    if url:
                        urls.append(url)
                    progress.progress((idx + 1) / len(all_images))
                
                if urls:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_to_google_sheet(order_input, timestamp, urls)
                    st.success(f"✅ Order **{order_input}** - {len(urls)} images saved!")
                    st.balloons()
                    st.markdown(f"[📋 View Sheet]({GOOGLE_SHEET_URL})")
                    st.session_state.camera_images = []
                else:
                    st.error("❌ Upload failed!")
    else:
        st.warning("⚠️ Enter Order Number first")

with tab2:
    st.header("Search Orders")
    search = st.text_input("🔍 Order Number", placeholder="Search...")
    
    if st.button("Search", type="primary") and search:
        df = load_sheet_data()
        if not df.empty:
            result = df[df['Order_Number'].astype(str) == search]
            if not result.empty:
                st.success(f"✅ Found Order #{search}")
                st.dataframe(result)
            else:
                st.warning("⚠️ Not found")
    
    if st.button("📊 All Orders"):
        df = load_sheet_data()
        if not df.empty:
            st.dataframe(df)

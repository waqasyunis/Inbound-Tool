import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd

IMGBB_API_KEY = "5d8c1750878fa4077dca7f25067822f1"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/edit"

st.set_page_config(page_title="Order Image Tool", page_icon="📸", layout="centered")

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
    return order_df['Image_URL'].tolist()

st.title("📸 Order Image Tool")
st.markdown("---")

tab1, tab2 = st.tabs(["📤 Upload Images", "🔍 Search Orders"])

with tab1:
    st.header("Upload Images")
    order_number = st.text_input("📦 Order Number", placeholder="Enter order number...")
    
    if order_number:
        st.success(f"Order: **{order_number}**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📸 Camera")
            camera_image = st.camera_input("Take photo")
        with col2:
            st.markdown("#### 📁 Upload")
            uploaded_files = st.file_uploader("Choose images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        all_images = []
        if camera_image:
            all_images.append(camera_image)
        if uploaded_files:
            for file in uploaded_files:
                all_images.append(file)
        
        if all_images:
            st.markdown("### 👁️ Preview:")
            cols = st.columns(min(len(all_images), 4))
            for idx, img in enumerate(all_images):
                with cols[idx % 4]:
                    st.image(img, caption=f"Image {idx+1}", use_container_width=True)
            
            if st.button("💾 SAVE ALL IMAGES", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                uploaded_urls = []
                total = len(all_images)
                for idx, img in enumerate(all_images):
                    img_bytes = img.getvalue()
                    url = upload_to_imgbb(img_bytes)
                    if url:
                        uploaded_urls.append(url)
                    progress_bar.progress((idx + 1) / total)
                
                if uploaded_urls:
                    st.success(f"✅ {len(uploaded_urls)} images uploaded!")
                    st.markdown(f"### [📋 Open Google Sheet]({GOOGLE_SHEET_URL})")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.markdown("### 📝 Copy & Paste in Sheet:")
                    copy_text = ""
                    for idx, url in enumerate(uploaded_urls):
                        copy_text += f"{order_number}\t{timestamp}\t{url}\t{idx+1}\n"
                    st.code(copy_text, language=None)
                    st.info("👆 Copy this and paste in Google Sheet!")
                else:
                    st.error("❌ Upload failed!")
    else:
        st.warning("⚠️ Enter Order Number first")

with tab2:
    st.header("Search Order Images")
    search_order = st.text_input("🔍 Search Order Number", placeholder="Enter order to search...")
    
    if st.button("Search", type="primary"):
        if search_order:
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
        df = load_sheet_data()
        if not df.empty:
            summary = df.groupby('Order_Number').agg({'Image_URL': 'count', 'Timestamp': 'first'}).reset_index()
            summary.columns = ['Order_Number', 'Total_Images', 'Upload_Date']
            st.dataframe(summary, use_container_width=True)

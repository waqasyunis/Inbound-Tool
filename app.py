import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd
from io import BytesIO
from PIL import Image
import io

st.set_page_config(page_title="Order Image Upload", page_icon="📷", layout="wide")

IMGBB_API_KEY = "5d8c1750878fa4077dca7f25067822f1"
GOOGLE_SCRIPT_URL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbxh_P5lLxoySjhqpQUPXofTttIRTkBHub1pGPKKtGaYHmdOSnjGZMzaqzv1JJ27jDab/exec"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"

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
        if img.width > 1200 or img.height > 1200:
            ratio = min(1200/img.width, 1200/img.height)
            img = img.resize((int(img.width*ratio), int(img.height*ratio)), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=70)
        output.seek(0)
        return output.read()
    except:
        return image_bytes

def upload_to_imgbb(image_bytes):
    try:
        compressed = compress_image(image_bytes)
        b64 = base64.b64encode(compressed).decode('utf-8')
        
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": b64},
            timeout=120
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                return data["data"]["url"]
        return None
    except:
        return None

def save_to_sheet(order_num, timestamp, image_urls):
    try:
        params = {
            "order_number": order_num,
            "timestamp": timestamp,
            "images": ",".join(image_urls)
        }
        resp = requests.get(GOOGLE_SCRIPT_URL, params=params, timeout=60)
        return resp.status_code == 200
    except:
        return False

def clear_form():
    st.session_state.camera_images = []
    st.session_state.confirmed_order = ""
    st.session_state.form_key += 1

st.title("📷 Order Image Upload")

tab1, tab2 = st.tabs(["📤 Upload", "🔍 Search"])

with tab1:
    if not st.session_state.confirmed_order:
        st.subheader("📦 Enter Order Number")
        order_input = st.text_input("Order Number", placeholder="e.g. 101090_20", key=f"order_{st.session_state.form_key}")
        
        if st.button("✅ CONFIRM ORDER", type="primary"):
            if order_input.strip():
                st.session_state.confirmed_order = order_input.strip()
                st.rerun()
            else:
                st.error("⚠️ Enter order number first!")
    
    else:
        st.success(f"📦 Order: **{st.session_state.confirmed_order}**")
        
        if st.button("🔄 New Order"):
            clear_form()
            st.rerun()
        
        st.markdown("---")
        st.subheader("📸 Add Photos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cam_key = f"cam_{len(st.session_state.camera_images)}_{st.session_state.form_key}"
            cam_img = st.camera_input("Take Photo", key=cam_key)
            
            if cam_img:
                img_bytes = cam_img.getvalue()
                is_new = all(s.getvalue() != img_bytes for s in st.session_state.camera_images)
                if is_new:
                    st.session_state.camera_images.append(cam_img)
                    st.rerun()
        
        with col2:
            files = st.file_uploader(
                "Or Upload Files",
                type=['jpg', 'jpeg', 'png'],
                accept_multiple_files=True,
                key=f"up_{st.session_state.form_key}"
            )
        
        # Combine all images
        all_imgs = list(st.session_state.camera_images)
        if files:
            all_imgs.extend(files)
        
        if all_imgs:
            st.markdown("---")
            st.subheader(f"📋 {len(all_imgs)} Photos Ready")
            
            cols = st.columns(4)
            for i, img in enumerate(all_imgs):
                with cols[i % 4]:
                    st.image(img, caption=f"Photo {i+1}", use_container_width=True)
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.session_state.camera_images:
                    if st.button("🗑️ Clear Camera Photos"):
                        st.session_state.camera_images = []
                        st.rerun()
            
            st.markdown("---")
            
            if st.button("💾 SAVE TO SHEET", type="primary", use_container_width=True):
                uploaded_urls = []
                progress = st.progress(0)
                status = st.empty()
                
                total = len(all_imgs)
                
                for i, img in enumerate(all_imgs):
                    status.text(f"⏳ Uploading photo {i+1} of {total}...")
                    
                    url = upload_to_imgbb(img.getvalue())
                    
                    if url:
                        uploaded_urls.append(url)
                    
                    progress.progress((i + 1) / total)
                
                if uploaded_urls:
                    status.text("💾 Saving to Google Sheet...")
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    order = st.session_state.confirmed_order
                    
                    if save_to_sheet(order, timestamp, uploaded_urls):
                        st.success(f"✅ Done! Saved {len(uploaded_urls)} photos for order **{order}**")
                        st.balloons()
                        
                        # Auto clear after 2 seconds
                        clear_form()
                        st.rerun()
                    else:
                        st.error("❌ Failed to save to sheet!")
                else:
                    st.error("❌ Failed to upload images!")
        
        else:
            st.info("👆 Take photos or upload files")

with tab2:
    st.subheader("🔍 Search Orders")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        
        if not df.empty:
            search = st.text_input("🔎 Search by Order Number")
            
            if search:
                mask = df.iloc[:, 0].astype(str).str.contains(search, case=False, na=False)
                fdf = df[mask]
            else:
                fdf = df
            
            st.write(f"📊 {len(fdf)} orders found")
            
            for _, row in fdf.iterrows():
                order = str(row.iloc[0]) if len(row) > 0 else "?"
                time = str(row.iloc[1]) if len(row) > 1 else ""
                
                with st.expander(f"📦 {order} | {time}"):
                    urls = []
                    for i in range(2, len(row)):
                        val = str(row.iloc[i])
                        if val.startswith('http'):
                            urls.append(val)
                    
                    if urls:
                        cols = st.columns(4)
                        for i, url in enumerate(urls):
                            with cols[i % 4]:
                                st.image(url, use_container_width=True)
                    else:
                        st.write("No images")
        else:
            st.info("No data in sheet")
    except Exception as e:
        st.error(f"Error loading data: {e}")

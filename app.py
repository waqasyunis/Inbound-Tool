import streamlit as st
import requests
import base64
from datetime import datetime
import pandas as pd
from PIL import Image
from io import BytesIO
import io
import time

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
        # Resize to smaller size for faster upload
        img.thumbnail((600, 600), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=40)
        output.seek(0)
        return output.read()
    except:
        return image_bytes

def upload_to_imgbb(image_bytes, retry=3):
    for attempt in range(retry):
        try:
            compressed = compress_image(image_bytes)
            b64 = base64.b64encode(compressed).decode('utf-8')
            
            resp = requests.post(
                "https://api.imgbb.com/1/upload",
                data={"key": IMGBB_API_KEY, "image": b64},
                timeout=60
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return data["data"]["url"]
            
            # Wait before retry
            time.sleep(2)
            
        except Exception as e:
            time.sleep(2)
            continue
    
    return None

def save_to_sheet(order, urls):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        requests.get(GOOGLE_SCRIPT_URL, params={
            "order_number": order,
            "timestamp": ts,
            "images": ",".join(urls)
        }, timeout=60)
        return True
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
        
        col1, col2 = st.columns([3, 1])
        with col1:
            order_input = st.text_input("Order Number", placeholder="Enter order number...", key=f"order_{st.session_state.form_key}", label_visibility="collapsed")
        with col2:
            confirm_btn = st.button("✅ Confirm", type="primary", use_container_width=True)
        
        if confirm_btn and order_input.strip():
            st.session_state.confirmed_order = order_input.strip()
            st.rerun()
        
        if confirm_btn and not order_input.strip():
            st.error("⚠️ Order number dalo!")
            
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"📦 Order: **{st.session_state.confirmed_order}**")
        with col2:
            if st.button("🔄 New Order", use_container_width=True):
                clear_form()
                st.rerun()
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📸 Camera")
            cam_key = f"cam_{len(st.session_state.camera_images)}_{st.session_state.form_key}"
            cam_img = st.camera_input("Take Photo", key=cam_key, label_visibility="collapsed")
            
            if cam_img:
                if all(s.getvalue() != cam_img.getvalue() for s in st.session_state.camera_images):
                    st.session_state.camera_images.append(cam_img)
                    st.rerun()
        
        with col2:
            st.subheader("📁 Upload")
            files = st.file_uploader("Upload", type=['jpg','jpeg','png'], accept_multiple_files=True, key=f"up_{st.session_state.form_key}", label_visibility="collapsed")
        
        all_imgs = list(st.session_state.camera_images)
        if files:
            all_imgs.extend(files)
        
        if all_imgs:
            st.markdown("---")
            st.subheader(f"📋 {len(all_imgs)} Photos")
            
            cols = st.columns(4)
            for i, img in enumerate(all_imgs):
                with cols[i % 4]:
                    st.image(img, caption=f"{i+1}", use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.camera_images:
                    if st.button("🗑️ Clear Photos", use_container_width=True):
                        st.session_state.camera_images = []
                        st.rerun()
            
            with col2:
                if st.button(f"💾 SAVE {st.session_state.confirmed_order}", type="primary", use_container_width=True):
                    progress = st.progress(0)
                    status = st.empty()
                    
                    urls = []
                    total = len(all_imgs)
                    failed = 0
                    
                    for i, img in enumerate(all_imgs):
                        status.text(f"⏳ Uploading {i+1}/{total}... (retry if fail)")
                        url = upload_to_imgbb(img.getvalue(), retry=3)
                        
                        if url:
                            urls.append(url)
                        else:
                            failed += 1
                        
                        progress.progress((i+1)/total)
                    
                    if urls:
                        status.text("💾 Saving to sheet...")
                        save_to_sheet(st.session_state.confirmed_order, urls)
                        
                        if failed > 0:
                            st.warning(f"⚠️ {failed} photo(s) failed, {len(urls)} saved for **{st.session_state.confirmed_order}**")
                        else:
                            st.success(f"✅ All {len(urls)} photos saved for **{st.session_state.confirmed_order}**")
                        
                        st.balloons()
                        clear_form()
                        st.rerun()
                    else:
                        st.error("❌ All uploads failed! Check internet connection.")

with tab2:
    st.subheader("🔍 Search Orders")
    
    if st.button("🔄 Refresh"):
        st.rerun()
    
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        
        search = st.text_input("🔎 Search Order Number")
        
        if search:
            fdf = df[df.iloc[:, 0].astype(str).str.contains(search, case=False, na=False)]
        else:
            fdf = df
        
        st.write(f"📊 {len(fdf)} orders")
        
        for _, row in fdf.iterrows():
            order = str(row.iloc[0])
            time_str = str(row.iloc[1]) if len(row) > 1 else ""
            
            with st.expander(f"📦 {order} | {time_str}"):
                urls = [str(row.iloc[i]) for i in range(2, len(row)) if str(row.iloc[i]).startswith('http')]
                if urls:
                    cols = st.columns(4)
                    for i, url in enumerate(urls):
                        with cols[i % 4]:
                            st.image(url, use_container_width=True)
    except:
        st.info("No data")

import streamlit as st
import requests
import base64
from datetime import datetime
from PIL import Image
from io import BytesIO
import io
import pandas as pd

st.set_page_config(page_title="Order Upload", page_icon="📷", layout="wide")

GURL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbxh_P5lLxoySjhqpQUPXofTttIRTkBHub1pGPKKtGaYHmdOSnjGZMzaqzv1JJ27jDab/exec"
SHEET = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"

if 'imgs' not in st.session_state: st.session_state.imgs = []
if 'order' not in st.session_state: st.session_state.order = ""
if 'k' not in st.session_state: st.session_state.k = 0

def upload_img(img_bytes):
    p = Image.open(BytesIO(img_bytes)).convert('RGB')
    p.thumbnail((400, 400))
    buf = io.BytesIO()
    p.save(buf, 'JPEG', quality=50)
    b64 = base64.b64encode(buf.getvalue()).decode()
    
    # Try ImgBB first
    try:
        r = requests.post("https://api.imgbb.com/1/upload", 
            data={"key": "5d8c1750878fa4077dca7f25067822f1", "image": b64}, 
            timeout=15)
        if r.ok and r.json().get("success"):
            return r.json()["data"]["url"]
    except:
        pass
    
    # Backup: freeimage.host
    try:
        r = requests.post("https://freeimage.host/api/1/upload",
            data={"key": "6d207e02198a847aa98d0a2a901485a5", "source": b64, "format": "json"},
            timeout=15)
        if r.ok and r.json().get("success"):
            return r.json()["image"]["url"]
    except:
        pass
    
    return None

st.title("📷 Order Upload")

t1, t2 = st.tabs(["📤 Upload", "🔍 Search"])

with t1:
    if not st.session_state.order:
        st.subheader("📦 Enter order #")
        o = st.text_input("Order Number", key=f"o_{st.session_state.k}", placeholder="Order number ...")
        
        c1, c2 = st.columns(2)
        if c1.button("⏎ Enter", type="primary", use_container_width=True) and o.strip():
            st.session_state.order = o.strip()
            st.rerun()
        if c2.button(f"💾 Save {o}" if o else "💾 Save", use_container_width=True) and o.strip():
            st.session_state.order = o.strip()
            st.rerun()
    
    else:
        c1, c2 = st.columns([3,1])
        c1.success(f"📦 **{st.session_state.order}**")
        if c2.button("🔄 New Order"):
            st.session_state.order = ""
            st.session_state.imgs = []
            st.session_state.k += 1
            st.rerun()
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        cam = c1.camera_input("📸 Camera", key=f"c_{len(st.session_state.imgs)}_{st.session_state.k}")
        files = c2.file_uploader("📁 Upload", type=['jpg','jpeg','png'], accept_multiple_files=True, key=f"f_{st.session_state.k}")
        
        if cam and not any(x.getvalue() == cam.getvalue() for x in st.session_state.imgs):
            st.session_state.imgs.append(cam)
            st.rerun()
        
        all_imgs = st.session_state.imgs + (files or [])
        
        if all_imgs:
            st.markdown("---")
            cols = st.columns(4)
            for i, img in enumerate(all_imgs): 
                cols[i%4].image(img, caption=i+1, use_container_width=True)
            
            c1, c2 = st.columns(2)
            if c1.button("🗑️ Clear", use_container_width=True):
                st.session_state.imgs = []
                st.rerun()
            
            if c2.button(f"💾 SAVE {st.session_state.order}", type="primary", use_container_width=True):
                urls = []
                prog = st.progress(0)
                
                for i, img in enumerate(all_imgs):
                    prog.progress((i+1)/len(all_imgs), f"⏳ {i+1}/{len(all_imgs)}")
                    url = upload_img(img.getvalue())
                    if url: urls.append(url)
                
                if urls:
                    requests.get(GURL, params={
                        "order_number": st.session_state.order,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "images": ",".join(urls)
                    }, timeout=30)
                    
                    st.success(f"✅ {len(urls)} photos saved for {st.session_state.order}!")
                    st.balloons()
                    st.session_state.order = ""
                    st.session_state.imgs = []
                    st.session_state.k += 1
                    st.rerun()
                else:
                    st.error("❌ Failed! Check internet.")

with t2:
    if st.button("🔄 Refresh"): st.rerun()
    try:
        df = pd.read_csv(SHEET)
        search = st.text_input("🔎 Search")
        fdf = df[df.iloc[:,0].astype(str).str.contains(search, case=False, na=False)] if search else df
        for _, r in fdf.iterrows():
            with st.expander(f"📦 {r.iloc[0]} | {r.iloc[1]}"):
                urls = [str(r.iloc[i]) for i in range(2,len(r)) if str(r.iloc[i]).startswith('http')]
                if urls:
                    cols = st.columns(4)
                    for i, u in enumerate(urls): cols[i%4].image(u, use_container_width=True)
    except:
        pass

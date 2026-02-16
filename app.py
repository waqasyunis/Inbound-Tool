import streamlit as st
import requests
import base64
from datetime import datetime
from PIL import Image
from io import BytesIO
import io
import pandas as pd

st.set_page_config(page_title="Order Upload", page_icon="📷", layout="wide")

KEY = "5d8c1750878fa4077dca7f25067822f1"
GURL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbxh_P5lLxoySjhqpQUPXofTttIRTkBHub1pGPKKtGaYHmdOSnjGZMzaqzv1JJ27jDab/exec"
SHEET = "https://docs.google.com/spreadsheets/d/1EArwRntG-s-fLzmslqoKTTAyVAmXpyn7DaiBtCUCS9g/export?format=csv"

if 'imgs' not in st.session_state: st.session_state.imgs = []
if 'order' not in st.session_state: st.session_state.order = ""

st.title("📷 Order Upload")

t1, t2 = st.tabs(["📤 Upload", "🔍 Search"])

with t1:
    if not st.session_state.order:
        o = st.text_input("📦 Order Number")
        if st.button("✅ OK", type="primary") and o:
            st.session_state.order = o.strip()
            st.rerun()
    else:
        st.success(f"📦 {st.session_state.order}")
        if st.button("🔄 Reset"):
            st.session_state.order = ""
            st.session_state.imgs = []
            st.rerun()
        
        c1, c2 = st.columns(2)
        cam = c1.camera_input("📸")
        files = c2.file_uploader("📁", type=['jpg','jpeg','png'], accept_multiple_files=True)
        
        if cam:
            b = cam.getvalue()
            if not any(x.getvalue() == b for x in st.session_state.imgs):
                st.session_state.imgs.append(cam)
                st.rerun()
        
        all_imgs = st.session_state.imgs + (files or [])
        
        if all_imgs:
            cols = st.columns(4)
            for i, img in enumerate(all_imgs):
                cols[i%4].image(img, caption=i+1, use_container_width=True)
            
            c1, c2 = st.columns(2)
            if c1.button("🗑️ Clear"):
                st.session_state.imgs = []
                st.rerun()
            
            if c2.button(f"💾 SAVE {st.session_state.order}", type="primary"):
                urls = []
                status = st.empty()
                prog = st.progress(0)
                
                for i, img in enumerate(all_imgs):
                    status.info(f"⏳ {i+1}/{len(all_imgs)}")
                    prog.progress((i+1)/len(all_imgs))
                    
                    p = Image.open(BytesIO(img.getvalue())).convert('RGB')
                    p.thumbnail((400, 400))
                    b = io.BytesIO()
                    p.save(b, 'JPEG', quality=30)
                    b64 = base64.b64encode(b.getvalue()).decode()
                    
                    try:
                        r = requests.post("https://api.imgbb.com/1/upload", data={"key": KEY, "image": b64}, timeout=30)
                        if r.status_code == 200 and r.json().get("success"):
                            urls.append(r.json()["data"]["url"])
                    except:
                        pass
                
                if urls:
                    status.info("💾 Saving...")
                    requests.get(GURL, params={"order_number": st.session_state.order, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "images": ",".join(urls)}, timeout=30)
                    st.success(f"✅ {len(urls)} photos saved!")
                    st.balloons()
                    st.session_state.order = ""
                    st.session_state.imgs = []
                    st.rerun()
                else:
                    st.error("❌ Failed - check internet!")

with t2:
    if st.button("🔄 Refresh"): st.rerun()
    try:
        df = pd.read_csv(SHEET)
        search = st.text_input("🔎 Search")
        fdf = df[df.iloc[:,0].astype(str).str.contains(search, case=False, na=False)] if search else df
        for _, r in fdf.iterrows():
            with st.expander(f"📦 {r.iloc[0]} | {r.iloc[1]}"):
                urls = [str(r.iloc[i]) for i in range(2, len(r)) if str(r.iloc[i]).startswith('http')]
                if urls:
                    cols = st.columns(4)
                    for i, u in enumerate(urls): cols[i%4].image(u, use_container_width=True)
    except:
        pass

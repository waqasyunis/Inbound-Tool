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
if 'k' not in st.session_state: st.session_state.k = 0

st.title("📷 Order Upload")

t1, t2 = st.tabs(["📤 Upload", "🔍 Search"])

with t1:
    # Step 1: Order Number (picture tab tak nahi dikhega jab tak order na ho)
    if not st.session_state.order:
        st.subheader("📦 Enter Order Number First")
        o = st.text_input("Order Number", key=f"ord_{st.session_state.k}")
        
        c1, c2 = st.columns(2)
        # Enter button
        if c1.button("⏎ Enter", type="primary", use_container_width=True) and o.strip():
            st.session_state.order = o.strip()
            st.rerun()
        # Save Order Name button
        if c2.button(f"💾 Save as {o}" if o else "💾 Save Order", use_container_width=True) and o.strip():
            st.session_state.order = o.strip()
            st.rerun()
    
    # Step 2: Pictures (sirf tab dikhe jab order confirm ho)
    else:
        col1, col2 = st.columns([3,1])
        col1.success(f"📦 Order: **{st.session_state.order}**")
        if col2.button("🔄 New Order"):
            st.session_state.order = ""
            st.session_state.imgs = []
            st.session_state.k += 1
            st.rerun()
        
        st.markdown("---")
        
        # Camera + Upload options
        c1, c2 = st.columns(2)
        cam = c1.camera_input("📸 Camera", key=f"cam_{len(st.session_state.imgs)}_{st.session_state.k}")
        files = c2.file_uploader("📁 Upload Files", type=['jpg','jpeg','png'], accept_multiple_files=True, key=f"f_{st.session_state.k}")
        
        # Add camera image
        if cam:
            if not any(x.getvalue() == cam.getvalue() for x in st.session_state.imgs):
                st.session_state.imgs.append(cam)
                st.rerun()
        
        # All images
        all_imgs = st.session_state.imgs + (files or [])
        
        if all_imgs:
            st.markdown("---")
            st.subheader(f"📋 {len(all_imgs)} Photos")
            
            # Preview
            cols = st.columns(4)
            for i, img in enumerate(all_imgs):
                cols[i%4].image(img, caption=i+1, use_container_width=True)
            
            # Buttons
            c1, c2 = st.columns(2)
            
            if c1.button("🗑️ Clear All Photos", use_container_width=True):
                st.session_state.imgs = []
                st.rerun()
            
            if c2.button(f"💾 SAVE {st.session_state.order}", type="primary", use_container_width=True):
                urls = []
                prog = st.progress(0)
                stat = st.empty()
                
                for i, img in enumerate(all_imgs):
                    stat.text(f"⏳ Uploading {i+1}/{len(all_imgs)}...")
                    prog.progress((i+1)/len(all_imgs))
                    
                    # Compress & Upload
                    p = Image.open(BytesIO(img.getvalue())).convert('RGB')
                    p.thumbnail((400,400))
                    buf = io.BytesIO()
                    p.save(buf, 'JPEG', quality=30)
                    
                    try:
                        r = requests.post("https://api.imgbb.com/1/upload", 
                            data={"key": KEY, "image": base64.b64encode(buf.getvalue()).decode()}, 
                            timeout=30)
                        if r.ok and r.json().get("success"):
                            urls.append(r.json()["data"]["url"])
                    except:
                        pass
                
                # Save to Sheet
                if urls:
                    stat.text("💾 Saving to sheet...")
                    requests.get(GURL, params={
                        "order_number": st.session_state.order,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "images": ",".join(urls)
                    }, timeout=30)
                    
                    st.success(f"✅ DONE! {len(urls)} photos saved for {st.session_state.order}")
                    st.balloons()
                    
                    # Reset
                    st.session_state.order = ""
                    st.session_state.imgs = []
                    st.session_state.k += 1
                    st.rerun()
                else:
                    st.error("❌ Upload failed! Check internet.")

with t2:
    st.subheader("🔍 Search Orders")
    if st.button("🔄 Refresh"): st.rerun()
    
    try:
        df = pd.read_csv(SHEET)
        search = st.text_input("🔎 Search Order")
        fdf = df[df.iloc[:,0].astype(str).str.contains(search, case=False, na=False)] if search else df
        
        st.write(f"📊 {len(fdf)} orders")
        
        for _, r in fdf.iterrows():
            with st.expander(f"📦 {r.iloc[0]} | {r.iloc[1]}"):
                urls = [str(r.iloc[i]) for i in range(2,len(r)) if str(r.iloc[i]).startswith('http')]
                if urls:
                    cols = st.columns(4)
                    for i, u in enumerate(urls): 
                        cols[i%4].image(u, use_container_width=True)
    except:
        st.info("No data yet")

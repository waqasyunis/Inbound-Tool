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
    
    try:
        r = requests.post("https://api.imgbb.com/1/upload", 
            data={"key": "5d8c1750878fa4077dca7f25067822f1", "image": b64}, 
            timeout=30)
        if r.ok and r.json().get("success"):
            return r.json()["data"]["url"]
        else:
            return f"ERROR: {r.text[:100]}"
    except Exception as e:
        return f"EXCEPTION: {str(e)}"

st.title("📷 Order Upload - DEBUG")

t1, t2 = st.tabs(["📤 Upload", "🔍 Search"])

with t1:
    if not st.session_state.order:
        st.subheader("📦 Pehle Order Number Dalo")
        o = st.text_input("Order Number", key=f"o_{st.session_state.k}")
        
        if st.button("✅ OK", type="primary") and o.strip():
            st.session_state.order = o.strip()
            st.rerun()
    
    else:
        c1, c2 = st.columns([3,1])
        c1.success(f"📦 **{st.session_state.order}**")
        if c2.button("🔄 New"):
            st.session_state.order = ""
            st.session_state.imgs = []
            st.session_state.k += 1
            st.rerun()
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        cam = c1.camera_input("📸", key=f"c_{len(st.session_state.imgs)}_{st.session_state.k}")
        files = c2.file_uploader("📁", type=['jpg','jpeg','png'], accept_multiple_files=True, key=f"f_{st.session_state.k}")
        
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
            if c1.button("🗑️ Clear"):
                st.session_state.imgs = []
                st.rerun()
            
            if c2.button(f"💾 SAVE {st.session_state.order}", type="primary"):
                st.write("---")
                st.write("### 🔍 DEBUG:")
                
                urls = []
                
                for i, img in enumerate(all_imgs):
                    st.write(f"**Photo {i+1}:** Uploading...")
                    result = upload_img(img.getvalue())
                    st.write(f"Result: `{result}`")
                    
                    if result.startswith("http"):
                        urls.append(result)
                        st.write(f"✅ Success!")
                    else:
                        st.write(f"❌ Failed!")
                
                st.write("---")
                st.write(f"**Total URLs:** {len(urls)}")
                st.write(f"**URLs:** {urls}")
                
                if urls:
                    st.write("**Saving to Google Sheet...**")
                    
                    params = {
                        "order_number": st.session_state.order,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "images": ",".join(urls)
                    }
                    st.write(f"Params: {params}")
                    
                    try:
                        r = requests.get(GURL, params=params, timeout=30)
                        st.write(f"Response: {r.text}")
                        
                        if "success" in r.text.lower():
                            st.success(f"✅ SAVED!")
                            st.balloons()
                    except Exception as e:
                        st.write(f"Error: {e}")
                else:
                    st.error("❌ No URLs - upload failed!")

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

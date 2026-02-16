import streamlit as st
import requests
import base64
from datetime import datetime
from PIL import Image
from io import BytesIO
import io

st.set_page_config(page_title="Simple Test", page_icon="📷")

IMGBB_API_KEY = "5d8c1750878fa4077dca7f25067822f1"
GOOGLE_SCRIPT_URL = "https://script.google.com/a/macros/joinfleek.com/s/AKfycbxh_P5lLxoySjhqpQUPXofTttIRTkBHub1pGPKKtGaYHmdOSnjGZMzaqzv1JJ27jDab/exec"

st.title("📷 Simple Test")

order = st.text_input("Order Number")
photo = st.camera_input("Take 1 Photo")

if st.button("💾 TEST SAVE", type="primary") and order and photo:
    
    st.write("1️⃣ Compressing image...")
    img = Image.open(BytesIO(photo.getvalue()))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    img = img.resize((400, 400), Image.LANCZOS)
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=50)
    compressed = output.getvalue()
    st.write(f"   Size: {len(compressed)} bytes")
    
    st.write("2️⃣ Uploading to ImgBB...")
    b64 = base64.b64encode(compressed).decode('utf-8')
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": b64},
        timeout=120
    )
    st.write(f"   Status: {resp.status_code}")
    
    if resp.status_code == 200 and resp.json().get("success"):
        url = resp.json()["data"]["url"]
        st.write(f"   ✅ URL: {url}")
        
        st.write("3️⃣ Saving to Google Sheet...")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        resp2 = requests.get(GOOGLE_SCRIPT_URL, params={
            "order_number": order,
            "timestamp": ts,
            "images": url
        }, timeout=60)
        
        st.write(f"   Status: {resp2.status_code}")
        st.write(f"   Response: {resp2.text}")
        
        if "success" in resp2.text.lower():
            st.success(f"✅ DONE! Check sheet for order: {order}")
            st.balloons()
    else:
        st.error(f"❌ ImgBB failed: {resp.text}")

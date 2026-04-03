import streamlit as st

st.set_page_config(page_title="We've Moved 🚀", layout="centered")

st.markdown("""
<div style="
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    height:80vh;
    text-align:center;
    font-family:sans-serif;
">
    <h1>🚀 We've moved!</h1>
    <p style="font-size:18px;">
        This app is no longer available here.
    </p>
    <p style="font-size:16px;">
        Please use the new app below:
    </p>

    <a href="https://unbrokentribe-fitness.streamlit.app/" target="_self">
        <button style="
            margin-top:20px;
            padding:12px 24px;
            font-size:16px;
            border-radius:10px;
            border:none;
            background:#ff4b4b;
            color:white;
            cursor:pointer;
        ">
            Go to New App
        </button>
    </a>

    <p style="margin-top:20px; font-size:14px;">
        (Clicking the button will take you there instantly)
    </p>
</div>
""", unsafe_allow_html=True)

st.stop()

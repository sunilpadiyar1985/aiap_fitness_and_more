import streamlit as st

# Redirect notice page
st.markdown("""
    <meta http-equiv="refresh" content="5;url=https://unbrokentribe-fitness.streamlit.app/">
    <div style="
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 80vh;
        text-align: center;
        font-family: sans-serif;
    ">
        <h2>🚀 We've moved on! To a bigger/better place. </h2>
        <p>This app is no longer available at this URL.</p>
        <p>You will be redirected to the new app in <b>5 seconds</b>.</p>
        <p>If not, <a href="https://unbrokentribe-fitness.streamlit.app/">click here</a>.</p>
    </div>
""", unsafe_allow_html=True)

st.stop()



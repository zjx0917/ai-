import streamlit as st

st.set_page_config(page_title="Test")
st.title("Test Page")
st.write("If you see this, the environment is OK.")

try:
    app_id = st.secrets["BAIDU_APP_ID"]
    st.success("Secrets loaded")
except:
    st.error("Secrets not configured")
   

  

import time
import streamlit as st

st.set_page_config(page_title="Slim check", page_icon="🧪", layout="wide")

st.title("Slim boot check")
st.write("If you see this in <5s, the Cloud is fine. Any slowness is in app logic.")

with st.spinner("Pretending to work 1s..."):
    time.sleep(1)

st.success("Slim app up ✅")

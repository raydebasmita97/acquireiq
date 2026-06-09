import streamlit as st

st.set_page_config(
    page_title="AcquireIQ",
    page_icon="🏢",
    layout="centered"
)

st.markdown("<h1 style='color:#1F4E79;'>AcquireIQ</h1>", unsafe_allow_html=True)
st.markdown("### Welcome")
st.markdown("Select a page from the sidebar to get started.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
        <a href='/CEO_Onboarding' target='_self' style='display:block; background:#1F4E79; color:white;
        padding:1.5rem; border-radius:10px; text-decoration:none; text-align:center;'>
        <h3 style='color:white; margin:0;'>🏢 CEO Onboarding</h3>
        <p style='color:#cce; margin:0.5rem 0 0;'>AI assistant and dashboards for newly placed CEOs</p>
        </a>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
        <a href='/Admin' target='_self' style='display:block; background:#2e86c1; color:white;
        padding:1.5rem; border-radius:10px; text-decoration:none; text-align:center;'>
        <h3 style='color:white; margin:0;'>⚙️ Admin Panel</h3>
        <p style='color:#cce; margin:0.5rem 0 0;'>Manage knowledge base, data, and dashboards</p>
        </a>
    """, unsafe_allow_html=True)

import streamlit as st

st.set_page_config(
    page_title="AcquireIQ",
    page_icon="🏢",
    layout="centered"
)

st.markdown("""
    <div style='text-align:center; padding: 3rem 0 1rem 0;'>
        <h1 style='color:#1F4E79; font-size:3rem; margin-bottom:0;'>AcquireIQ</h1>
        <p style='color:#777; font-size:1.1rem; margin-top:0.5rem;'>
            Intelligent Lead Qualification for Business Acquisitions
        </p>
    </div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("""
    <div style='max-width:500px; margin:2rem auto;'>
        <a href='/CEO_Onboarding' target='_self' style='
            display:block;
            background: linear-gradient(135deg, #1F4E79, #2e86c1);
            color:white;
            padding:2rem;
            border-radius:12px;
            text-decoration:none;
            text-align:center;
            box-shadow: 0 4px 15px rgba(31,78,121,0.3);
        '>
            <div style='font-size:2.5rem;'>🏢</div>
            <h2 style='color:white; margin:0.5rem 0 0.25rem 0;'>CEO Onboarding Agent</h2>
            <p style='color:#cde; margin:0; font-size:0.95rem;'>
                AI-powered assistant and dashboards to help a newly placed CEO
                get up to speed on their acquired business on day one.
            </p>
        </a>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <p style='text-align:center; color:#aaa; font-size:0.8rem; margin-top:3rem;'>
        AcquireIQ — Built by Debasmita Ray
    </p>
""", unsafe_allow_html=True)

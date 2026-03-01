
import streamlit as st

from ui.lang import t

import base64
import os

def home_page():
    # Helper para carregar imagem e converter para base64
    def get_img_as_base64(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()

    img_path = "images/logo.svg"
    img_base64 = get_img_as_base64(img_path)

    # Hero Section: Logo + Nome (Centralizados)
    st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 40px; margin-top: -20px;">
            <img src="data:image/svg+xml;base64,{img_base64}" width="100">
            <h1 style="font-size: 3.5rem; margin: 0;">
                <span style="color: var(--text-color);">Solver</span> <span style="color: #4CAF50;">LP</span>
            </h1>
        </div>
    """, unsafe_allow_html=True)

    # Subtitulo
    st.markdown(f"""
    <div style="text-align: center; margin-top: -20px; margin-bottom: 50px;">
        <p style="font-size: 1.25rem; color: var(--text-color); font-weight: 300; opacity: 0.8;">
            {t("home.subtitle")}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Custom CSS for Home Page Buttons
    st.markdown("""
        <style>
        /* Transform buttons into feature cards */
        div.stButton > button {
            height: 100%;
            min-height: 160px;
            border-radius: 10px;
            background-color: var(--secondary-background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.2);
            text-align: left;
            white-space: pre-wrap;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: flex-start;
            width: 100%;
        }
        div.stButton > button:hover {
            border-color: #4CAF50;
            opacity: 0.9;
        }
        div.stButton > button p {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 10px;
        }
        div.stButton > button p strong {
            font-size: 1.25rem;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Linha 1: Solvers (Principais) ---
    c_solv1, c_solv2 = st.columns(2)
    
    with c_solv1:
        if st.button(f":blue[**{t('home.simplex_title')}**]\n\n{t('home.simplex_desc')}", key="btn_simplex_home", use_container_width=True):
            st.session_state["pending_redirect"] = "simplex"
            st.rerun()
        
    with c_solv2:
        if st.button(f":green[**{t('home.bab_title')}**]\n\n{t('home.bab_desc')}", key="btn_bab_home", use_container_width=True):
            st.session_state["pending_redirect"] = "bab"
            st.rerun()

    st.write("")
    
    # --- Linha 2: Ferramentas (Novidades) ---
    c_tool1, c_tool2, c_tool3 = st.columns(3)
    
    with c_tool1:
        if st.button(f":orange[**{t('home.duality_title')}**]\n\n{t('home.duality_desc')}", key="btn_duality_home", use_container_width=True):
            st.session_state["pending_redirect"] = "duality"
            st.rerun()

    with c_tool2:
        if st.button(f":red[**{t('home.sensitivity_title')}**]\n\n{t('home.sensitivity_desc')}", key="btn_sens_home", use_container_width=True):
            st.session_state["pending_redirect"] = "sensitivity"
            st.rerun()

    with c_tool3:
        if st.button(f":blue[**{t('home.std_form_title')}**]\n\n{t('home.std_form_desc')}", key="btn_std_form_home", use_container_width=True):
            st.session_state["pending_redirect"] = "std_form"
            st.rerun()
        
    st.write("")

    # --- Linha 3: Recursos (Biblioteca, Histórico e Multi-Idioma) ---
    c_res1, c_res2, c_res3 = st.columns(3)
    
    with c_res1:
        if st.button(f":violet[**{t('home.library_title')}**]\n\n{t('home.library_desc')}", key="btn_lib_home", use_container_width=True):
            st.session_state["pending_redirect"] = "library"
            st.rerun()

    with c_res2:
        if st.button(f":orange[**{t('home.history_title')}**]\n\n{t('home.history_desc')}", key="btn_hist_home", use_container_width=True):
            st.session_state["pending_redirect"] = "history"
            st.rerun()
        
    with c_res3:
        # For Language, open the sidebar using a small JS trick since natively it requires st.sidebar toggle.
        import streamlit.components.v1 as components
        
        # We need a proper button that looks like the others, but triggers JS.
        # We create a button and an iframe that listens to its clicks (or just execute a click on the sidebar when the button is pressed).
        # Actually in Streamlit, pressing the button triggers a python re-run.
        # We can just check if it was clicked, and IF SO, render the JS to open the sidebar!
        if st.button(f":green[**{t('home.multilang_title')}**]\n\n{t('home.multilang_desc')}", key="btn_lang_home", use_container_width=True):
            components.html(
                """
                <script>
                const parentDoc = window.parent.document;
                // Find the sidebar toggle button and click it
                const sidebarToggle = parentDoc.querySelector('[data-testid="collapsedControl"]');
                if (sidebarToggle) {
                    sidebarToggle.click();
                }
                </script>
                """,
                height=0
            )

"""
Carte vide.
"""

from __future__ import annotations

import streamlit as st


def render_empty_map():

    st.markdown(
        """
<div style="
height:520px;

display:flex;

align-items:center;

justify-content:center;

border:2px dashed #CBD5E1;

border-radius:16px;

background:#F8FAFC;

color:#64748B;
">

<div style="text-align:center;">

<h2>🗺️</h2>

<h3>Carte interactive</h3>

Folium sera intégré ici.

</div>

</div>
""",
        unsafe_allow_html=True,
    )
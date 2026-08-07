"""
Titre de section.
"""

from __future__ import annotations

import streamlit as st


def render_section(title: str):

    st.markdown(
        f"""
<h3 style="
color:#17324D;
margin-top:30px;
margin-bottom:10px;
">
{title}
</h3>
""",
        unsafe_allow_html=True,
    )
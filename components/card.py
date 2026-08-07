"""
Carte générique GeoDashboard.
"""

from __future__ import annotations

import streamlit as st


def begin_card(title: str) -> None:
    """Début d'une carte."""

    st.markdown(
        f"""
<div style="
background:white;
padding:20px;
border-radius:16px;
border:1px solid #E2E8F0;
box-shadow:0 4px 12px rgba(0,0,0,.05);
margin-top:15px;
margin-bottom:15px;
">

<h4 style="
margin-top:0;
color:#17324D;
">
{title}
</h4>
""",
        unsafe_allow_html=True,
    )


def end_card() -> None:
    """Fin d'une carte."""

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )
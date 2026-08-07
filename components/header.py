"""En-tête principal de GeoDashboard."""

import streamlit as st

from .theme import (
    APP_NAME,
    BORDER,
    PRIMARY,
    SECONDARY,
    TEXT_SECONDARY,
    VERSION,
)


def render_header() -> None:
    """Affiche l’en-tête principal de l’application."""

    html = f"""
<div style="display:flex;justify-content:space-between;align-items:center;
background:#FFFFFF;border:1px solid {BORDER};border-radius:16px;
padding:18px 22px;margin-bottom:18px;
box-shadow:0 6px 18px rgba(23,50,77,0.06);">

    <div>
        <div style="font-size:30px;font-weight:800;color:{PRIMARY};
        line-height:1.1;">
            {APP_NAME}
        </div>

        <div style="margin-top:6px;font-size:14px;color:{TEXT_SECONDARY};">
            Analyse territoriale, cartographie et indicateurs SIG
        </div>
    </div>

    <div style="text-align:right;">
        <div style="font-size:13px;font-weight:700;color:{SECONDARY};">
            Plateforme cartographique
        </div>

        <div style="margin-top:5px;font-size:12px;color:{TEXT_SECONDARY};">
            Version {VERSION}
        </div>
    </div>

</div>
"""

    st.html(html)
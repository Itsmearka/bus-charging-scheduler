"""
UI Styles Module
Custom CSS styling for Streamlit application.
"""

import streamlit as st


def apply_custom_styles():
    """Apply custom CSS for progress bar shimmer effect and other styling."""
    st.markdown("""
<style>
@keyframes shimmer {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}

.stProgress > div > div > div {
    animation: shimmer 2s ease-in-out infinite;
}
</style>
""", unsafe_allow_html=True)

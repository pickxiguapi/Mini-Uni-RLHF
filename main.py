import streamlit as st
import sys
import os
import pathlib
from st_pages import Page, show_pages, add_page_title

st.set_page_config(
    page_title="Mini-Uni-RLHF",
    page_icon="🚀",
)

with st.sidebar:
    st.title('🚀 Mini-Uni-RLHF')
    
st.subheader('📋Instruction', divider='rainbow')

st.markdown('''
            First, create your project.   
            Then, annotate as you like.   
            Finally, export the annotation
            ''')

show_pages(
    [
        Page("main.py", "Home", "🏠"),
        Page("pages/create.py", "Create", "⚙️"),
        Page("pages/annotate.py", "Annotate", "⚡"),
        Page("pages/export.py", "Export", "🤗"),
    ]
)




import streamlit as st
import os
import json
import csv
import pandas as pd

def get_all_project(data_dir):
    file_names = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
    json_files = [f for f in file_names if f.endswith('.json') and '@' in f]
    project_info = {}
    for json_file_name in json_files:
        project_name, _ = json_file_name.split('@')
        project_info.update({project_name: json_file_name})
    return project_info

def setup_project(data_dir, project_dir):
    project_dir = os.path.join(data_dir, project_dir)
    with open(project_dir, 'r') as jsonfile:
        project_info = json.load(jsonfile)
    with open(project_dir[:-5]+'.csv', 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile)
        next(csv_reader)  # for skipping header
        query_info = []
        for row in csv_reader:
            query_info.append(row)
    return project_info, query_info

st.set_page_config(page_title='Mini-Uni-RLHF (Export)', layout='wide')

project_info = get_all_project(data_dir="./data")
selected_project_name = st.selectbox('Choose your project', options=project_info.keys())

def click_view():
    st.session_state.view = 1
    
if 'view' not in st.session_state:
    st.session_state.view = 0

st.button('View', on_click=click_view)

if st.session_state.view:
    project_dir = os.path.join("./data", project_info[selected_project_name])
    with open(project_dir, 'r') as jsonfile:
        full_project_info = json.load(jsonfile)
    df = pd.read_csv(project_dir[:-5]+'.csv')
    
    with st.expander('🔍 Full Project infomation', expanded=False):
        st.write(full_project_info)
    with st.expander('🔍 Project dataframe', expanded=True):
        st.dataframe(data=df)
    
    csv_content = df.to_csv().encode('utf-8')
    st.download_button(label='Export', data=csv_content, file_name='export.csv', mime='text/csv')

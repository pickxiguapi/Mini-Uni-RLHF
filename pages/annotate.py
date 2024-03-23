import streamlit as st
import os
import json
import csv
import time
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

st.set_page_config(page_title='Mini-Uni-RLHF (Annotate)', layout='wide')

if 'project_choose_flag' not in st.session_state:
    st.session_state.project_choose_flag = False
if 'project_info' not in st.session_state:
    st.session_state.project_info = {}
if 'query_info' not in st.session_state:
    st.session_state.query_info = None
if 'index' not in st.session_state:
    st.session_state.index = 0
if 'label' not in st.session_state:
    st.session_state.label = []

if not st.session_state.project_choose_flag:
    project_info = get_all_project(data_dir="./data")
    selected_project_name = st.selectbox('Choose your project', options=project_info.keys())

    def on_button_click(project_info):
        st.session_state.project_choose_flag = True
        project_info, query_info = setup_project(data_dir="./data", project_dir=project_info[selected_project_name])
        st.session_state.project_info = project_info
        st.session_state.query_info = query_info
        
        # success
        placeholder = st.empty()
        placeholder.success('Loading project successfully!', icon="✅")
        time.sleep(1.5)
        placeholder.empty()

    st.button('Annotate', on_click=on_button_click, args=(project_info, ))

else: 
    # page initialization
    DEFAULT_WIDTH = 25
    width = st.sidebar.slider(
        label="Width", min_value=0, max_value=100, value=DEFAULT_WIDTH, format="%d%%"
    )
    width = max(width, 0.01)
    side = max((100 - 2*width) / 2, 0.01)
    
    with st.expander('🔍 Full Project infomation', expanded=False):
        st.write(st.session_state.project_info)
    with st.expander('🔍 Instruction', expanded=True):
        st.write(st.session_state.project_info["instruction"])
        
    # for annotation scheduler
    def save_and_next():
        # save
        query_id = st.session_state.query_info[st.session_state.index][2]
        label = st.session_state.label
        csv_dir = f"./data/{st.session_state.project_info['project_name']}@{st.session_state.project_info['project_id']}.csv"
        df = pd.read_csv(csv_dir)
        df.loc[df['query_id'] == query_id, ['label', 'annotated']] = [','.join(label), 1]
        df.to_csv(csv_dir, index=False)
        st.session_state.label = []
        # next
        st.session_state.index += 1
    
    with st.expander('🔍 Annotation UI', expanded=True):
        # e.g.
        #   [
        #   "{'start_indices_1': 79122, 'end_indices_1': 79132, 'start_indices_2': 71118, 'end_indices_2': 71128, 'query_id':                 '943b92ad6bbe40e58177051623a26014'}",
        #   1:"./videos/mrwN6BcYD7xDZBYWgeVUP4/walker_walk_medium_943b92ad6bbe40e58177051623a26014.mp4",
        #   2:"943b92ad6bbe40e58177051623a26014",
        #   3:"0"
        # ]
        
        # display video pair
        _, col, _ = st.columns([side, 2*width, side])
        with col:
            st.video(st.session_state.query_info[st.session_state.index][1])
            st.write(st.session_state.query_info[st.session_state.index][2])
    with st.expander('💡 Question', expanded=True):
        for k, v in st.session_state.project_info["question"].items():
            st.session_state.label.append(st.radio(k, options=v, horizontal=True))
        st.button('Submit', on_click=save_and_next)
    
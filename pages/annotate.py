import streamlit as st
import os
import json
import csv
import time
import pandas as pd
import os
import re
import time
from functools import partial

import streamlit as st
import cv2
import pickle
import numpy as np
import json
import random
import shutil
import pandas as pd
from PIL import Image
import shutil
from streamlit_img_label import st_img_label
from streamlit_img_label.manage import ImageManager, ImageDirManager





if 'feedback_type' not in st.session_state:
    st.session_state.feedback_type = ''
if 'image_index' not in st.session_state:
    st.session_state.image_index = 0
if 'disabled_save_btn' not in st.session_state:
    st.session_state.disabled_save_btn = False 
if 'rank_result_via_prompt' not in st.session_state:
    st.session_state.rank_result_via_prompt = []
if 'rank_result_via_prompt_vis' not in st.session_state:
    st.session_state.rank_result_via_prompt_vis = {}
if 'rect_results' not in st.session_state:
    st.session_state.rect_results = []
if 'image_list' not in st.session_state:
    st.session_state.image_list = []


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
        
        st.session_state.feedback_type = project_info['feedback_type']
        st.session_state.query_length = project_info['query_length']
    return project_info, query_info

def video_to_frames(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    os.makedirs(output_path, exist_ok=True)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        filename = os.path.join(output_path, f"{count}.jpg")
        cv2.imwrite(filename, frame)
        count += 1
    cap.release()


def sort_by_number(filename):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', filename)]

def previous_image():
    st.session_state["disabled_save_btn"] = True
    if st.session_state["image_index"] != 0:
        st.session_state["image_index"] = (st.session_state["image_index"]-1) % st.session_state['query_length'] 
    else:
        st.session_state["image_index"] = st.session_state['query_length']-1



def next_image():
    st.session_state["disabled_save_btn"] = True
    st.session_state["image_index"] = (st.session_state["image_index"]+1) % st.session_state['query_length']   


def next_annotate_file(idm):
    image_index = st.session_state["image_index"]
    st.session_state["disabled_save_btn"] = True
    next_image_index = idm.get_next_annotation_image(image_index)
    if next_image_index:
        st.session_state["image_index"] = idm.get_next_annotation_image(image_index)
    else:
        st.warning("All images are annotated.")
        next_image()
    
    
def go_to_image():
    file_index = st.session_state["files"].index(st.session_state["file"])
    st.session_state["image_index"] = file_index
    st.session_state["disabled_save_btn"] = True
    

def annotate(rects, idm, im, img_file_name):
    for box in rects:
        xmin = box["left"]
        ymin = box["top"]
        xmax = box["left"] + box["width"]
        ymax = box["top"] + box["height"]
        rank_result_via_prompt = st.session_state['rank_result_via_prompt_vis']
        if st.session_state["image_index"] not in rank_result_via_prompt:
            rank_result_via_prompt = [st.session_state["image_index"]] = [(xmin, ymin, xmax, ymax)]
        else:
            rank_result_via_prompt[st.session_state["image_index"]].append((xmin, ymin, xmax, ymax))

    st.session_state['rank_result_via_prompt_vis'] = rank_result_via_prompt
    im.save_annotation()
    image_annotate_file_name = img_file_name.split(".")[0] + ".xml"
    if image_annotate_file_name not in st.session_state["annotation_files"]:
        st.session_state["annotation_files"].append(image_annotate_file_name)
    next_annotate_file(idm)
    st.session_state["disabled_save_btn"] = True 

def keyframe(stchoose):
    index = st.session_state['rank_result_via_prompt'] 
    index.append(st.session_state['image_index'])
    st.session_state['rank_result_via_prompt'] = index

    file_path = str(st.session_state.query_info[st.session_state.index][1]).replace(".mp4", "_img"). \
                                replace("\\", "/") + f"/{st.session_state['image_index']}.jpg"
    image_list = st.session_state["image_list"]
    image_list.append(file_path)
    st.session_state["image_list"] = image_list
    
      
        
def previous():
    if st.session_state["image_index"] != 0:
        st.session_state["image_index"] = (st.session_state["image_index"]-1) % st.session_state['query_length'] 
    else:
        st.session_state["image_index"] = st.session_state['query_length'] -1
def next_img():
    st.session_state["image_index"] = (st.session_state["image_index"]+1) % st.session_state['query_length']  

    
@st.cache_data
def load_image_manager(img_path):
    return ImageManager(img_path)

@st.cache_data
def resize_image(im, width, height):
    return im.resizing_img(width, height)


    
@st.cache_data
def load_images(file_path):
    images = []
    for i in range(50):
        try:
            img_path = file_path + f"/{i}.jpg"
            images.append(Image.open(img_path)) 
        except FileNotFoundError:
            print(f"Error loading image {i}: file not found")
        except Exception as e:
            print(f"Error loading image {i}: {str(e)}")
    return images
    

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
        query_num = st.session_state.project_info['query_num']
        st.session_state['image_index'] = 0
        st.session_state['image_list'] = []
        
        if int(st.session_state.index) < query_num:
            # save
            query_id = st.session_state.query_info[st.session_state.index][2]
            label = st.session_state.label
            csv_dir = f"./data/{st.session_state.project_info['project_name']}@{st.session_state.project_info['project_id']}.csv"
            df = pd.read_csv(csv_dir)
            df.loc[df['query_id'] == query_id, ['label', 'annotated']] = [','.join(label), 1]
            df.to_csv(csv_dir, index=False)
            st.session_state.label = []
            st.session_state["rank_result_via_prompt"] = []
            # next
            
            if int(st.session_state.index) == query_num-1:
                # success
                placeholder = st.empty()
                placeholder.success('Loading project successfully!', icon="✅")
                time.sleep(3)
                placeholder.empty()

                st.button('Exit')
            else:
                st.session_state.index += 1

    if st.session_state.feedback_type == 'attribute' or st.session_state.feedback_type == 'comparative' or st.session_state.feedback_type == 'evaluative':
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
        


    
    elif st.session_state.feedback_type == 'keypoint':
        with st.expander('🔍 Annotation UI', expanded=True): 
            # col1, _, stchoose = st.columns([side, 2*width, side])
            # 生成图片
            video_path = st.session_state.query_info[st.session_state.index][1]
            img_path = str(video_path).replace(".mp4", "_img")
            video_to_frames(str(video_path), str(img_path))
            
            file_path = str(st.session_state.query_info[st.session_state.index][1]).replace(".mp4", "_img").replace("\\", "/")
            im_list = load_images(file_path)
            col1, stchoose = st.columns([2,3])
            stframe = col1.empty()
            frame_text = col1.empty()
            col1_path = str(st.session_state.query_info[st.session_state.index][1]).replace(".mp4", "_img"). \
                            replace("\\", "/") + f"/{st.session_state['image_index']}.jpg"
            stframe.image(col1_path)
            print(st.session_state['image_index'])
            frame_text.text(f"Current Frame：{st.session_state['image_index']}/{st.session_state['query_length'] -1}")
            
            
            if st.session_state["image_list"] != []:
                image_list = st.session_state["image_list"]
                index =  st.session_state['rank_result_via_prompt']
                if len(image_list)<=3:
                    cols = stchoose.columns(len(image_list))
                    for i in range(len(image_list)):
                        cols[i].image(image_list[i])
                        cols[i].text(f"frame{index[i]}")
                else:
                    cols = stchoose.columns(3)
                    for i in range(len(image_list)):
                        cols[i%3].image(image_list[i])
                        cols[i%3].text(f"frame{index[i]}")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                play = st.button(label="Play")
            with col2:
                pause = st.button(label="Pause")
            with col3:
                st.button(label="Previous", on_click=previous)
        
            with col4:
                st.button(label="Next", on_click=next_img)
                    
            with col5:
                st.button(label="choose frame", on_click=keyframe, args=(stchoose,))
                    # keyframe(stchoose)
            
            
            while play and not pause:
                stframe.image(im_list[st.session_state['image_index']])
                frame_text.text(
                    f"Current Frame：{st.session_state['image_index']}/{st.session_state['query_length'] -1}")
                st.session_state['image_index'] = (st.session_state['image_index']+1) % st.session_state['query_length'] 
                time.sleep(0.5)

        with st.expander('💡 Question', expanded=True):
            st.write(st.session_state.project_info["question"][0])
            st.session_state.label = str(st.session_state["rank_result_via_prompt"])
            st.button('Submit', on_click=save_and_next)


    

    elif st.session_state.feedback_type == 'visual':
        file_path = str(st.session_state.query_info[st.session_state.index][1]).replace(".mp4", "_img").replace("\\", "/")
        im_list = load_images(file_path)
        st.set_option("deprecation.showfileUploaderEncoding", False)
        idm = ImageDirManager(file_path)
        st.session_state.disabled_save_btn = True
        if "files" not in st.session_state:
            st.session_state["files"] = idm.get_all_files()
            st.session_state["files"] = sorted(st.session_state["files"], key=sort_by_number)
            st.session_state["annotation_files"] = idm.get_exist_annotation_files()
            st.session_state["image_index"] = 0
        else:
            idm.set_all_files(st.session_state["files"])
            idm.set_annotation_files(st.session_state["annotation_files"])

        n_files = len(st.session_state["files"])
        n_annotate_files = len(st.session_state["annotation_files"])

        col1, col2 = st.columns(2)
        with col1:
            stframe = st.empty()
            frame_text = st.empty()
            col1_path = str(st.session_state.query_info[st.session_state.index][1]).replace(".mp4", "_img"). \
                            replace("\\", "/") + f"/{st.session_state['image_index']}.jpg"
            stframe.image(col1_path, width=250)
            frame_text.text(f"Current Frame：{st.session_state['image_index']}/{st.session_state['query_length']-1}")
        with col2:
            # Main content: annotate images
            img_file_name = idm.get_image(st.session_state["image_index"])
            image_annotate_file_name = img_file_name.split(".")[0] + ".xml"
            if image_annotate_file_name in st.session_state["annotation_files"]:
                st.session_state["disabled_save_btn"] = True
            img_path = os.path.join(file_path, img_file_name)
            im = load_image_manager(img_path)#ImageManager(img_path)
            img = im.get_img()
            resized_img = im.resizing_img(300, 300)
            resized_rects = im.get_resized_rects()#im.get_resized_rects()
            rects = st_img_label(resized_img, box_color="red", rects=resized_rects)
            
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            play = st.button(label="Play")
        with col2:
            pause = st.button(label="Pause")
        with col3:
            st.button(label="Previous", on_click=previous_image)
        with col4:
            st.button(label="Next", on_click=next_image)
        # with col4:
        #     st.button(label="Next need annotate", on_click=next_annotate_file)
        with col5:
            st.button(label="Save", disabled=st.session_state["disabled_save_btn"], on_click=annotate, args=(rects, idm, im, img_file_name))
            
        

        while play and not pause:
            stframe.image(im_list[st.session_state['image_index']], width=250)
            frame_text.text(
                f"Current Frame：{st.session_state['image_index']}/{st.session_state['query_length']-1}")
            st.session_state['image_index'] = (st.session_state['image_index']+1) % st.session_state['query_length']
            time.sleep(0.5)
            
        
        if rects:
            st.session_state["disabled_save_btn"] = False
            preview_imgs = im.init_annotation(rects)
            for i, prev_img in enumerate(preview_imgs):
                im.set_annotation(i, "default")
                
        with st.expander('💡 Question', expanded=True):
            st.write(st.session_state.project_info["question"][0])
            st.session_state.label = str(st.session_state["rank_result_via_prompt"])
            st.button('Submit', on_click=save_and_next)
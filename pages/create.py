import streamlit as st
import os
import sys
import pathlib
import streamlit_tags
import shortuuid
import json
import csv

sys.path.append(str(pathlib.Path(__file__).parent.parent))

def generate_video(project_id, 
                domain, 
                task, 
                environment_name,
                mode="offline",
                sampler_type="random",
                feedback_type="comparative",
                query_num=2,
                query_length=100,
                fps=30,
                video_width=100,
                video_height=100,
                save_dir="./videos"):
    
    context = {}
    exec(f"from datasets.{mode}_{domain} import Dataset", context)
    Dataset = context['Dataset']
    
    # Instantiate the Dataset with the provided configuration
    dataset = Dataset(
        project_id=project_id,
        domain=domain,
        task=task,
        environment_name=environment_name,
        mode=mode,
        sampler_type=sampler_type,
        feedback_type=feedback_type,
        query_num=query_num,
        query_length=query_length,
        fps=fps,
        video_width=video_width,
        video_height=video_height,
        save_dir=save_dir
    )

    # Generate video resources
    video_info_list, video_url_list, query_id_list = dataset.generate_video_resources()

    # Check if the video resources are generated successfully
    if not video_info_list or not video_url_list or not query_id_list:
        raise ValueError("generate_video_resources did not return expected data")
    
    del dataset

    # You can return the lists if you want to use them outside this function
    return video_info_list, video_url_list, query_id_list

def save_video(project_info, save_dir="./data"):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    file_name = f"{project_info['project_name']}@{project_info['project_id']}.json"
    save_path = os.path.join(save_dir, file_name)
    with open(save_path, 'w') as json_file:
        json.dump(project_info, json_file)
    
    file_name = f"{project_info['project_name']}@{project_info['project_id']}.csv"
    save_path = os.path.join(save_dir, file_name)
    with open(save_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['video_info', 'video_url', 'query_id', 'task', 'label', 'annotated'])
        for info, url, query_id in zip(project_info['video_info'], project_info['video_url'], project_info['query_id']):
            # print(info, url, query_id)
            writer.writerow([info, url, query_id, project_info['task'], None,0])
        
st.set_page_config(page_title='🔨 Mini-Uni-RLHF (Create)', layout='wide')

domain_task_map = {
    'd4rl': ['mujoco', 'antmaze', 'adroit'],
    'vd4rl': ['walker', 'humanoid'],
    'smarts': ['smarts'],
    'atari': ['adventure', 'air-raid', 'alien', 'amidar', 'assault', 'asterix',
        'asteroids', 'atlantis', 'bank-heist', 'battle-zone', 'beam-rider',
        'berzerk', 'bowling', 'boxing', 'breakout', 'carnival', 'centipede',
        'chopper-command', 'crazy-climber', 'defender', 'demon-attack',
        'double-dunk', 'elevator-action', 'enduro', 'fishing-derby', 'freeway',
        'frostbite', 'gopher', 'gravitar', 'hero', 'ice-hockey', 'jamesbond',
        'journey-escape', 'kangaroo', 'krull', 'kung-fu-master',
        'montezuma-revenge', 'ms-pacman', 'name-this-game', 'phoenix',
        'pitfall', 'pong', 'pooyan', 'private-eye', 'qbert', 'riverraid',
        'road-runner', 'robotank', 'seaquest', 'skiing', 'solaris',
        'space-invaders', 'star-gunner', 'tennis', 'time-pilot', 'tutankham',
        'up-n-down', 'venture', 'video-pinball', 'wizard-of-wor',
        'yars-revenge', 'zaxxon']
}

info_placeholder = st.empty()

with st.expander('🔍 Create Project', expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        # project_id: text_input
        project_name = st.text_input('Project Name', value="Project #1")
        
        # domain: select_box
        domain_options = ['vd4rl', 'd4rl', 'atari', 'smarts']  
        domain = st.selectbox('Domain', options=domain_options)
        
        # task: select_box
        task = st.selectbox('Task', options=domain_task_map[domain])
        
        # environment_name: text_input
        environment_name = st.text_input('Environment Name', value="walker_walk_medium")
        
        # fps: select_slider
        fps_options = [10, 15, 25, 30, 50]  
        fps = st.select_slider('FPS', options=fps_options)

    with col2:
        # sampler_type: select_box
        sampler_type_options = ['random', 'disagreement']
        sampler_type = st.selectbox('Sampler Type', options=sampler_type_options)
        
        # feedback_type: select_box
        feedback_type_options = ['comparative', 'attribute', 'evaluative', 'visual', 'keypoint']
        feedback_type = st.selectbox('Feedback Type', options=feedback_type_options)
        
        # query_num: number_input
        query_num = st.number_input('Query Number', min_value=1, max_value=10)
        
        # query_length: number_input
        query_length = st.number_input('Query Length', min_value=10, max_value=100)
        
        # own_dataset: file_uploader 
        own_dataset = st.file_uploader("Upload your own hdf5 dataset (Optional)")

    with col3:
        # instruction: text_area
        instruction_text = '''**You see two videos of robots walking with the goal of moving as far to the right as possible while minimising energy costs**:  
        - If the robot is about to fall or is walking abnormally (e.g., walking on only one leg, slipping, etc.) while the other robot is walking normally, it should be considered the worse choice, even if it is moving farther than the other video robot.  
        - If you think both robots are walking robustly and normally, choose the better video based on how far the robot moved.  
        - If both robots in the two videos have shown an imminent fall or an abnormal state of walking, consider the robot that has maintained its normal standing posture for longer or has moved farther away to be the better choice.  
        - If the above rules still do not allow you to decide on a preference for clips, the equal option is allowed, giving an equal preference to both video clips.'''
        instruction = st.text_area(label="Please enter the instructions for the annotators:",
                                value=instruction_text,
                                height=200)
        # qustion = {caption: option}
        caption = st.text_input(label="Please enter the question for the annotators:",
                                value="Which of the two walker runs faster?")
        option = streamlit_tags.st_tags(label='Enter options for the question:  (optional)',
                            text='Press enter the options',
                            value=['Left', 'Equal', 'Right'],
                            maxtags=5)
        question = {caption: option}
        st.write("⬇️⬇️ If you want to add one more question, please press the button:")
        
        if 'rows' not in st.session_state:
            st.session_state['rows'] = 0

        def add_more_questions():
            st.session_state['rows'] += 1

        def display_more_questions(index):
            caption_temp = st.text_input(label="Please enter the question for the annotators:",
                                    value="Which of the two walker more like human?",
                                    key=f'caption_{index}')
            option_temp = streamlit_tags.st_tags(label='Enter options for the question:  (optional)',
                                            text='Press enter the options',
                                            maxtags=5,
                                            key=f'option_{index}')
            question.update({caption_temp:option_temp})
            
        st.button('Add more question', on_click=add_more_questions)  # todo
        
        for i in range(st.session_state['rows']):
            display_more_questions(i)


    _, col, _ = st.columns([1, 0.3, 1])
    with col:
        generate_button = st.button('Generate', type="primary")
        
    if generate_button:
        if not project_name or not environment_name:
            info_placeholder.error("Project ID and Environment Name cannot be empty.")
        else:
            with st.spinner('Wait for generation...'):
                info_placeholder.info("Start generating videos...")
                project_id = str(shortuuid.uuid())
                video_info_list, video_url_list, query_id_list = generate_video(project_id=project_id, domain=domain, task=task, environment_name=environment_name, sampler_type=sampler_type, feedback_type=feedback_type, query_num=query_num,
                query_length=query_length)
                # print(video_info_list, video_url_list, query_id_list)
                
                project_info_dict = {
                    "project_id": project_id,
                    "project_name": project_name,
                    "domain": domain,
                    "task": task,
                    "environment_name": environment_name,
                    "fps": fps,
                    "sampler_type": sampler_type,
                    "feedback_type": feedback_type,
                    "query_num": query_num,
                    "query_length": query_length,
                    "instruction": instruction,
                    "question": question,
                    "video_info": video_info_list,
                    "video_url": video_url_list,
                    "query_id": query_id_list
                }
                
                # save to json
                save_video(project_info_dict)

            info_placeholder.success("Create project successfully!")
            st.balloons()
            st.write('Full project info:')
            st.write(project_info_dict)
    
with st.expander('🔍 Your input', expanded=True):
    st.json({
        'Project Name': project_name,
        'Domain': domain,
        'Task': task,
        'Environment Name': environment_name,
        'Sampler Type': sampler_type,
        'Feedback Type': feedback_type,
        'Query Number': query_num,
        'Query Length': query_length,
        'FPS': fps
    })

    

import os
import random

import json
from builder_core import beauty_output, init_builder_chatbot_agent
from config_utils import Config, save_builder_configuration
from flask import Flask, Response, request
from server_utils import STATIC_FOLDER
from user_core import init_user_chatbot_agent

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')


@app.route('/preview/save/<uuid_str>', methods=['POST'])
def previewSave(uuid_str):
    builder_config_str = request.form.get('builder_config')
    builder_config = json.loads(builder_config_str)
    files = request.files.getlist('files')
    upload_dir = os.path.join('config', uuid_str, 'upload')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    for file in files:
        file.save(os.path.join(upload_dir, file.filename))
    save_builder_configuration(builder_cfg=builder_config, uuid_str=uuid_str)
    return json.dumps({
        'success': True,
    })


@app.route('/preview/chat/<uuid_str>', methods=['POST'])
def previewChat(uuid_str):
    req_data = request.get_json()
    input_param = req_data.get('content')

    def generate():
        seed = random.randint(0, 1000000000)
        user_agent = init_user_chatbot_agent(uuid_str)
        user_agent.seed = seed

        print('input_param:', input_param)
        response = ''
        is_final = False
        for frame in user_agent.stream_run(
                input_param, print_info=True, remote=False):
            print('frame:', frame)
            llm_result = frame.get('llm_text', '')
            exec_result = frame.get('exec_result', '')
            if len(exec_result) != 0:
                # action_exec_result
                if isinstance(exec_result, dict):
                    exec_result = str(exec_result['result'])
                frame_text = f'<result>{exec_result}</result>'
            else:
                # llm result
                frame_text = llm_result
            if frame.get('is_final', False):
                is_final = True

            # important! do not change this
            response += frame_text
            res = json.dumps({
                'data': response,
                'is_final': is_final,
            })
            yield f'data: {res}\n\n'

    return Response(generate(), mimetype='text/event-stream')


@app.route('/create/chat/<uuid_str>', methods=['POST'])
def createChat(uuid_str):
    req_data = request.get_json()
    input_param = req_data.get('content')

    def generate():
        builder_agent = init_builder_chatbot_agent(uuid_str)

        print('input_param:', input_param)
        response = ''
        is_final = False
        for frame in builder_agent.stream_run(
                input_param, print_info=True, uuid_str=uuid_str):
            llm_result = frame.get('llm_text', '')
            exec_result = frame.get('exec_result', '')
            step_result = frame.get('step', '')
            print(frame)
            if len(exec_result) != 0:
                if isinstance(exec_result, dict):
                    exec_result = exec_result['result']
                    assert isinstance(exec_result, Config)
                    builder_cfg = exec_result.to_dict()
                    save_builder_configuration(builder_cfg, uuid_str)
                    res = json.dumps({
                        'data': '',
                        'config': builder_cfg,
                    })
                    print('res:', res)
                    yield f'data: {res}\n\n'
            else:
                # llm result
                if isinstance(llm_result, dict):
                    content = llm_result['content']
                else:
                    content = llm_result
                if frame.get('is_final', False):
                    is_final = True
                frame_text = content
                response = beauty_output(f'{response}{frame_text}',
                                         step_result)
                res = json.dumps({
                    'data': response,
                    'is_final': is_final,
                })
                print('res:', res)
                yield f'data: {res}\n\n'

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)

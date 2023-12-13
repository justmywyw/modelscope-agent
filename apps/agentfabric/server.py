import os
import random

import json
from builder_core import beauty_output, init_builder_chatbot_agent
from config_utils import (Config, get_ci_dir, get_user_dir,
                          parse_configuration, save_builder_configuration)
from flask import (Flask, Response, jsonify, make_response, request,
                   send_from_directory)
from publish_util import pop_user_info_from_config, prepare_agent_zip
from server_utils import STATIC_FOLDER
from user_core import init_user_chatbot_agent

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')

ci_dir = get_ci_dir()
if not os.path.exists(ci_dir):
    os.makedirs(ci_dir)


@app.route('/preview/config/<uuid_str>')
def previewConfig(uuid_str):
    builder_cfg, model_cfg, tool_cfg, available_tool_list, _, _ = parse_configuration(
        uuid_str)
    return jsonify({
        'success': True,
        'data': {
            'builder_config': builder_cfg.to_dict(),
            'model_config': model_cfg.to_dict(),
            'tool_config': tool_cfg.to_dict(),
            'available_tool_list': available_tool_list,
        }
    })


# TODO: 用户文件鉴权
@app.route('/preview/config_files/<uuid_str>/<file_name>', methods=['GET'])
def previewGetFile(uuid_str, file_name):
    print('uuid_str:', uuid_str, 'file_name:', file_name)
    as_attachment = request.args.get('as_attachment') == 'true'
    directory = get_user_dir(uuid_str)
    try:
        response = make_response(
            send_from_directory(
                directory, file_name, as_attachment=as_attachment))
        return response
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 404,
            'message': str(e)
        }), 404


@app.route('/preview/save/<uuid_str>', methods=['POST'])
def previewSave(uuid_str):
    builder_config_str = request.form.get('builder_config')
    builder_config = json.loads(builder_config_str)
    files = request.files.getlist('files')
    upload_dir = get_user_dir(uuid_str)
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    for file in files:
        file.save(os.path.join(upload_dir, file.filename))
    save_builder_configuration(builder_cfg=builder_config, uuid_str=uuid_str)
    return jsonify({
        'success': True,
    })


@app.route('/preview/publish/zip/<uuid_str>', methods=['POST'])
def previewPublishGetZip(uuid_str):
    req_data = request.get_json()
    name = req_data.get('name')
    src_dir = os.path.abspath(os.path.dirname(__file__))
    user_info = pop_user_info_from_config(src_dir, uuid_str)
    print('user_info:', user_info)
    output_url = prepare_agent_zip(name, src_dir, uuid_str, None)
    return jsonify({'success': True, 'data': {'output_url': output_url}})


@app.route('/preview/chat/<uuid_str>', methods=['POST'])
def previewChat(uuid_str):
    params_str = request.form.get('params')
    params = json.loads(params_str)
    input_param = params.get('content')
    files = request.files.getlist('files')
    file_paths = []
    for file in files:
        file_path = os.path.join(get_ci_dir(), file.filename)
        file.save(file_path)
        file_paths.append(file_path)

    def generate():
        seed = random.randint(0, 1000000000)
        user_agent = init_user_chatbot_agent(uuid_str)
        user_agent.seed = seed

        print('input_param:', input_param)
        response = ''
        is_final = False
        for frame in user_agent.stream_run(
                input_param,
                print_info=True,
                remote=False,
                append_files=file_paths):
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
    params_str = request.form.get('params')
    params = json.loads(params_str)
    input_param = params.get('content')
    files = request.files.getlist('files')
    file_paths = []
    for file in files:
        file_path = os.path.join(get_ci_dir(), file.filename)
        file.save(file_path)
        file_paths.append(file_path)

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
                        'data': response,
                        'config': builder_cfg,
                        'is_final': is_final,
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

        final_res = json.dumps({
            'data': response,
            'is_final': True,
        })
        yield f'data: {final_res}\n\n'

    return Response(generate(), mimetype='text/event-stream')


@app.errorhandler(Exception)
def handle_error(error):
    # 处理错误并返回统一格式的错误信息
    error_message = {'success': False, 'message': str(error), 'status': 500}
    return jsonify(error_message), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

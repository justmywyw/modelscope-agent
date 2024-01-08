import os

from modelscope_agent.agent import Agent
from modelscope_agent.tools.style_repaint import StyleRepaint

print(os.getcwd())

from modelscope_agent.prompts.role_play import RolePlay  # NOQA


def test_style_repaint():
    # 图片默认上传到ci_workspace
    params = """{'input.image_path': './WechatIMG139.jpg', 'input.style_index': 0}"""

    style_repaint = StyleRepaint()
    res = style_repaint.call(params)
    assert (res.startswith('http'))


def test_style_repaint_role():
    role_template = '你扮演一个绘画家，用尽可能丰富的描述调用工具绘制各种风格的图画。'

    llm_config = {'model': 'qwen-max', 'model_server': 'dashscope'}

    # input tool args
    function_list = [{'name': 'style_repaint'}]

    bot = RolePlay(
        function_list=function_list, llm=llm_config, instruction=role_template)

    response = bot.run('[上传文件WechatIMG139.jpg],我想要清雅国风')
    text = ''
    for chunk in response:
        text += chunk
    print(text)
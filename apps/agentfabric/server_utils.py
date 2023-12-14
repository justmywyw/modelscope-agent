import os
import shutil

from builder_core import init_builder_chatbot_agent
from user_core import init_user_chatbot_agent

STATIC_FOLDER = 'statics'


def static_file(source_path):
    file_name = os.path.basename(source_path)
    target_path = os.path.join(STATIC_FOLDER, file_name)
    shutil.move(source_path, target_path)
    return file_name


# 简单进行内存级别的会话管理
class SessionManager():

    def __init__(self):
        self.builder_bots = {}
        self.user_bots = {}

    def get_builder_bot(self, uuid_str, renew=False):
        if (uuid_str not in self.builder_bots) or renew:
            self.builder_bots[uuid_str] = init_builder_chatbot_agent(uuid_str)
        return self.builder_bots[uuid_str]

    def clear_builder_bot(self, uuid_str):
        if uuid_str in self.builder_bots:
            del self.builder_bots[uuid_str]

    def get_user_bot(self, uuid_str, renew=False):
        if (uuid_str not in self.user_bots) or renew:
            self.user_bots[uuid_str] = init_user_chatbot_agent(uuid_str)
        return self.user_bots[uuid_str]

    def clear_user_bot(self, uuid_str):
        if uuid_str in self.user_bots:
            del self.user_bots[uuid_str]

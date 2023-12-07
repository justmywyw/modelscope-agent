import os
import shutil

STATIC_FOLDER = 'statics'


def static_file(source_path):
    file_name = os.path.basename(source_path)
    target_path = os.path.join(STATIC_FOLDER, file_name)
    shutil.move(source_path, target_path)
    return file_name

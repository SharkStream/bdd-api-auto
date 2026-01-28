import json
import os

def read_json_file(file_path: str) -> str:
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}
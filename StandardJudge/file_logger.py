from typing import Union
from os import path

file_path = "./sql_grader_log.txt"

def init():
    with open(file_path, 'w') as file:
        file.write("")

def log(header : Union[str, None], *args, **kwargs):
    if path.exists(file_path):
        with open(file_path, 'a') as file:
            if header != None:
                print(f"[{header}]", file=file, end = " ")
            print(*args, **kwargs, file=file)
import os
import sys

def add_app_to_path(levels):
    path = os.path.abspath(__file__)
    for _ in range(levels):
        path = os.path.dirname(path)
    sys.path.append(path)
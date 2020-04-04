import os

files = os.listdir(os.path.dirname(os.path.realpath(__file__)))
__all__ = [file[:-3] for file in files if file.endswith("Commands.py")]

import os
import re


def replace_ext(path, ext):
    if not ext.startswith("."):
        ext = "." + ext
    root = os.path.splitext(path)[0]
    return root + ext


def extract_integer(text):
    m = re.search(r"\d+", text)
    return m.group(0) if m else text

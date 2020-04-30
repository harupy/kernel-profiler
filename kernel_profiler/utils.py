import os
import re


def replace_ext(path, ext):
    if not ext.startswith("."):
        ext = "." + ext
    root = os.path.splitext(path)[0]
    return root + ext


def extract_int(text):
    m = re.search(r"\d+", text)
    if m is not None:
        return m.group(0)

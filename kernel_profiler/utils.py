import os
import re

import jupytext


def replace_ext(path, ext):
    if not ext.startswith("."):
        ext = "." + ext
    root = os.path.splitext(path)[0]
    return root + ext


def extract_int(text):
    m = re.search(r"\d+", text)
    if m is not None:
        return m.group(0)


def markdown_to_notebook(md_path, nb_path):
    notebook = jupytext.read(md_path, fmt="md")
    jupytext.write(notebook, nb_path)

import os
import re

import jupytext


def replace_ext(path, ext):
    """
    Examples
    --------
    >>> replace_ext("foo.md", ".ipynb")
    'foo.ipynb'

    >>> replace_ext("foo.md", "ipynb")
    'foo.ipynb'

    """
    if not ext.startswith("."):
        ext = "." + ext
    root = os.path.splitext(path)[0]
    return root + ext


def extract_int(text):
    """
    Examples
    --------
    >>> extract_int("ver 1")
    '1'

    >>> extract_int("ver 10")
    '10'

    >>> extract_int("ver") is None
    True

    """
    m = re.search(r"\d+", text)
    if m is not None:
        return m.group(0)


def extract_public_score(s):
    """
    Examples
    --------
    >>> extract_public_score('"publicScore":"0.123"')
    '0.123'

    >>> extract_public_score("") is None
    True

    """
    m = re.search(r'"publicScore":"(.+?)"', s)
    if m is not None:
        return m.group(1)


def extract_best_public_score(s):
    """
    Examples
    --------
    >>> extract_best_public_score('"bestPublicScore":0.123,')
    '0.123'

    >>> extract_best_public_score("") is None
    True

    """
    m = re.search(r'"bestPublicScore":([^,]+)', s)
    if m is not None:
        return m.group(1)


def markdown_to_notebook(md_path, nb_path):
    """
    Examples
    --------
    >>> import os
    >>> import tempfile
    >>>
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     md_path = os.path.join(tmpdir, "foo.md")
    ...     nb_path = os.path.join(tmpdir, "foo.ipynb")
    ...
    ...     with open(md_path, "w") as f:
    ...         _ = f.write("# Title")
    ...
    ...     markdown_to_notebook(md_path, nb_path)
    ...     os.path.exists(nb_path)
    True

    """
    notebook = jupytext.read(md_path, fmt="md")
    jupytext.write(notebook, nb_path)


def round_run_time(run_time_str):
    """
    Examples
    --------
    >>> round_run_time("59s")
    '59.0 s'

    >>> round_run_time("60s")
    '1.0 m'

    >>> round_run_time("3599s")
    '60.0 m'

    >>> round_run_time("3600s")
    '1.0 h'

    """
    run_time = float(run_time_str[:-1])

    if run_time < 60:
        return f"{run_time} s"
    elif run_time >= 60 and run_time < 3600:
        return f"{round(run_time / 60, 1)} m"
    else:
        return f"{round(run_time / 3600, 1)} h"

import os

from kernel_profiler import utils


def test_replace_ext():
    assert utils.replace_ext("a.txt", ".png") == "a.png"
    assert utils.replace_ext("a.txt", "png") == "a.png"


def test_extract_int():
    assert utils.extract_int("1 day") == "1"
    assert utils.extract_int("10 days") == "10"
    assert utils.extract_int("x") is None


def test_extract_public_score():
    assert utils.extract_public_score('"publicScore":"0.123"') == "0.123"


def test_extract_best_public_score():
    assert utils.extract_best_public_score('"bestPublicScore":0.123,') == "0.123"


def test_markdown_to_notebook(tmpdir):
    md_path = os.path.join(tmpdir, "test.md")
    nb_path = os.path.join(tmpdir, "test.ipynb")

    with open(md_path, "w") as f:
        f.write("# Test")

    utils.markdown_to_notebook(md_path, nb_path)
    assert os.path.exists(nb_path)


def test_round_run_time():
    assert utils.round_run_time("59s") == "59.0 s"
    assert utils.round_run_time("60s") == "1.0 m"
    assert utils.round_run_time("3599s") == "60.0 m"
    assert utils.round_run_time("3600s") == "1.0 h"

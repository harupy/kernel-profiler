from kernel_profiler import utils


def test_replace_ext():
    assert utils.replace_ext("a.txt", ".png") == "a.png"
    assert utils.replace_ext("a.txt", "png") == "a.png"


def test_extract_int():
    assert utils.extract_int("1 day") == "1"
    assert utils.extract_int("10 days") == "10"
    assert utils.extract_int("x") is None

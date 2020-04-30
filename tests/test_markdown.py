from kernel_profiler import markdown as md


def test_make_row():
    assert md.make_row(["a", "b"]) == "|a|b|"


def test_make_link():
    assert md.make_link("text", "https://url.com")


def test_make_table():
    data = [(1, 2), (3, 4)]
    headers = ["a", "b"]

    actual = md.make_table(data, headers)
    expected = "\n".join(["|a|b|", "| :-- | :-- |", "|1|2|", "|3|4|"])
    assert actual == expected

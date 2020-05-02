def make_link(text, url):
    """
    Examples
    --------
    >>> make_link("foo", "https://foo.com")
    '[foo](https://foo.com)'

    """
    return f"[{text}]({url})"


def make_row(items):
    """
    Examples
    --------
    >>> make_row(["a", "b"])
    '|a|b|'

    >>> make_row([0, 1])
    '|0|1|'

    """
    return "|".join(["", *map(str, items), ""])


def make_table(data, headers):
    """
    Examples
    --------
    >>> print(make_table([("a", "b")], ["x", "y"]))
    |x|y|
    | :-- | :-- |
    |a|b|

    """
    return "\n".join(
        [make_row(headers), make_row([" :-- "] * len(headers)), *map(make_row, data)]
    )

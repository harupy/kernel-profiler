def make_link(text, url):
    return f"[{text}]({url})"


def make_row(items):
    return "|".join(["", *map(str, items), ""])


def make_table(data, headers):
    return "\n".join(
        [make_row(headers), make_row([" :-- "] * len(headers)), *map(make_row, data)]
    )

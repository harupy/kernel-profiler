from kernel_profiler import html
import re


def test_format_attributes():
    assert html.format_attributes({"a": "b", "c": "d"}) == 'a="b" c="d"'
    assert html.format_attributes({"a": 0, "c": 1}) == 'a="0" c="1"'


def test_make_img_tag():
    src = "https://src.com/src.png"
    assert html.make_image_tag({"src": src}) == f'<img src="{src}">'


def test_make_anchor_tag():
    href = "https://src.com/src.png"
    assert html.make_anchor_tag("a", {"href": href}) == f'<a href="{href}">a</a>'


def test_make_thumbnail():
    template = "https://src.com/{}.png"
    thumbnail_src = template.format("thumbnail")
    tier_src = template.format("tier")
    author_url = template.format("author")

    actual = html.make_thumbnail(thumbnail_src, tier_src, author_url)
    expected = """
<a href="{}" style="display: inline-block">
  <img src="{}" width="72">
  <img src="{}" width="72">
</a>
""".format(
        author_url, thumbnail_src, tier_src
    )
    expected = re.sub(r"^\s+|\n", "", expected, flags=re.MULTILINE)
    assert actual == expected

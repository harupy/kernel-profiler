def format_attributes(attrs):
    """
    Examples
    --------
    >>> format_attributes({"a": "b", "c": "d"})
    'a="b" c="d"'

    """
    return " ".join([f'{key}="{val}"' for key, val in attrs.items()])


def make_image_tag(attrs):
    """
    Examples
    --------
    >>> make_image_tag({"src": "https://src.com/src.png"})
    '<img src="https://src.com/src.png">'

    """
    return f"<img {format_attributes(attrs)}>"


def make_anchor_tag(content, attrs):
    """
    Examples
    --------
    >>> make_anchor_tag("anchor", {"href": "https://href.com"})
    '<a href="https://href.com">anchor</a>'

    """
    return f"<a {format_attributes(attrs)}>{content}</a>"


def make_thumbnail(thumbnail_src, tier_src, author_url):
    """
    Examples
    --------
    >>> make_thumbnail("thumbnail.com", "tier.com", "author.com")
    '<a href="author.com" style="display: inline-block">\
<img src="thumbnail.com" width="72">\
<img src="tier.com" width="72">\
</a>'

    """
    thumbnail = make_image_tag({"src": thumbnail_src, "width": 72})
    tier = make_image_tag({"src": tier_src, "width": 72})
    return make_anchor_tag(
        thumbnail + tier, {"href": author_url, "style": "display: inline-block"}
    )

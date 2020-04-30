def format_attributes(attrs):
    return " ".join([f'{key}="{val}"' for key, val in attrs.items()])


def make_image_tag(attrs):
    return f"<img {format_attributes(attrs)}>"


def make_anchor_tag(content, attrs):
    return f"<a {format_attributes(attrs)}>{content}</a>"


def make_thumbnail(thumbnail_src, tier_src, author_url):
    thumbnail = make_image_tag({"src": thumbnail_src, "width": 72})
    tier = make_image_tag({"src": tier_src, "width": 72})
    return make_anchor_tag(
        thumbnail + tier, {"href": author_url, "style": "display: inline-block"}
    )

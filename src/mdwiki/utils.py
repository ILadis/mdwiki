
from mkdocs.utils import meta

def get_posts(files):
    posts = list()

    for file in files.documentation_pages():
        source = file.content_string
        _, data = meta.get_data(source)

        post = dict(
            title = data.get('title'),
            summary = data.get('summary'),
            date = data.get('date'),
            tags = data.get('tags', []),
            url = file.url)

        posts.append(post)

    return posts

def get_tags(files):
    tags = set()

    for file in files.documentation_pages():
        source = file.content_string
        _, data = meta.get_data(source)

        for tag in data.get('tags', []):
            tags.add(tag)

    return tags

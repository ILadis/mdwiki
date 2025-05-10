
import os.path
import hashlib

from datetime import datetime
from mkdocs.utils import meta

def get_note_id(file):
    return int(os.stat(file.abs_src_path).st_ino)

def get_note_etag(file):
    etag = hashlib.md5()

    name = file.name.encode('utf-8')
    if len(name) > 0:
        etag.update(name)

    content = file.content_string.encode('utf-8')
    if len(content) > 0:
        etag.update(content)

    return str(etag.hexdigest())

def get_note(file):
    noteid = get_note_id(file)
    etag = get_note_etag(file)
    modified = int(os.path.getmtime(file.abs_src_path))

    # TODO consider using typed dicts
    note = dict()
    note['id'] = noteid
    note['title'] = file.name
    note['content'] = file.content_string
    note['category'] = ''
    note['readonly'] = False
    note['favorite'] = False
    note['modified'] = modified
    note['etag'] = etag

    return note

def get_posts(files):
    posts = list()

    for file in files.documentation_pages():
        source = file.content_string
        _, data = meta.get_data(source)

        post = dict()
        # TODO use same source for fallbacks
        post['title'] = data.get('title', 'Untitled')
        post['summary'] = data.get('summary', '')
        post['date'] = data.get('date', datetime.fromisoformat('1970-01-01'))
        post['tags'] = data.get('tags', [])
        post['url'] = file.url

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

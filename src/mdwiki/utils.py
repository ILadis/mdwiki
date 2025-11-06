
import os, os.path
import logging
import datetime
import hashlib
import types

from mkdocs.utils import meta

def get_file_id(file):
    return int(os.stat(file.abs_src_path).st_ino)

def get_file_etag(file):
    etag = hashlib.md5()

    name = file.name.encode('utf-8')
    if len(name) > 0:
        etag.update(name)

    content = file.content_string.encode('utf-8')
    if len(content) > 0:
        etag.update(content)

    return str(etag.hexdigest())

def get_note(file):
    fid = get_file_id(file)
    etag = get_file_etag(file)
    modified = int(os.path.getmtime(file.abs_src_path))

    note = dict()
    note['id'] = fid
    note['title'] = file.name
    note['content'] = file.content_string
    note['category'] = ''
    note['readonly'] = False
    note['favorite'] = False
    note['modified'] = modified
    note['etag'] = etag

    return note

def get_post(file):
    source = file.content_string
    _, data = meta.get_data(source)

    fid = get_file_id(file)
    title = data.get('title', file.name)
    summary = data.get('summary', '')
    date = data.get('date')
    tags = data.get('tags')

    if not isinstance(date, datetime.date):
        timestamp = int(os.path.getmtime(file.abs_src_path))
        date = datetime.date.fromtimestamp(timestamp)
    if not isinstance(tags, list):
        tags = list()

    post = dict()
    post['id'] = fid
    post['title'] = title
    post['summary'] = summary
    post['date'] = date
    post['tags'] = tags
    post['url'] = file.url

    return post

def get_posts(files):
    posts = list()

    for file in files.documentation_pages():
        post = get_post(file)
        posts.append(post)

    return posts

def get_tags(files):
    tags = set()

    for file in files.documentation_pages():
        post = get_post(file)

        for tag in post['tags']:
            tags.add(tag)

    return tags

def setup_logging(stream, level, pattern):
    levels = {
        'debug': logging.DEBUG,
        'info':  logging.INFO,
        'warn':  logging.WARNING,
        'error': logging.ERROR
    }

    # stips timestamps from live reload server logs
    def formatMessage(self, record):
        if record.name == 'mkdocs.livereload':
            record.message = record.msg[11:]
        return self._style.format(record)

    formatter = logging.Formatter(pattern)
    formatter.formatMessage = types.MethodType(formatMessage, formatter)

    logger = logging.getLogger('mkdocs')
    logger.setLevel(levels[level])

    handler = logging.getHandlerByName('MkDocsStreamHandler')

    if handler is None:
        handler = logging.StreamHandler()
        handler.name = 'MkDocsStreamHandler'
        logger.addHandler(handler)

    handler.setStream(stream)
    handler.setFormatter(formatter)

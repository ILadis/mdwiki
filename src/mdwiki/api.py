
import os, pathlib
import json

from mkdocs.structure.files import File

from mdwiki.utils import get_note, get_note_id
from mdwiki.http import safe_get, urlpath_matcher

# For API specs see:
# https://github.com/nextcloud/notes/blob/main/docs/api/v1.md

class Capabilities:
    def __init__(self, config):
        self.path = urlpath_matcher(config.site_url or '/', 'ocs/v2.php/cloud/capabilities')
        self.capabilities = '''
            {
                "ocs": {
                    "data": {
                        "capabilities": {
                            "notes": {
                                "api_version": ["1.1"],
                                "version": "3.6.0"
                            }
                        }
                    }
                }
            }
            '''

    def __call__(self, request, response):
        path = self.path.fullmatch(request.path)
        if not path or request.method != 'GET':
            return False

        response.status = '200 OK'
        response.headers['Content-Type'] = 'application/json'
        response.body = self.capabilities

        return True

class ListNotes:
    def __init__(self, config, files = None):
        self.methods = ['GET']
        self.path = urlpath_matcher(config.site_url or '/', 'index.php/apps/notes/api/v1/notes')
        self.files = files

    def __call__(self, request, response):
        path = self.path.fullmatch(request.path)
        if not path or request.method not in self.methods:
            return False

        category = request.query('category', default = '')
        exclude = request.query('exclude', default = '').split(',')
        prune = request.query('pruneBefore', default = '-inf', pattern = '[0-9]+')

        notes = list()

        for page in self.files.documentation_pages():
            note = get_note(page)

            # default note category is an empty string
            if note['category'] == category:
                notes.append(note)

            # exclude (prune) all keys except id if note is to old
            if note['modified'] < float(prune):
                excludes = set(note.keys())
                excludes.remove('id')
            # otherwise use default exclude from query parameter
            else:
                excludes = (field for field in exclude if field in note)

            for field in excludes:
                note.pop(field)

        response.status = '200 OK'
        response.headers['Content-Type'] = 'application/json'
        response.body = json.dumps(notes)

        return True

class UpdateNotes:
    def __init__(self, config, files = None):
        self.methods = ['GET', 'PUT', 'DELETE']
        self.path = urlpath_matcher(config.site_url or '/', 'index.php/apps/notes/api/v1/notes/([0-9]+)')
        self.files = files

    def __call__(self, request, response):
        path = self.path.fullmatch(request.path)
        if not path or request.method not in self.methods:
            return False

        file = None
        pathid = int(path.group(1))

        for page in self.files.documentation_pages():
            noteid = get_note_id(page)

            if noteid == pathid:
                file = page
                break

        if not file:
            response.status = '404 Not Found'
            response.body = ''

        elif request.method == 'PUT':
            length = request.header('content-length', pattern = '[0-9]+')
            note = json.loads(request.body.read(int(length)))

            title = safe_get(note, 'title', pattern = '[a-zA-Z0-9 _-]*')
            content = safe_get(note, 'content')

            if title == '':
                title = 'Untitled'

            path = pathlib.Path(file.abs_src_path)
            path.write_text(content)

            newpath = path.parent.joinpath(title + '.md')
            if not newpath.is_file():
                path.rename(newpath)

            file.name = title
            file.content_string = content
            file.abs_src_path = str(newpath)

            note = get_note(file)

            response.status = '200 OK'
            response.headers['Content-Type'] = 'application/json'
            response.body = json.dumps(note)

        elif request.method == 'GET':
            note = get_note(file)

            response.status = '200 OK'
            response.headers['Content-Type'] = 'application/json'
            response.body = json.dumps(note)

        elif request.method == 'DELETE':
            os.remove(file.abs_src_path)

            response.status = '200 OK'
            response.body = ''

        return True

class CreateNotes:
    def __init__(self, config):
        self.methods = ['POST']
        self.path = urlpath_matcher(config.site_url or '/', 'index.php/apps/notes/api/v1/notes')
        self.config = config

    def __call__(self, request, response):
        path = self.path.fullmatch(request.path)
        if not path or request.method not in self.methods:
            return False

        length = request.header('content-length', pattern = '[0-9]+')
        note = json.loads(request.body.read(int(length)))

        title = safe_get(note, 'title', pattern = '[a-zA-Z0-9 _-]*')
        content = safe_get(note, 'content')
        category = safe_get(note, 'category', default = '')

        # TODO use same source for fallback title
        if title == '':
            title = 'Untitled'

        path = pathlib.Path(self.config.docs_dir)
        path = path.joinpath(title + '.md')

        # do not overwrite already existing files
        if path.is_file():
            response.status = '400 Bad Request'
            response.body = ''

        else:
            path.write_text(content)

            file = File.generated(self.config, path.name, abs_src_path = str(path))
            note = get_note(file)

            response.status = '200 OK'
            response.headers['Content-Type'] = 'application/json'
            response.body = json.dumps(note)

        return True

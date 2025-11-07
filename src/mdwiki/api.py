
import os, re
import pathlib
import json

from mkdocs.structure.files import File

from mdwiki.utils import get_note, get_file_id, get_file_etag
from mdwiki.http import safe_get, urlpath_matcher

# for API specs see:
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
    def __init__(self, config, files=None):
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
    def __init__(self, config, files=None):
        self.methods = ['GET', 'PUT', 'DELETE']
        self.path = urlpath_matcher(config.site_url or '/', 'index.php/apps/notes/api/v1/notes/([0-9]+)')
        self.files = files

    def __call__(self, request, response):
        path = self.path.fullmatch(request.path)
        if not path or request.method not in self.methods:
            return False

        file = None
        pathid = int(path.group(1))
        etag = request.header('if-match', pattern='"[a-f0-9]{1,32}"', default=False)

        for page in self.files.documentation_pages():
            noteid = get_file_id(page)

            if noteid == pathid:
                file = page
                break

        if not file:
            response.status = '404 Not Found'
            response.body = ''

        elif etag and etag[+1:-1] != get_file_etag(file):
            response.status = '412 Precondition Failed'
            response.body = ''

        elif request.method == 'PUT':
            length = request.header('content-length', pattern='[0-9]+')
            note = json.loads(request.body.read(int(length)))

            title = safe_get(note, 'title', pattern='[a-zA-Z0-9 _-]*') or 'Untitled'
            content = safe_get(note, 'content')

            path = pathlib.Path(file.abs_src_path)
            path.write_text(content)

            newpath = path.parent.joinpath(title + '.md')
            if not newpath.is_file():
                path.rename(newpath)

            file.name = title
            file._content = content
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
            self.files.remove(file)

            response.status = '200 OK'
            response.body = ''

        return True

class CreateNotes:
    def __init__(self, config, files=None):
        self.methods = ['POST']
        self.path = urlpath_matcher(config.site_url or '/', 'index.php/apps/notes/api/v1/notes')
        self.config = config
        self.files = files

    def __call__(self, request, response):
        path = self.path.fullmatch(request.path)
        if not path or request.method not in self.methods:
            return False

        length = request.header('content-length', pattern='[0-9]+')
        note = json.loads(request.body.read(int(length)))

        title = safe_get(note, 'title', pattern='[a-zA-Z0-9 _-]*') or 'Untitled'
        content = safe_get(note, 'content')
        category = safe_get(note, 'category', default='')

        path = pathlib.Path(self.config.docs_dir)
        path = path.joinpath(title + '.md')

        # do not overwrite already existing files
        if path.is_file():
            response.status = '400 Bad Request'
            response.body = ''

        else:
            path.write_text(content)

            file = File.generated(self.config, path.name, abs_src_path = str(path))
            file._content = content
            self.files.append(file)

            note = get_note(file)

            response.status = '200 OK'
            response.headers['Content-Type'] = 'application/json'
            response.body = json.dumps(note)

        return True

class TickCheckbox:
    def __init__(self, config, files=None):
        self.methods = ['POST']
        self.path = urlpath_matcher(config.site_url or '/', 'index.php/apps/notes/api/v1/notes/([0-9]+)/checkboxes/([0-9]+)/(un)?tick')
        self.checkbox = re.compile(r'^[ ]*[*+-][ ]+\[([ Xx])\]', re.M)
        self.files = files

    def __call__(self, request, response):
        path = self.path.fullmatch(request.path)
        if not path or request.method not in self.methods:
            return False

        file = None
        match = None

        pathid = int(path.group(1))
        boxnum = int(path.group(2))
        untick = bool(path.group(3))

        for page in self.files.documentation_pages():
            noteid = get_file_id(page)

            if noteid != pathid:
                continue

            file = page
            content = file.content_string

            while boxnum > 0:
                offset = 0 if match is None else match.end(1)
                match  = self.checkbox.search(content, offset)
                boxnum = boxnum - 1 if match else 0
            break

        if not file:
            response.status = '404 Not Found'
            response.body = ''

        elif not match:
            response.status = '400 Bad Request'
            response.body = ''

        else:
            start = file.content_string[:match.start(1)]
            end   = file.content_string[match.end(1):]

            content = start + (' ' if untick else 'x') + end
            file._content = content

            path = pathlib.Path(file.abs_src_path)
            path.write_text(content)

            response.status = '200 OK'
            response.body = ''

        return True

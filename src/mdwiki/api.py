
import json, re

from mdwiki.utils import get_note, get_note_id

# For API specs see:
# https://github.com/nextcloud/notes/blob/main/docs/api/v1.md

class Capabilities:
    def __init__(self):
        self.path = '/ocs/v2.php/cloud/capabilities'
        self.capabilities = '''
            {
                "ocs": {
                    "data": {
                        "capabilities": {
                            "notes": {
                                "api_version": ["1.3"],
                                "version": "3.6.0"
                            }
                        }
                    }
                }
            }
            '''

    def __call__(self, request, response):
        if request.method != 'GET' or request.path != self.path:
            return False

        response.status = '200 OK'
        response.headers['Content-Type'] = 'application/json'
        response.body = self.capabilities

        return True

class ListNotes:
    def __init__(self, files = None):
        self.files = files
        self.path = '/index.php/apps/notes/api/v1/notes'

    def __call__(self, request, response):
        if request.method != 'GET' or request.path != self.path:
            return False

        notes = list()

        for file in self.files.documentation_pages():
            note = get_note(file)
            notes.append(note)

        response.status = '200 OK'
        response.headers['Content-Type'] = 'application/json'
        response.body = json.dumps(notes)

        return True

class UpdateNotes:
    def __init__(self, files = None):
        self.files = files
        self.path = '/index.php/apps/notes/api/v1/notes/([1-9][0-9]*)'

    def __call__(self, request, response):
        if request.method != 'PUT':
            return False

        path = re.fullmatch(self.path, request.path)
        if path is None:
            return False

        file = None
        pathid = int(path.group(1))

        for f in self.files.documentation_pages():
            noteid = get_note_id(f)

            if noteid == pathid:
                file = f
                break

        if file is None:
            response.status = '404 Not Found'
            response.body = ''

        else:
            note = json.loads(request.body.read())

            with open(file.abs_src_path, 'wt') as f:
                f.write(note['content'])

            response.status = '200 OK'
            response.body = json.dumps(note)

        return True

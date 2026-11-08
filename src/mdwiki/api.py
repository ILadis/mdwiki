
import re, os.path
import json

from mdwiki.http import safe_get, urlpath_matcher

class PublicAccess:
    def __init__(self, config, files=None):
        self.methods = ['HEAD', 'GET', 'PUT', 'POST', 'DELETE']
        self.path = urlpath_matcher(config.site_url or '/', '.*')
        self.whitelist = ['index.html', 'tags.html', 'script.js', 'styles.css', 'favicon.ico']
        self.files = files

    def __call__(self, request, response):
        path = request.path
        authz = request.header('authorization', pattern='(Basic|Bearer) .+', default=False)
        referer = request.header('referer', default='/')

        # for HTTP templates to render public versions of pages
        request.params['public'] = False if authz else True

        # if valid authz header is present all resources are accessible
        if authz: return False

        accessible = False
        resource = os.path.basename(path) or 'index.html'

        file = self.files.file_by_path(path)
        reffile = self.files.file_by_path(referer)

        # check that referer page actually contains a link to resource
        if not file and reffile and resource in reffile.content_string:
            file = reffile

        # if page/post is marked as public it is accessible
        if file:
            post = self.files.post_by_file(file)
            accessible = post.get('public') is True
        # if resource is whitelisted it is accessible
        elif resource in self.whitelist:
            accessible = True

        if not accessible:
            response.status = '403 Forbidden'
            response.body = ''
            return True

        return False

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

        category = request.query('category', default='')
        exclude = request.query('exclude', default='').split(',')
        prune = request.query('pruneBefore', default='-inf', pattern='[0-9]+')

        notes = list()

        for note in self.files.all_notes():
            # default note category is an empty string
            if note['category'] == category:
                notes.append(note)

            # exclude (prune) all keys except id if note is too old
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

        uid = int(path.group(1))
        etag = request.header('if-match', pattern='"[a-f0-9]{1,32}"', default=False)
        agent = request.header('user-agent', default='')

        # disable etags for quillpad (does not currently handle 4xx responses)
        if 'okhttp' in agent:
            etag = False

        note = self.files.note_by_uid(uid)

        if not note:
            response.status = '404 Not Found'
            response.body = ''

        elif etag and etag[+1:-1] != note.get('etag'):
            response.status = '412 Precondition Failed'
            response.body = ''

        elif request.method == 'PUT':
            length = request.header('content-length', pattern='[0-9]+')
            body = json.loads(request.body.read(int(length)))

            title = safe_get(body, 'title', pattern='[a-zA-Z0-9 _-]*') or 'Untitled'
            content = safe_get(body, 'content')

            note = self.files.update_note(uid, title=title, content=content)

            response.status = '200 OK'
            response.headers['Content-Type'] = 'application/json'
            response.body = json.dumps(note)

        elif request.method == 'GET':
            response.status = '200 OK'
            response.headers['Content-Type'] = 'application/json'
            response.body = json.dumps(note)

        elif request.method == 'DELETE':
            self.files.delete_note(uid)

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
        body = json.loads(request.body.read(int(length)))

        title = safe_get(body, 'title', pattern='[a-zA-Z0-9 _-]*') or 'Untitled'
        content = safe_get(body, 'content')
        category = safe_get(body, 'category', default='')

        note = self.files.create_note(title=title, content=content, category=category)

        if not note:
            response.status = '400 Bad Request'
            response.body = ''

        else:
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

        uid = int(path.group(1))
        boxnum = int(path.group(2))
        untick = bool(path.group(3))

        note = self.files.note_by_uid(uid)
        title = note.get('title') if note else ''
        content = note.get('content') if note else ''

        match = None
        while boxnum > 0:
            offset = 0 if match is None else match.end(1)
            match  = self.checkbox.search(content, offset)
            boxnum = boxnum - 1 if match else 0

        if not note:
            response.status = '404 Not Found'
            response.body = ''

        elif not match:
            response.status = '400 Bad Request'
            response.body = ''

        else:
            start = content[:match.start(1)]
            end   = content[match.end(1):]

            content = start + (' ' if untick else 'x') + end
            self.files.update_note(uid, title=title, content=content)

            response.status = '200 OK'
            response.body = ''

        return True

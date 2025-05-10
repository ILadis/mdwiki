
import logging, re
import pathlib, urllib.parse

class HttpRouter:
    def __init__(self):
        self.handlers = list()
        self.logger = logging.getLogger('mkdocs.plugins.mdwiki')

    def add_handler(self, handler):
        self.handlers.append(handler)

    def attach_to(self, server):
        delegate = server.get_app()

        def handler(environ, start_response):
            # Wait until the ongoing rebuild (if any) finishes
            with server._epoch_cond:
                server._epoch_cond.wait_for(lambda: server._visible_epoch == server._wanted_epoch)

            request = HttpRequest(environ)
            response = HttpResponse()

            for handler in self.handlers :
                if handler(request, response) is True:
                    self.logger.info('Handled request: %s %s -> %s', request.method, request.path, response.status)

                    headers = list(response.headers.items())
                    body = [response.body.encode('utf-8')]
                    start_response(response.status, headers)
                    return body

            return delegate(environ, start_response)

        server.set_app(handler)

class HttpRequest:
    def __init__(self, environ):
        self.method = environ['REQUEST_METHOD']
        self.path = environ['PATH_INFO']
        self.params = parse_query(environ)
        self.headers = parse_headers(environ)
        self.body = environ['wsgi.input']

    def query(self, key, **kwargs):
        return safe_get(self.params, key, **kwargs)

    def header(self, key, **kwargs):
        return safe_get(self.headers, key, **kwargs)

class HttpResponse:
    def __init__(self):
        self.status = '200 OK'
        self.headers = dict()
        self.body = None

def parse_query(environ):
    query = urllib.parse.parse_qsl(environ['QUERY_STRING'])
    return dict(query)

def parse_headers(environ):
    headers = dict()
    extras = ['CONTENT_LENGTH']

    for key in environ:
        if key.startswith('HTTP_') or key in extras:
            name = key.replace('HTTP_', '', 1).lower().replace('_', '-')
            value = environ[key]
            headers[name] = value

    return headers

def safe_get(values, key, *, pattern = None, default = None):
    value = values.get(key, None)
    if value is None:
        if default is None:
            raise Exception(f'"{key}" is required but not present')
        return default

    if pattern is not None and not re.fullmatch(pattern, value):
        raise Exception(f'"{key}" does not match required pattern: {pattern}')

    return value

def urlpath_matcher(url, path):
    base = urllib.parse.urlsplit(url)
    url = pathlib.Path(base.path).joinpath(path)

    return re.compile(str(url))

class HttpTemplate:
    def __init__(self, name):
        self.name = name
        self.path = '/' + name

    def __call__(self, request, response):
        if request.method != 'GET' or request.path != self.path:
            return False

        context = dict(self.context)
        context['request'] = request

        content = self.template.render(context)

        response.status = '200 OK'
        response.headers['Content-Type'] = 'text/html'
        response.body = content

        return True

    def set_template(self, name, template):
        if self.name == name:
            self.template = template

    def set_context(self, name, context):
        if self.name == name:
            self.context = context

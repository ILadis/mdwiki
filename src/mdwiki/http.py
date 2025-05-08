
import logging
import urllib.parse

class HttpRouter:
    def __init__(self):
        self.handlers = list()
        self.logger = logging.getLogger('mkdocs.plugins.mdwiki')

    def add_handler(self, handler):
        self.handlers.append(handler)

    def attach_to(self, server):
        delegate = server.get_app()

        def handler(environ, start_response):
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
        self.query = parse_query(environ)
        self.headers = parse_headers(environ)
        self.body = environ['wsgi.input']

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

    for key in environ:
        if key.startswith('HTTP_'):
            name = key[5:].lower().replace('_', '-')
            value = environ[key]

            headers[name] = value

    return headers

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

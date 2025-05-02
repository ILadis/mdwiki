
import logging
import urllib.parse
import mkdocs.plugins

from mdwiki.utils import get_posts, get_tags

class MdWikiPlugin(mkdocs.plugins.BasePlugin):
    def on_startup(self, command, dirty):
        self.logger = logging.getLogger('mkdocs.plugins.mdwiki')
        self.index = MdWikiDynamicTemplate('index.html')

    def on_serve(self, server, config, builder):
        self.index.attach_to(server)
        self.logger.info('Attached dynamic template "%s" to server', str(self.index.name))

    def on_env(self, env, config, files):
        posts = get_posts(files)
        tags = get_tags(files)

        self.logger.debug('Got page tags: %s', str(tags))
        self.logger.debug('Got page %d post(s)', len(posts))

        env.globals['posts'] = posts
        env.globals['tags'] = tags

        return env

    def on_pre_template(self, template, template_name, config):
        self.index.set_template(template_name, template)

    def on_template_context(self, context, template_name, config):
        self.index.set_context(template_name, context)

class MdWikiDynamicTemplate:
    def __init__(self, name):
        self.name = name

    def set_template(self, name, template):
        if self.name == name:
            self.template = template

    def set_context(self, name, context):
        if self.name == name:
            self.context = context

    def attach_to(self, server):
        delegate = server.get_app()

        def handler(environ, start_response):
            path = environ['PATH_INFO'][1:]
            query = urllib.parse.parse_qsl(environ['QUERY_STRING'])

            if self.name != path:
                return delegate(environ, start_response)

            start_response('200 OK', [('Content-Type', 'text/html')])

            context = dict()
            context.update(self.context)
            context['request'] = dict(query = dict(query))

            content = self.template.render(context)
            return [content.encode('utf-8')]

        server.set_app(handler)

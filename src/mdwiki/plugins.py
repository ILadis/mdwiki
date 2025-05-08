
import logging
import urllib.parse
import mkdocs.plugins

import mdwiki.http
import mdwiki.api

from mdwiki.utils import get_posts, get_tags

# For developer guide in plugins see:
# https://www.mkdocs.org/dev-guide/plugins/

class MdWikiPlugin(mkdocs.plugins.BasePlugin):
    def on_startup(self, command, dirty):
        self.logger = logging.getLogger('mkdocs.plugins.mdwiki')
        self.index = mdwiki.http.HttpTemplate('index.html')

        self.router = mdwiki.http.HttpRouter()
        self.router.add_handler(self.index)

        self.list_notes = mdwiki.api.ListNotes()
        self.update_notes = mdwiki.api.UpdateNotes()

        self.router.add_handler(mdwiki.api.Capabilities())
        self.router.add_handler(self.list_notes)
        self.router.add_handler(self.update_notes)

        self.logger.info('Attached nextcloud notes api to server')

    def on_serve(self, server, config, builder):
        self.router.attach_to(server)
        self.logger.info('Attached dynamic/http template "%s" to server', self.index.name)

    def on_files(self, files, config):
        self.list_notes.files = files
        self.update_notes.files = files
        self.logger.info('Updated files information for nextcloud notes api')

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

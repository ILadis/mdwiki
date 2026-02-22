
import sys, logging
import urllib.parse
import mkdocs.plugins
import mkdocs.config.config_options

import mdwiki.http
import mdwiki.api

from mdwiki.utils import setup_logging, enable_graceful_shutdown, disable_livereload_jsinject
from mdwiki.utils import get_posts, get_post, get_tags

# For developer guide in plugins see:
# https://www.mkdocs.org/dev-guide/plugins/

class MdWikiPlugin(mkdocs.plugins.BasePlugin):
    config_scheme = (
        ('log_level' , mkdocs.config.config_options.Type(str, default='info')),
        ('log_format', mkdocs.config.config_options.Type(str, default='%(levelname)8s-  %(message)s')),
    )

    def on_startup(self, command, dirty):
        self.logger = logging.getLogger('mkdocs.plugins.mdwiki')
        self.configured = False

    def on_config(self, config):
        setup_logging(sys.stdout, self.config['log_level'], self.config['log_format'])

        if self.configured:
            return

        # Only configure http handlers once ("on_config" event can be triggered multiple times)
        self.configured = True

        self.index = mdwiki.http.HttpTemplate(config, 'index.html')
        self.tags = mdwiki.http.HttpTemplate(config, 'tags.html')

        self.public_access = mdwiki.api.PublicAccess(config)
        self.list_notes = mdwiki.api.ListNotes(config)
        self.update_notes = mdwiki.api.UpdateNotes(config)
        self.create_notes = mdwiki.api.CreateNotes(config)
        self.tick_checkbox = mdwiki.api.TickCheckbox(config)

    def on_serve(self, server, config, builder):
        self.router = mdwiki.http.HttpRouter()
        self.router.attach_to(server)

        enable_graceful_shutdown(server)
        disable_livereload_jsinject(server)

        # Should always run first (must be first handler in chain)
        self.router.add_handler(self.public_access)

        self.router.add_handler(self.index)
        self.logger.info('Attached dynamic template "%s" to server', self.index.name)

        self.router.add_handler(self.tags)
        self.logger.info('Attached dynamic template "%s" to server', self.tags.name)

        self.router.add_handler(mdwiki.api.Capabilities(config))
        self.router.add_handler(self.list_notes)
        self.router.add_handler(self.update_notes)
        self.router.add_handler(self.create_notes)
        self.router.add_handler(self.tick_checkbox)
        self.logger.info('Attached nextcloud notes api to server')

    def on_files(self, files, config):
        self.public_access.files = files
        self.list_notes.files = files
        self.update_notes.files = files
        self.create_notes.files = files
        self.tick_checkbox.files = files
        self.logger.info('Updated files information for nextcloud notes api')

    def on_env(self, env, config, files):
        env.globals['posts'] = lambda tag, public: get_posts(files, tag, public)
        env.globals['tags'] = lambda public: get_tags(files, public)
        env.filters['to_post'] = lambda page: get_post(page.file)
        return env

    def on_pre_template(self, template, template_name, config):
        self.index.set_template(template_name, template)
        self.tags.set_template(template_name, template)

    def on_template_context(self, context, template_name, config):
        self.index.set_context(template_name, context)
        self.tags.set_context(template_name, context)

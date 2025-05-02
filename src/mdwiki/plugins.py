
import logging
import mkdocs.plugins

from mkdocs.utils import meta
from mkdocs.structure.pages import Page

class MdWikiPlugin(mkdocs.plugins.BasePlugin):
    def on_startup(self, command, dirty):
        self.logger = logging.getLogger('mkdocs.plugins.mdwiki')

    def get_features(self, files):
        features = list()

        for file in files.documentation_pages():
            source = file.content_string
            _, data = meta.get_data(source)

            feature = dict(
                title = data.get('title'),
                summary = data.get('summary'),
                date = data.get('date'),
                url = file.url)

            features.append(feature)
            self.logger.debug('Got featured page: "%s"', feature.get('title'))

        return features

    def get_tags(self, files):
        tags = set()

        for file in files.documentation_pages():
            source = file.content_string
            _, data = meta.get_data(source)

            for tag in data.get('tags', []):
                tags.add(tag)

        self.logger.debug('Got page tags: %s', str(tags))
        return tags

    def on_env(self, env, config, files):
        env.globals['features'] = self.get_features(files)
        env.globals['tags'] = self.get_tags(files)
        return env



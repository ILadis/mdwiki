
import re, subprocess

import markdown.extensions
import markdown.postprocessors
import markdown.blockprocessors

class TabLengthProcessor(markdown.blockprocessors.BlockProcessor):
    def __init__(self, parser):
        super().__init__(parser)
        self.tab_length = 2

class ListProcessor():
    def __init__(self, parser):
        super().__init__(parser)

    def test(self, parent, block):
        blocks = block.split('\n')
        for block in blocks:
            if self.RE.match(block):
                return True
        return False

    # Splits a block which contains a list into separate blocks that can later
    # be processed by the actual list processors.
    #
    # For example the block:
    #   "this is a headline\n- item 1\n- item 2"
    #
    # Is turned into two separate blocks:
    #   "this is a headline"
    #   "- item 1\n- item 2"
    def run(self, parent, blocks):
        index = 0
        block = blocks.pop(0)

        for b in block.split('\n'):
            if not self.RE.match(b):
                blocks.insert(index, b)
                block = block[len(b)+1:]
                index += 1
            else:
                blocks.insert(index, block)
                break

        if index == 0:
            super().run(parent, blocks)

class OListProcessor(ListProcessor, markdown.blockprocessors.OListProcessor, TabLengthProcessor):
    def __init__(self, parser):
        super().__init__(parser)

    def test(self, parent, block):
        return super().test(parent, block)

    def run(self, parent, blocks):
        return super().run(parent, blocks)

class UListProcessor(ListProcessor, markdown.blockprocessors.UListProcessor, TabLengthProcessor):
    def __init__(self, parser):
        super().__init__(parser)

    def test(self, parent, block):
        return super().test(parent, block)

    def run(self, parent, blocks):
        return super().run(parent, blocks)

class IndentProcessor(markdown.blockprocessors.ListIndentProcessor, TabLengthProcessor):
     def __init__(self, parser):
        super().__init__(parser)

class ChecklistPostprocessor(markdown.postprocessors.Postprocessor):
    RE = re.compile(r'^<li>\[([ Xx])\]', re.MULTILINE)

    def run(self, html):
        return re.sub(self.RE, self.convert, html)

    def convert(self, match):
        state = match.group(1)
        checked = ' checked' if state != ' ' else ''
        return '<li><input type="checkbox" disabled%s>' % checked

class FencesPreprocessor(markdown.preprocessors.Preprocessor):
    RE = re.compile(r'^```(?P<lang>[a-z]+)\s*\n(?P<content>.*?)```\s*$', re.MULTILINE | re.DOTALL)

    def __init__(self, md, lang, commands):
        super().__init__(md)
        self.lang = lang
        self.commands = commands

    def run(self, lines):
        index = 0
        text = '\n'.join(lines)
        while True:
            match = self.RE.search(text, index)
            if not match:
                break

            lang = match.group('lang')
            content = match.group('content')

            placeholder = ''
            if lang == self.lang:
                code = self.process(content) or ''
                placeholder = self.md.htmlStash.store(code)

            text = text[:match.start()] + '\n' + placeholder + '\n' + text[match.end():]
            index = match.start() + len(placeholder) + 2

        return text.split('\n')

    def process(self, content):
        try:
            process = subprocess.Popen(self.commands,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)
            process.stdin.write(content.encode('utf-8'))
            output, error = process.communicate()

            return output.decode('utf-8')
        except:
            return False

class MdWikiExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(OListProcessor(md.parser), 'olist', 41)
        md.parser.blockprocessors.register(UListProcessor(md.parser), 'ulist', 31)
        md.parser.blockprocessors.register(IndentProcessor(md.parser), 'indent', 91)
        md.preprocessors.register(FencesPreprocessor(md, 'graphviz', ['dot', '-Tsvg']), 'graphviz', 29)
        md.postprocessors.register(ChecklistPostprocessor(), 'checklist', 51)

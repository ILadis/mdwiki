
import re

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

class MdWikiExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(OListProcessor(md.parser), 'olist', 41)
        md.parser.blockprocessors.register(UListProcessor(md.parser), 'ulist', 31)
        md.parser.blockprocessors.register(IndentProcessor(md.parser), 'indent', 91)
        md.postprocessors.register(ChecklistPostprocessor(), 'checklist', 51)

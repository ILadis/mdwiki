
import markdown.extensions
import markdown.blockprocessors

class TabLengthProcessor(markdown.blockprocessors.BlockProcessor):
    def __init__(self, parser):
        super(TabLengthProcessor, self).__init__(parser)
        self.tab_length = 2

class OListProcessor(markdown.blockprocessors.OListProcessor, TabLengthProcessor):
     def __init__(self, parser):
        super(OListProcessor, self).__init__(parser)

class UListProcessor(markdown.blockprocessors.UListProcessor, TabLengthProcessor):
    def __init__(self, parser):
        super(UListProcessor, self).__init__(parser)

class IndentProcessor(markdown.blockprocessors.ListIndentProcessor, TabLengthProcessor):
     def __init__(self, parser):
        super(IndentProcessor, self).__init__(parser)

class MdWikiListExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(OListProcessor(md.parser), 'olist', 41)
        md.parser.blockprocessors.register(UListProcessor(md.parser), 'ulist', 31)
        md.parser.blockprocessors.register(IndentProcessor(md.parser), 'indent', 91)

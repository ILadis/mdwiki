
import sys

def run():
    from mkdocs.commands import serve
    sys.exit(serve.serve())

if __name__ == '__main__':
    run()

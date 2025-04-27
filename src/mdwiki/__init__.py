
import os, builtins
import pathlib, importlib

from mdwiki.ioutils import newfio

@newfio(os, 'walk', mode=False)
def walk(file, **kwargs):
    for f in file.iterdir():
        path = pathlib.Path(str(f.parent))
        parent = path.resolve()
        files = [str(f.name)]
        yield (parent, [], files)

@newfio(os, 'listdir', mode=False)
def listdir(file):
    for f in file.iterdir():
        yield f.name

@newfio(os.path, 'isfile')
def isfile(file):
    return file.is_file()

@newfio(os.path, 'getmtime')
def getmtime(file):
    with importlib.resources.as_file(file) as fspath:
        return fspath.stat().st_mtime

@newfio(builtins, 'open')
def open(file, mode='r', **kwargs):
    return file.open(mode)

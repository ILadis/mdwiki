#!/usr/bin/python3

import urllib.request
import zipapp, zipimport
import os, pathlib, hashlib

def main():
    clean(['./pip.pyz', './mkdocs.pyz', './vendor'])
    clean(['./src/build', './src/*.egg-info'])

    pip = get_pip()

    flags = ['--prefix', './vendor', '--disable-pip-version-check']
    pip(['install', 'mkdocs'] + flags)
    pip(['install', './src'] + flags)

    prefix = get_pip_prefix('./vendor')
    zipapp.create_archive(prefix, target='./mkdocs.pyz', main='mdwiki.main:run')

def get_pip(version='25.1.1', hash='3a4f097c346f67adde38ceb430f4872d1e12d729'):
    url = f"https://bootstrap.pypa.io/pip/zipapp/pip-{version}.pyz"
    target = pathlib.Path('./pip.pyz')

    if not target.exists():
        urllib.request.urlretrieve(url, target)

    with target.open(mode='rb') as file:
        h = hashlib.file_digest(file, 'sha1').hexdigest()
        if h != hash:
            raise ImportError(name='pip')

    importer = zipimport.zipimporter(os.fspath(target))
    module = importer.load_module('pip')

    return module.main

def get_pip_prefix(prefix):
    files = pathlib.Path(prefix).glob('./lib/python*/site-packages')
    file = next(files, False)

    if file is False:
        raise FileNotFoundError()
    return file

def clean(files):
    for file in files:
        paths = pathlib.Path('.').glob(file)
        for path in paths:
            remove(path)

def remove(path):
    for root, dirs, files in path.walk(top_down=False):
        for name in files:
            file = root.joinpath(name)
            file.unlink()
        for name in dirs:
            file = root.joinpath(name)
            file.rmdir()

if __name__ == '__main__':
    main()

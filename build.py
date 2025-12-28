#!/usr/bin/python3

import argparse
import unittest
import urllib.request
import zipapp, zipimport
import os, pathlib, hashlib

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'test'])
    parser.add_argument('-c', '--clean', action='store_true')

    args = parser.parse_args()
    actions = { 'test': test, 'build': build }

    actions[args.action](args)

def build(args):
    clean(['./mkdocs.pyz', './src/build', './src/*.egg-info'])
    clean(['./vendor']  if args.clean else [])

    pip = get_pip()

    flags = ['--prefix', './vendor', '--disable-pip-version-check']
    pkgs  = ['mkdocs', './src'] if args.clean else ['./src']

    pip(['install'] + pkgs + flags)

    prefix = get_pip_prefix('./vendor')
    zipapp.create_archive(prefix, target='./mkdocs.pyz', main='mdwiki.main:run')

def test(args):
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = lambda test, other: +1 if test > other else -1

    tests = loader.discover('./test', pattern='*_test.py')

    runner = unittest.runner.TextTestRunner()
    runner.run(tests)

def get_pip(version='25.1.1', hash='3a4f097c346f67adde38ceb430f4872d1e12d729'):
    url = f"https://bootstrap.pypa.io/pip/zipapp/pip-{version}.pyz"
    target = pathlib.Path('./pip.pyz')

    if not target.exists():
        urllib.request.urlretrieve(url, target)

    with target.open(mode='rb') as file:
        digest = hashlib.file_digest(file, 'sha1').hexdigest()
        if digest != hash:
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

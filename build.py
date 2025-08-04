import os, os.path
import urllib.request
import glob, zipapp, hashlib, zipimport

def main():
    clean(['./pip.pyz', './mkdocs.pyz', './vendor'])
    clean(['./src/build', './src/*.egg-info'])

    pip = get_pip()

    pip(['install', 'mkdocs', '--prefix', './vendor'])
    pip(['install', './src', '--prefix', './vendor'])

    zipapp.create_archive('./vendor/lib/python3.13/site-packages/', target='./mkdocs.pyz', main='mdwiki.main:run')

def get_pip(version='25.1.1', hash='3a4f097c346f67adde38ceb430f4872d1e12d729'):
    pipurl = f"https://bootstrap.pypa.io/pip/zipapp/pip-{version}.pyz"
    pipfile = './pip.pyz'

    if not os.path.isfile(pipfile):
        urllib.request.urlretrieve(pipurl, pipfile)

    with open(pipfile, 'rb') as file:
        piphash = hashlib.file_digest(file, 'sha1').hexdigest()
        if hash != piphash:
            raise ImportError()

    importer = zipimport.zipimporter(pipfile)
    module = importer.load_module('pip')

    return module.main

# FIXME: does not work for directories
def clean(files):
    for file in files:
        for name in glob.glob(file):
            print(f"Removing file: {name}")
            os.remove(name)

if __name__ == '__main__':
    main()

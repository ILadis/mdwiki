from setuptools import setup, find_packages

setup(
    name='mdwiki',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'mkdocs.themes': [
            'mdwiki = mdwiki.theme',
        ],
        'mkdocs.plugins': [
            'mdwiki = mdwiki.plugins:MdWikiPlugin',
        ]
    },
    zip_safe=False
)
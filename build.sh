#!/bin/bash

curl -OL https://bootstrap.pypa.io/pip/pip.pyz

VENDORDIR=$(realpath "./vendor/lib/python3".*"/site-packages/")
ZIPAPP=$(realpath "./mkdocs.pyz")

rm -rf "${ZIPAPP}" ./vendor
rm -rf ./src/build ./src/*.egg-info

python pip.pyz install mkdocs --prefix ./vendor
python pip.pyz install ./src --prefix ./vendor

python -m zipapp "${VENDORDIR}" -m "mdwiki.main:run" -o "${ZIPAPP}"

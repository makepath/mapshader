#!/bin/bash

set -e
set -x

BLD_DIR=`pwd`

SRC_DIR=$RECIPE_DIR/..

pushd $SRC_DIR

$PYTHON setup.py --quiet install --single-version-externally-managed --channel anaconda --channel conda-forge --channel pyviz --record=record.txt
cp -r $SRC_DIR/examples $PREFIX/share/mapshader-examples

popd

import json
from os import path

from io import BytesIO

import pytest

import xarray as xr

from datashader.transfer_functions import Image

from mapshader.sources import MapSource
from mapshader.core import render_map
from mapshader.core import render_geojson

from mapshader.sources import elevation_source

from mapshader.tests.data import DEFAULT_SOURCES_FUNCS

# TODO: add transform tests (test_transforms.py)

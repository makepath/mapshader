import json
from os import path

from io import BytesIO

import pytest

import xarray as xr

from datashader.transfer_functions import Image

from mapshader.sources import MapSource
from mapshader.core import render_map
from mapshader.core import render_geojson


from mapshader.tests.data import DEFAULT_SOURCES_FUNCS


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_to_geojson(source_func):
    source = source_func()
    geojson = render_geojson(source)
    assert isinstance(geojson, str)
    data = json.loads(geojson)
    assert isinstance(data, dict)

    if not source.geometry_type in ('raster', 'line'):
        assert data.get('type') == 'FeatureCollection'
    else:
        assert data


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_to_image(source_func):
    source = source_func()
    img = render_map(source, xmin=-20e6, ymin=-20e6,
                     xmax=20e6, ymax=20e6, width=500, height=500)
    assert isinstance(img, Image)


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_to_tile(source_func):
    source = source_func()
    img = render_map(source, x=0, y=0, z=0)
    assert isinstance(img, Image)

import json
from os import path

from io import BytesIO

import pytest

import numpy as np
import xarray as xr

from datashader.transfer_functions import Image

from mapshader.sources import MapSource
from mapshader.core import render_map
from mapshader.core import render_geojson
from mapshader.core import to_raster
from mapshader.core import create_agg
from mapshader.tests.data import DEFAULT_SOURCES_FUNCS
from mapshader.sources import elevation_source


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_to_geojson(source_func):
    source = MapSource.from_obj(source_func()).load()
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
    source = MapSource.from_obj(source_func()).load()
    img = render_map(source, xmin=-20e6, ymin=-20e6,
                     xmax=20e6, ymax=20e6, width=500, height=500)
    assert isinstance(img, Image)


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_to_tile(source_func):
    source = MapSource.from_obj(source_func()).load()
    img = render_map(source, x=0, y=0, z=0, height=256, width=256)
    assert isinstance(img, Image)


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_to_raster(source_func):
    source = MapSource.from_obj(source_func()).load()
    result = to_raster(source, xmin=-20e6, ymin=-20e6,
                     xmax=20e6, ymax=20e6, width=500, height=500)
    assert isinstance(result, xr.DataArray)
    assert result.data.shape == (500, 500)


def test_tile_render_edge_effects():
    source = MapSource.from_obj(elevation_source()).load()

    # this tile was bad...
    agg = create_agg(source, x=10, y=11, z=5)

    first_col = agg.data[:, 0]
    last_col = agg.data[:, -1]
    top_row = agg.data[0, :] # TODO: do i have these flipped?
    bottom_row = agg.data[-1, :]

    assert np.all(~np.isnan(first_col))
    assert np.all(~np.isnan(last_col))
    assert np.all(~np.isnan(top_row))
    assert np.all(~np.isnan(bottom_row))

    img = render_map(source, x=10, y=11, z=5)
    assert isinstance(img, Image)

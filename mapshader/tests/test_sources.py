import json
from os import path

from io import BytesIO

import xarray as xr

import pytest

from PIL import Image
import geopandas as gpd

from mapshader.sources import MapSource
from mapshader.sources import VectorSource

from mapshader.sources import world_countries_source
from mapshader.sources import world_cities_source
from mapshader.sources import nybb_source
from mapshader.sources import elevation_source

from mapshader.core import to_raster

HERE = path.abspath(path.dirname(__file__))
FIXTURES_DIR = path.join(HERE, 'fixtures')
DEFAULT_SOURCES_FUNCS = [world_countries_source,
                         world_cities_source,
                         nybb_source,
                         elevation_source]

@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_load_default_dataset(source_func):
    source = MapSource.from_obj(source_func()).load()
    assert isinstance(source, MapSource)

def test_create_map_source_with_existing_geodataframe():

    gdf = gpd.read_file(gpd.datasets.get_path('nybb'))

    # construct transforms
    reproject_transform = dict(name='reproject_vector', args=dict(epsg=3857))
    sp_transform = dict(name='to_spatialpandas', args=dict(geometry_field='geometry'))
    transforms = [reproject_transform, sp_transform]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'NYC Admin'
    source_obj['key'] = 'nyc-boroughs'
    source_obj['text'] = 'NYC Boroughs'
    source_obj['description'] = 'New York City Boroughs'
    source_obj['geometry_type'] = 'polygon'
    source_obj['agg_func'] = 'max'
    source_obj['shade_how'] = 'linear'
    source_obj['span'] = 'min/max'
    source_obj['dynspread'] = None
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'geometry'
    source_obj['yfield'] = 'geometry'
    source_obj['zfield'] = 'BoroCode'
    source_obj['data'] = gdf
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile', 'wms', 'image', 'geojson']

    source = MapSource.from_obj(source_obj).load()
    assert isinstance(source, VectorSource)

    arr = to_raster(source, width=100)
    assert isinstance(arr, xr.DataArray)

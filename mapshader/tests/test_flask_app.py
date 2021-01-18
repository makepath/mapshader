import json
import pytest

from mapshader.flask_app import app
from

DEFAULT_SOURCES_FUNCS = [world_countries_source,
                         world_cities_source,
                         nybb_source]

client = app.test_client()

@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_tile_requests(source_func):
    source = source_func()
    assert isinstance(source, MapSource)


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_map_requests(source_func):
    source = source_func()
    assert isinstance(source, MapSource)


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_geometry_requests(source_func):
    source = source_func()
    assert isinstance(source, MapSource)


def test_default_tile_queries():
    res = client.get('/')
    assert res

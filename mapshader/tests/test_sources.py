import json
from os import path

from io import BytesIO

import pytest

from PIL import Image

from mapshader.sources import MapSource

from mapshader.sources import world_countries_source
from mapshader.sources import world_cities_source
from mapshader.sources import nybb_source
from mapshader.sources import elevation_source

HERE = path.abspath(path.dirname(__file__))
FIXTURES_DIR = path.join(HERE, 'fixtures')
DEFAULT_SOURCES_FUNCS = [world_countries_source,
                         world_cities_source,
                         nybb_source,
                         elevation_source]

@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_load_default_dataset(source_func):
    source = source_func()
    assert isinstance(source, MapSource)

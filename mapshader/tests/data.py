from os import path

from mapshader.sources import world_countries_source
from mapshader.sources import world_boundaries_source
from mapshader.sources import world_cities_source
from mapshader.sources import nybb_source
from mapshader.sources import elevation_source

HERE = path.abspath(path.dirname(__file__))
FIXTURES_DIR = path.join(HERE, 'fixtures')

DEFAULT_SOURCES_FUNCS = [world_countries_source,
                         world_cities_source,
                         nybb_source,
                         world_boundaries_source,
                         elevation_source]

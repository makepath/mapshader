import json
import pytest

from mapshader.flask_app import create_app

from mapshader.sources import world_countries_source
from mapshader.sources import world_cities_source
from mapshader.sources import nybb_source


DEFAULT_SOURCES_FUNCS = [world_countries_source,
                         world_cities_source,
                         nybb_source]

CLIENT = create_app().test_client()


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_geojson_polygons(source_func):
    source = source_func()
    resp = CLIENT.get(source.geojson_url)
    data = json.loads(resp.data)
    assert isinstance(data, dict)
    assert data.get('type') == 'FeatureCollection'

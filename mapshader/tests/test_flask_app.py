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
def test_default_geojson(source_func):
    source = source_func()
    resp = CLIENT.get(source.geojson_url)
    data = json.loads(resp.data)
    assert isinstance(data, dict)
    assert data.get('type') == 'FeatureCollection'


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def est_default_tiles(source_func):
    source = source_func()
    url = source.tile_url
    X = 0
    Y = 0
    Z = 0
    url = (url.replace('<x>', str(X))
              .replace('<y>', str(Y))
              .replace('<z>', str(Z)))
    resp = CLIENT.get(url)
    data = json.loads(resp.data)
    assert isinstance(data, dict)
    assert data.get('type') == 'FeatureCollection'


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_images(source_func):
    source = source_func()
    url = source.image_url
    xmin = -180
    xmax = 180
    ymin = -90
    ymax = 90
    W = 300
    H = 150
    url = (url.replace('<xmin>', str(xmin))
              .replace('<ymin>', str(ymin))
              .replace('<xmax>', str(xmax))
              .replace('<ymax>', str(ymax))
              .replace('<width>', str(W))
              .replace('<height>', str(H)))
    resp = CLIENT.get(url)
    print(resp)
    assert resp

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
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, dict)
    assert data.get('type') == 'FeatureCollection'


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_tiles(source_func):
    source = source_func()
    url = source.tile_url
    X = 0
    Y = 0
    Z = 0
    url = (url.replace('<x>', str(X))
              .replace('<y>', str(Y))
              .replace('<z>', str(Z)))
    resp = CLIENT.get(url)
    assert resp.status_code == 200
    assert resp


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_images(source_func):
    source = source_func()
    url = source.image_url
    xmin = -20e6
    xmax = 20e6
    ymin = -20e6
    ymax = 20e6
    W = 500
    H = 500
    url = (url.replace('<xmin>', str(xmin))
              .replace('<ymin>', str(ymin))
              .replace('<xmax>', str(xmax))
              .replace('<ymax>', str(ymax))
              .replace('<width>', str(W))
              .replace('<height>', str(H)))
    resp = CLIENT.get(url)
    assert resp.status_code == 200
    assert resp


@pytest.mark.parametrize("source_func", DEFAULT_SOURCES_FUNCS)
def test_default_wms(source_func):
    source = source_func()
    url = source.wms_url
    xmin = -20e6
    xmax = 20e6
    ymin = -20e6
    ymax = 20e6
    W = 500
    H = 500
    url += f'?height={H}&width={W}&bbox={xmin},{ymin},{xmax},{ymax}'
    resp = CLIENT.get(url)
    assert resp.status_code == 200
    assert resp


def test_site_index():
    resp = CLIENT.get('/')
    assert resp.status_code == 200
    assert resp


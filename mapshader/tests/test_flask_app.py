import json
import pytest

from mapshader.flask_app import create_app

from mapshader.sources import world_countries_source
from mapshader.sources import world_cities_source
from mapshader.sources import nybb_source

from mapshader.sources import get_services


DEFAULT_SERVICES = get_services()

CLIENT = create_app().test_client()


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES if s.service_type == 'geojson'])
def test_default_geojson(service):

    resp = CLIENT.get(service.default_url)
    assert resp.status_code == 200

    data = json.loads(resp.data)
    assert isinstance(data, dict)


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES])
def test_legend(service):

    resp = CLIENT.get(service.legend_url)
    assert resp.status_code == 200

    data = json.loads(resp.data)
    assert isinstance(data, list)


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES if s.service_type == 'tile'])
def test_default_tiles(service):
    resp = CLIENT.get(service.default_url)
    assert resp.status_code == 200


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES if s.service_type == 'image'])
def test_default_images(service):
    resp = CLIENT.get(service.default_url)
    assert resp.status_code == 200


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES if s.service_type == 'wms'])
def test_default_wms(service):
    resp = CLIENT.get(service.default_url)
    assert resp.status_code == 200


def test_site_index():
    resp = CLIENT.get('/')
    assert resp.status_code == 200


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES if s.service_type == 'dag'])
def test_geoprocessing_service(service):
    resp = CLIENT.get(service.default_url)
    assert resp.status_code == 200


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES if s.service_type == 'dag'])
def test_geoprocessing_service_load_sources(service):
    first_two = service.sources[:2]
    sources_key = [source.key for source in first_two]

    data = {
        'graph': {
            'load_srcs': ('load_sources', sources_key),
        }
    }
    assert not first_two[0].is_loaded
    assert not first_two[1].is_loaded
    resp = CLIENT.get(service.default_url, data)
    assert resp.status_code == 200
    assert first_two[0].is_loaded
    assert first_two[1].is_loaded

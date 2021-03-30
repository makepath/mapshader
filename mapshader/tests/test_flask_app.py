import json
import pytest

import mapshader

from mock import patch

from mapshader.flask_app import create_app

from mapshader.sources import (
    MapSource,
    GeoprocessingService,
    elevation_source,
    get_services,
    world_boundaries_source,
)

DEFAULT_SERVICES = list(get_services())

CLIENT = create_app().test_client()


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES if s.service_type == 'geojson'])
def test_default_geojson(service):

    resp = CLIENT.get(service.default_url)
    assert resp.status_code == 200

    data = json.loads(resp.data)
    assert isinstance(data, dict)


@pytest.mark.parametrize("service", [s for s in DEFAULT_SERVICES if s.service_type != 'dag'])
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


def test_geoprocessing_service_load_sources():
    dag_service = GeoprocessingService(source=[])

    resp = CLIENT.post(
        dag_service.default_url,
        json={
            'output': ('output', 'My text message'),
        },
        query_string={'process': 'output'}
    )
    assert resp.status_code == 200
    assert resp.data == b'My text message'

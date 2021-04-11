import pytest
from mapshader.flask_app import build_previewer
from mapshader.sources import GeoJSONService, MapSource, TileService, world_countries_source
from bokeh.plotting.figure import Figure

def test_build_previewer_with_point_data_source():
    source_dict = world_countries_source()
    map_source = MapSource.from_obj(source_dict)
    tile_service = TileService(map_source)
    result = build_previewer(tile_service)
    assert isinstance(result, Figure)

def test_build_previewer_with_geojson_service_type():
    source_dict = world_countries_source()
    map_source = MapSource.from_obj(source_dict)
    geojson_service = GeoJSONService(map_source)
    result = build_previewer(geojson_service)

    assert isinstance(result, Figure)

def test_build_previewer_with_bad_data():
    source_dict = world_countries_source()
    map_source = MapSource.from_obj(source_dict)

    map_source.data = None
    map_service = TileService(map_source)

    with pytest.raises(ValueError) as e:
        # does not raise any error with bad_data
        result = build_previewer(map_service)

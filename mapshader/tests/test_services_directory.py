from mapshader.flask_app import build_previewer
from mapshader.sources import world_countries_source

def test_build_previewer_with_point_data_source():
    source_dict = world_countries_source()
    map_source = MapSource.from_obj(source_dict)
    map_service = MapService(map_source)
    result = build_previewer(map_service)
    assert isinstance(result, bokeh.Figure)

def test_build_previewer_with_bad_data():
    source_dict = world_countries_source()
    map_source = MapSource.from_obj(source_dict)
    map_source.data = None

    with pytest.assertError as _:
        result = build_previewer(map_service)

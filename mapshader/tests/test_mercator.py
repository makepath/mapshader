import pytest
from mapshader.mercator import MercatorTileDefinition
import math

# Test Data
default_ranges = ((-20037508.34, 20037508.34), (-20037508.34, 20037508.34))
test_object = MercatorTileDefinition(default_ranges[0], default_ranges[1])

# Test Parameters
tile_params = {
    'q1_tile': ((0, 0, 1), True),
    'q2_tile': ((-1, 1, 1), False),
    'q3_tile': ((-1, -1, 1), False),
    'q4_tile': ((1, -1, 1), False),
    'neg_z_val': ((1, 1, -1), False)
}

resolution_params = {
    'int': (10, 152.8740565703525),
    'float': (10.25, 128.551246155303)
}

resolution_extent_params = {
    'int': (((0, 0, 150, 220), 20, 30), [5, 11]),
    'float': (((0, 0, 150.5, 220.30), 20.5, 28.67), [5.2493896058597835, 10.746341463414634])
}

pixels_to_meters_params = {
    'int': ((100, 200, 2), (-16123932.491798975, -12210356.643597951)),
    'float': ((100.25, 200.3, 2.7), (-17622397.097840715, -15212104.032723146))
}

meters_to_pixels_params = {
    'int': ((-16123932.491798975, -12210356.643597951, 2), (100.00000000000003, 200)),
    'float': ((-17622397.097840715, -15212104.032723146, 2.7), (100.25000000000001, 200.3))
}

pixels_to_tile_params = {
    'int': ((100, 200, 2), (0, 3)),
    'float': ((100.25, 200.3, 2.7), (0, 5.498019170849885))
}

pixels_to_raster_params = {
    'int': ((100, 200, 2), (100, 824)),
    'float': ((100.25, 200.3, 2), (100.250, 823.7))
}

meters_to_tile_params = {
    'int': ((-16123932.491798975, -12210356.643597951, 2), (0, 3)),
    'float': ((-17622397.097840715, -15212104.032723146, 2.7), (0, 5.498019170849885))
}

# Tests
def test_MercatorTileDefinition():
    # Test Inputs
    assert isinstance(test_object.x_range, tuple)
    assert isinstance(test_object.y_range, tuple)
    assert isinstance(test_object.max_zoom, int)
    assert isinstance(test_object.min_zoom, int)
    assert isinstance(test_object.x_origin_offset, float)
    assert isinstance(test_object.y_origin_offset, float)
    assert isinstance(test_object.initial_resolution, float)
    # assert isinstance(test_obj.format, int)

def test_to_ogc_tile_metadata():
    pass

def test_to_esri_tile_metadata():
    pass

@pytest.mark.parametrize('args, expected', list(tile_params.values()), ids = list(tile_params.keys()))
def test_is_valid_tile(args, expected):
    # Test Inputs
    assert isinstance(args, tuple) and len(args) == 3
    for a in args:
        assert isinstance(a, int)

    assert isinstance(expected, bool)

    # Test Output
    assert test_object.is_valid_tile(args[0], args[1], args[2]) == expected


@pytest.mark.parametrize('arg, expected', list(resolution_params.values()), ids = list(resolution_params.keys()))
def test__get_resolution(arg, expected):
    # Test Inputs
    assert isinstance(arg, int) or isinstance(arg, float)

    assert isinstance(expected, int) or isinstance(expected, float)

    # Test Output
    assert test_object._get_resolution(arg) == expected

@pytest.mark.parametrize('args, expected', list(resolution_extent_params.values()), ids = list(resolution_extent_params.keys()))
def test_get_resolution_by_extent(args, expected):
    # Test Inputs
    assert isinstance(args, tuple) and len(args) == 3
    for a in args[1:2]:
        assert isinstance(a, int) or isinstance(a, float)
    assert isinstance(args[0], tuple) and len(args[0]) == 4
    for a in args[0]:
        assert isinstance(a, int) or isinstance(a, float)

    assert isinstance(expected, list) and len(expected) == 2
    for e in expected:
        assert isinstance(e, int) or isinstance(e, float)

    # Test Output
    assert test_object.get_resolution_by_extent(args[0], args[1], args[2]) == expected

def test_get_level_by_extent():
    pass

@pytest.mark.parametrize('args, expected', list(pixels_to_meters_params.values()), ids = list(pixels_to_meters_params.keys()))
def test_pixels_to_meters(args, expected):
    # Test Inputs
    assert isinstance(args, tuple) and len(args) == 3
    for a in args:
        assert isinstance(a, int) or isinstance(a, float)

    assert isinstance(expected, tuple) and len(expected) == 2
    for e in expected:
        assert isinstance(e, int) or isinstance(e, float)

    # Test Output
    assert test_object.pixels_to_meters(args[0], args[1], args[2]) == expected

@pytest.mark.parametrize('args, expected', list(meters_to_pixels_params.values()), ids = list(meters_to_pixels_params.keys()))
def test_meters_to_pixels(args, expected):
    # Test Inputs
    assert isinstance(args, tuple) and len(args) == 3
    for a in args:
        assert isinstance(a, int) or isinstance(a, float)

    assert isinstance(expected, tuple) and len(expected) == 2
    for e in expected:
        assert isinstance(e, int) or isinstance(e, float)

    # Test Output
    assert test_object.meters_to_pixels(args[0], args[1], args[2]) == expected

@pytest.mark.parametrize('args, expected', list(pixels_to_tile_params.values()), ids = list(pixels_to_tile_params.keys()))
def test_pixels_to_tile(args, expected):
    # Test Inputs
    assert isinstance(args, tuple) and len(args) == 3
    for a in args:
        assert isinstance(a, int) or isinstance(a, float)

    assert isinstance(expected, tuple) and len(expected) == 2
    for e in expected:
        assert isinstance(e, int) or isinstance(e, float)

    # Test Output
    assert test_object.pixels_to_tile(args[0], args[1], args[2]) == expected

@pytest.mark.parametrize('args, expected', list(pixels_to_raster_params.values()), ids = list(pixels_to_raster_params.keys()))
def test_pixels_to_raster(args, expected):
    # Test Inputs
    assert isinstance(args, tuple) and len(args) == 3
    for a in args[0:1]:
        assert isinstance(a, int) or isinstance(a, float)
    assert isinstance(args[2], int) 

    assert isinstance(expected, tuple) and len(expected) == 2
    for e in expected:
        assert isinstance(e, int) or isinstance(e, float)

    # Test Output
    assert test_object.pixels_to_raster(args[0], args[1], args[2]) == expected

@pytest.mark.parametrize('args, expected', list(meters_to_tile_params.values()), ids = list(meters_to_tile_params.keys()))
def test_meters_to_tile(args, expected):
    # Test Inputs
    assert isinstance(args, tuple) and len(args) == 3
    for a in args:
        assert isinstance(a, int) or isinstance(a, float)

    assert isinstance(expected, tuple) and len(expected) == 2
    for e in expected:
        assert isinstance(e, int) or isinstance(e, float)

    # Test Output
    assert test_object.meters_to_tile(args[0], args[1], args[2]) == expected

def test_get_tiles_by_extent():
    pass
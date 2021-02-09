import pytest
from mapshader.mercator import MercatorTileDefinition
from mapshader.tests.data import DEFAULT_SOURCES_FUNCS
from mapshader.core import create_agg
import math

ranges = ((-20037508.34, 20037508.34), (-20037508.34, 20037508.34))
test_obj = MercatorTileDefinition(ranges[0], ranges[1])


def test_MercatorTileDefinition():
    # Test Inputs
    assert isinstance(test_obj.x_range, tuple)
    assert isinstance(test_obj.y_range, tuple)
    assert isinstance(test_obj.max_zoom, int)
    assert isinstance(test_obj.min_zoom, int)
    assert isinstance(test_obj.x_origin_offset, float)
    assert isinstance(test_obj.y_origin_offset, float)
    assert isinstance(test_obj.initial_resolution, float)
    # assert isinstance(test_obj.format, int)
    

def test_to_ogc_tile_metadata():
    pass

def test_to_esri_tile_metadata():
    pass

tile_params = {
    'q1_tile': ((0, 0, 1), (True, 2)),
    'q2_tile': ((-1, 1, 1), (False, 2)),
    'q3_tile': ((-1, -1, 1), (False, 2)),
    'q4_tile': ((1, -1, 1), (False, 2)),
    'neg_z_val': ((1, 1, -1), (False, 0.5))
}

@pytest.mark.parametrize('args, expected', list(tile_params.values()), ids = list(tile_params.keys()))
def test_is_valid_tile(args, expected):
    # Test Inputs
    for arg in args:
        assert isinstance(arg, int)
    assert isinstance(expected[0], bool)

    if expected[0] == True:
        assert (args[0] > 0 or args[0] <= expected[1]) or (args[1] > 0 or args[1] <= expected[1])
    else:
        assert (args[0] < 0 or args[0] >= expected[1]) or (args[1] < 0 or args[1] >= expected[1])

    #Test Outputs
    test_tile = test_obj.is_valid_tile(args[0], args[1], args[2])
    assert test_tile == expected[0]

@pytest.mark.parametrize("z, expected", [(10, 1024)])
def test__get_resolution(z, expected):
    new_res = test_obj._get_resolution(z)

    # Test Inputs
    assert isinstance(z, int)
    assert expected == 2 ** z 

    # Test Outputs
    assert new_res == test_obj.initial_resolution / expected

res_extent_params = {
    'small': (((0, 0, 150, 220), 20, 30), (50, 11)),
    'medium': (((0, 0, 1800, 1200), 20, 30), (60, 60)),
    'large': (((0, 0, 3900, 2600), 20, 30), (130, 130))
}
@pytest.mark.parametrize('args, expected', list(res_extent_params.values()), ids = list(res_extent_params.keys()))
def test_resolution_by_extent(args, expected):
    new_res = test_obj.get_resolution_by_extent(args[0], args[1], args[2])

    # Test Inputs
    assert isinstance(args[0], tuple)
    for arg in args[0]:
        assert isinstance(arg, int)
    assert isinstance(args[1], int)
    assert isinstance(args[2], int)

    for exp in expected:
        assert isinstance(exp, int)

    # Test Outputs
    assert isinstance(new_res, list)
    for res in new_res:
        assert isinstance(res, float)


#@pytest.mark.parametrize("extent, height, width", [((0,1024,0, 1024), 20, 30)])
#def test_get_level_by_extent(extent, height, width):
#    new_level = test_obj.get_level_by_extent(extent, height, width)

    # Test Inputs 
#    assert isinstance(extent, tuple)
#   assert isinstance(height, int)
#    assert isinstance(width, int)

@pytest.mark.parametrize("px, py, level", [(354, 345, 5)])
def test_pixels_to_meters(px, py, level):
    meters = test_obj.pixels_to_meters(px, py, level)
    res = test_obj._get_resolution(level)

    # Test Inputs
    assert isinstance(px, int)
    assert isinstance(py, int)
    assert isinstance(level, int)
    assert isinstance(res, float)

    # Test Outputs
    assert meters[0] == (px * res) - test_obj.x_origin_offset
    assert meters[1] == (py * res) - test_obj.y_origin_offset
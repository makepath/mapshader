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

@pytest.mark.parametrize("x, y, z, expected", [(0 ,0 ,0 ,True), (-1, -1, -1, False)])
def test_is_valid_tile(x, y, z, expected):
    # Test Inputs
    assert isinstance(x, int)
    assert isinstance(y, int)
    assert isinstance(z, int)
    assert isinstance(expected, bool)

    if expected == True:
        assert x > 0 or x <= math.pow(2, z)
        assert y > 0 or y <= math.pow(2, z)
    else:
        assert x < 0 or x >= math.pow(2, z)
        assert y < 0 or y >= math.pow(2, z)

    # Test Outputs
    test_tile = test_obj.is_valid_tile(x, y, z)
    assert test_tile == expected

@pytest.mark.parametrize("z, expected", [(10, 1024)])
def test__get_resolution(z, expected):
    new_res = test_obj._get_resolution(z)

    # Test Inputs
    assert isinstance(z, int)
    assert expected == 2 ** z 

    # Test Outputs
    assert new_res == test_obj.initial_resolution / expected

@pytest.mark.parametrize("extent, height, width, x_rs, y_rs", [((100, 500,200, 850), 20, 30)])
def test_get_resolution_by_extent(extent, height, width):
    new_res = test_obj.get_resolution_by_extent(extent, height, width)
    
    # Test Inputs
    assert isinstance(extent, tuple)
    assert isinstance(height, int)
    assert isinstance(width, int)


    # Test Output
    assert isinstance(new_res, list)
    assert new_res[0] == ((extent[2] - extent[0]) / width)
    assert new_res[1] == ((extent[3] - extent[1]) / height)

@pytest.mark.parametrize("extent, height, width", [((0,1024,0, 1024), 20, 30)])
    new_level = test.obj.get_level_by_extent(extent, height, width)

    # Test Inputs 
    assert isinstance(extent, tuple)
    assert isinstance(height, int)
    assert isinstance(width, int)
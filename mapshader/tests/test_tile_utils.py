from mapshader.tile_utils import (
    get_tile,
    render_tiles_by_extent,
    get_tiles_by_extent
)


TEMPLATE = ('https://c.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png')


def test_get_tile():
    lng = -90.283741
    lat = 29.890626
    level = 7
    tile = get_tile(lng, lat, level, template=TEMPLATE)
    assert isinstance(tile, str)


def test_render_tiles_by_extent():
    xmin = -90.283741
    ymin = 29.890626
    xmax = -89.912952
    ymax = 30.057766
    level = 11
    tiles = render_tiles_by_extent(xmin, ymin, xmax,
                                   ymax, level, template=TEMPLATE)
    tile_list = list(tiles)
    assert len(tile_list) == 6


def test_get_tiles_by_extent():
    xmin = -90.283741
    ymin = 29.890626
    xmax = -89.912952
    ymax = 30.057766
    level = 11
    tiles = get_tiles_by_extent(xmin, ymin, xmax, ymax, level)
    tile_list = list(tiles)
    assert len(tile_list) == 6

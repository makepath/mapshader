import pytest

import geopandas as gpd
import spatialpandas
from shapely.geometry import Polygon

from mapshader.sources import MapSource
from mapshader.sources import VectorSource
from mapshader.tile_utils import (
    get_tile,
    render_tiles_by_extent,
    get_tiles_by_extent,
    list_tiles
)

MIN_ZOOM = 0
MAX_ZOOM = 5
ALL_ZOOM_LEVELS = range(MIN_ZOOM, MAX_ZOOM)

TEMPLATE = ('https://c.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png')


@pytest.fixture
def full_map_polygon_vector_source(min_zoom, max_zoom):

    if min_zoom > max_zoom:
        polygon_source = None
    else:
        # create a polygon that fully covers the whole map
        lat_point_list = [85.05112878, -85.05112878, -85.05112878, 85.05112878, 85.05112878]
        lon_point_list = [-180, -180, 180, 180, -180]
        polygon_geom = Polygon(zip(lon_point_list, lat_point_list))
        crs = {'init': 'epsg:4326'}
        polygon_gdf = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[polygon_geom])

        # construct transforms
        buffered_extent_transform = dict(name='add_projected_buffered_extent',
                                         args=dict(crs='4326',
                                                   buffer_distance=.01,
                                                   geometry_field='geometry'))
        transforms = [buffered_extent_transform]
        # construct value obj
        source_obj = dict()
        source_obj['geometry_type'] = 'polygon'
        source_obj['data'] = polygon_gdf
        source_obj['transforms'] = transforms
        source_obj['tiling'] = dict(
            min_zoom=min_zoom,
            max_zoom=max_zoom,
            xmin_field='buffer_0_4326_xmin',
            xmax_field='buffer_0_4326_xmax',
            ymin_field='buffer_0_4326_ymin',
            ymax_field='buffer_0_4326_ymax',
        )

        # VectorSource from source object we created above
        polygon_source = VectorSource.from_obj(source_obj)
        polygon_source.load()

    return polygon_source, min_zoom, max_zoom


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


@pytest.mark.parametrize("min_zoom", ALL_ZOOM_LEVELS)
@pytest.mark.parametrize("max_zoom", ALL_ZOOM_LEVELS)
def test_list_tiles(full_map_polygon_vector_source):
    polygon_source, minz, maxz = full_map_polygon_vector_source
    if polygon_source is not None:
        tiles_ddf = list_tiles(polygon_source)
        # the polygon fully covers the whole map,
        # thus at each zoom level, all possible tiles will be generated
        num_all_possible_tiles = sum([2**(2*i) for i in range(minz, maxz + 1)])
        assert len(tiles_ddf) == num_all_possible_tiles

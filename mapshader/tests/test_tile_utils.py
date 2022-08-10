import pytest

import geopandas as gpd
import spatialpandas
from shapely.geometry import Polygon, Point

from mapshader.sources import VectorSource
from mapshader.tile_utils import (
    get_tile,
    render_tiles_by_extent,
    get_tiles_by_extent,
    list_tiles
)

ZOOM_LEVELS_1_5 = range(1, 5)
ZOOM_LEVELS_1_24 = range(1, 24)

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


@pytest.fixture
def point_vector_source(min_zoom, max_zoom):
    if min_zoom > max_zoom:
        point_source = None
    else:
        # create a point at (0, 0)
        point = Point(0, 0)
        crs = {'init': 'epsg:4326'}
        point_gdf = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[point])
        point_gdf['x'] = [point.x]
        point_gdf['y'] = [point.y]

        # construct value obj
        source_obj = dict()
        source_obj['geometry_type'] = 'point'
        source_obj['data'] = point_gdf
        source_obj['tiling'] = dict(
            min_zoom=min_zoom,
            max_zoom=max_zoom,
            xmin_field='x',
            xmax_field='x',
            ymin_field='y',
            ymax_field='y',
        )

        # VectorSource from source object we created above
        point_source = VectorSource.from_obj(source_obj)

    return point_source, min_zoom, max_zoom


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


@pytest.mark.parametrize("min_zoom", ZOOM_LEVELS_1_5)
@pytest.mark.parametrize("max_zoom", [5])
def test_list_tiles_polygon(full_map_polygon_vector_source):
    polygon_source, minz, maxz = full_map_polygon_vector_source
    if polygon_source is not None:
        tiles_ddf = list_tiles(polygon_source)
        # the polygon fully covers the whole map,
        # thus at each zoom level, all possible tiles will be generated
        num_all_possible_tiles = sum([2**(2*i) for i in range(minz, maxz + 1)])
        assert len(tiles_ddf) == num_all_possible_tiles


@pytest.mark.parametrize("min_zoom", ZOOM_LEVELS_1_24)
@pytest.mark.parametrize("max_zoom", [24])
def test_list_tiles_point(point_vector_source):

    point_source, minz, maxz = point_vector_source

    if point_source is not None:
        tiles_ddf = list_tiles(point_source).compute()
        # there is only a single point at (0, 0) in the vector point source,
        # thus at each zoom level, only one tile will be generated
        assert len(tiles_ddf) == maxz - minz + 1

        # at each zoom level, the generated tile is at the center of the map
        for i, row in tiles_ddf.iterrows():
            x = row['x']
            y = row['y']
            z = row['z']
            assert x == y == 2**(z-1)

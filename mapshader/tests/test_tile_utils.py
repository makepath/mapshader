import pytest

import numpy as np

import datashader as ds
import geopandas as gpd
from pyproj import CRS
import spatialpandas as spd
from shapely.geometry import Polygon, Point, LineString

from mapshader.sources import VectorSource, RasterSource

from mapshader.tile_utils import (
    get_tile,
    render_tiles_by_extent,
    get_tiles_by_extent,
    list_tiles,
)

ZOOM_LEVELS_1_8 = range(1, 8)
ZOOM_LEVELS_1_24 = range(1, 24)

TEMPLATE = "https://c.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png"


@pytest.fixture
def polygon_gdf():
    # create a polygon that fully covers the whole map
    lat_point_list = [
        85.05112878,
        -85.05112878,
        -85.05112878,
        85.05112878,
        85.05112878,
    ]
    lon_point_list = [-180, -180, 180, 180, -180]
    geom = Polygon(zip(lon_point_list, lat_point_list))
    gdf = gpd.GeoDataFrame(
        index=[0], crs={"init": "epsg:4326"}, geometry=[geom]
    )
    gdf["xmin"] = -180
    gdf["xmax"] = 180
    gdf["ymin"] = -85.05112878
    gdf["ymax"] = 85.05112878
    return gdf


@pytest.fixture
def polygon_vector_source(min_zoom, max_zoom, polygon_gdf):
    source_obj = dict()
    source_obj["geometry_type"] = "polygon"
    source_obj["data"] = polygon_gdf
    source_obj["tiling"] = dict(
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        xmin_field="xmin",
        xmax_field="xmax",
        ymin_field="ymin",
        ymax_field="ymax",
    )
    polygon_source = VectorSource.from_obj(source_obj)
    return polygon_source, min_zoom, max_zoom


@pytest.fixture
def polygon_raster(polygon_gdf):
    xrange = (-180, 180)
    yrange = (-90, 90)
    width = 360
    height = 180
    cvs = ds.Canvas(
        plot_width=width, plot_height=height, x_range=xrange, y_range=yrange
    )
    raster = cvs.polygons(spd.GeoDataFrame(polygon_gdf), geometry="geometry")
    return raster


@pytest.fixture
def polygon_raster_source(min_zoom, max_zoom, polygon_raster):
    source_obj = dict()
    source_obj["geometry_type"] = "raster"
    source_obj["data"] = polygon_raster
    source_obj["tiling"] = dict(min_zoom=min_zoom, max_zoom=max_zoom,)
    polygon_source = RasterSource.from_obj(source_obj)
    polygon_source.load()
    return polygon_source, min_zoom, max_zoom


@pytest.fixture
def point_gdf():
    # create a point at (0, 0)
    geom = Point(0, 0)
    crs = {"init": "epsg:4326"}
    gdf = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[geom])
    gdf["x"] = [geom.x]
    gdf["y"] = [geom.y]
    return gdf


@pytest.fixture
def point_vector_source(min_zoom, max_zoom, point_gdf):
    source_obj = dict()
    source_obj["geometry_type"] = "point"
    source_obj["data"] = point_gdf
    source_obj["tiling"] = dict(
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        xmin_field="x",
        xmax_field="x",
        ymin_field="y",
        ymax_field="y",
    )
    point_source = VectorSource.from_obj(source_obj)
    return point_source, min_zoom, max_zoom


@pytest.fixture
def point_raster(point_gdf):
    xrange = (1e-5, 0)
    yrange = (-1e-5, 0)
    width = 1
    height = 1
    cvs = ds.Canvas(
        plot_width=width, plot_height=height, x_range=xrange, y_range=yrange
    )
    raster = cvs.points(
        spd.GeoDataFrame(point_gdf), geometry="geometry"
    ).astype(np.float32)
    return raster


@pytest.fixture
def point_raster_source(min_zoom, max_zoom, point_raster):
    source_obj = dict()
    source_obj["geometry_type"] = "raster"
    source_obj["data"] = point_raster
    source_obj["tiling"] = dict(min_zoom=min_zoom, max_zoom=max_zoom,)
    # RasterSource from source object we created above
    point_source = RasterSource.from_obj(source_obj)
    return point_source, min_zoom, max_zoom


@pytest.fixture
def line_gdf():
    # create a horizontal line y=0 crossing 2 points (-180, 0), and (180, 0)
    p1 = Point(-180, 0)
    p2 = Point(180, 0)
    geom = LineString([p1, p2])
    gdf = gpd.GeoDataFrame(
        index=[0], crs={"init": "epsg:4326"}, geometry=[geom]
    )
    gdf["xmin"] = [p1.x]
    gdf["ymin"] = [p1.y]
    gdf["xmax"] = [p2.x]
    gdf["ymax"] = [p2.y]
    return gdf


@pytest.fixture
def line_vector_source(min_zoom, max_zoom, line_gdf):
    source_obj = dict()
    source_obj["geometry_type"] = "line"
    source_obj["data"] = line_gdf
    source_obj["tiling"] = dict(
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        xmin_field="xmin",
        xmax_field="xmax",
        ymin_field="ymin",
        ymax_field="ymax",
    )
    line_source = VectorSource.from_obj(source_obj)
    return line_source, min_zoom, max_zoom


@pytest.fixture
def line_raster(line_gdf):
    # create a line raster
    xrange = (-180, 180)
    yrange = (-1, 0)
    width = 360
    height = 1
    cvs = ds.Canvas(
        plot_width=width, plot_height=height, x_range=xrange, y_range=yrange
    )
    raster = cvs.line(spd.GeoDataFrame(line_gdf), geometry="geometry").astype(
        np.float32
    )
    return raster


@pytest.fixture
def line_raster_source(min_zoom, max_zoom, line_raster):
    # construct value obj
    source_obj = dict()
    source_obj["geometry_type"] = "raster"
    source_obj["data"] = line_raster
    source_obj["tiling"] = dict(min_zoom=min_zoom, max_zoom=max_zoom,)
    # RasterSource from source object we created above
    line_source = RasterSource.from_obj(source_obj)
    return line_source, min_zoom, max_zoom


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
    crs = None
    tiles = render_tiles_by_extent(
        xmin, ymin, xmax, ymax, crs, level, template=TEMPLATE
    )
    tile_list = list(tiles)
    assert len(tile_list) == 6


def test_get_tiles_by_extent():
    xmin = -90.283741
    ymin = 29.890626
    xmax = -89.912952
    ymax = 30.057766
    level = 11
    crs = None
    tiles = get_tiles_by_extent(xmin, ymin, xmax, ymax, crs, level)
    tile_list = list(tiles)
    assert len(tile_list) == 6


def test_get_tiles_by_extent_epsg_3857_succeeds():
    xmin = -9247040.214051334
    ymin = 2957552.7202336164
    xmax = -8982339.452713674
    ymax = 3470148.9253275474
    level = 9
    crs = CRS.from_epsg(3857)
    tiles = get_tiles_by_extent(xmin, ymin, xmax, ymax, crs, level)
    tile_list = list(tiles)
    assert len(tile_list) == 40


def test_get_tiles_by_extent_unsupported_crs_fails():
    with pytest.raises(ValueError):
        xmin = -9247040.214051334
        ymin = 2957552.7202336164
        xmax = -8982339.452713674
        ymax = 3470148.9253275474
        level = 9
        crs = CRS.from_epsg(900913)
        tiles = get_tiles_by_extent(xmin, ymin, xmax, ymax, crs, level)
        tile_list = list(tiles)
        assert len(tile_list) == 40


def test_get_tiles_by_extent_wrong_crs_fails():
    xmin = -9247040.214051334
    ymin = 2957552.7202336164
    xmax = -8982339.452713674
    ymax = 3470148.9253275474
    level = 9
    crs = CRS.from_epsg(4326)
    tiles = get_tiles_by_extent(xmin, ymin, xmax, ymax, crs, level)
    tile_list = list(tiles)
    assert len(tile_list) != 40


def _test_list_tiles_polygon(polygon_source, minz, maxz):
    if polygon_source is not None:
        tiles_ddf = list_tiles(polygon_source)
        # the polygon fully covers the whole map,
        # thus at each zoom level, all possible tiles will be generated
        num_all_possible_tiles = sum(
            [2 ** (2 * i) for i in range(minz, maxz + 1)]
        )
        assert len(tiles_ddf) == num_all_possible_tiles


@pytest.mark.parametrize("min_zoom", ZOOM_LEVELS_1_8)
@pytest.mark.parametrize("max_zoom", [8])
def test_list_tiles_polygon_vector(polygon_vector_source):
    polygon_source, minz, maxz = polygon_vector_source
    _test_list_tiles_polygon(polygon_source, minz, maxz)


@pytest.mark.parametrize("min_zoom", ZOOM_LEVELS_1_8)
@pytest.mark.parametrize("max_zoom", [8])
def test_list_tiles_polygon_raster(polygon_raster_source):
    polygon_source, minz, maxz = polygon_raster_source
    _test_list_tiles_polygon(polygon_source, minz, maxz)


def _test_list_tiles_point_geometry(point_source, minz, maxz):
    if point_source is not None:

        tiles_ddf = list_tiles(point_source).compute()
        # there is only a single point at (0, 0) in the vector point source,
        # thus at each zoom level, only one tile will be generated
        assert len(tiles_ddf) == maxz - minz + 1

        # at each zoom level, the generated tile is at the center of the map
        for i, row in tiles_ddf.iterrows():
            x = row["x"]
            y = row["y"]
            z = row["z"]
            assert x == y == 2 ** (z - 1)


@pytest.mark.parametrize("min_zoom", ZOOM_LEVELS_1_24)
@pytest.mark.parametrize("max_zoom", [24])
def test_list_tiles_point_vector(point_vector_source):
    point_source, minz, maxz = point_vector_source
    _test_list_tiles_point_geometry(point_source, minz, maxz)


@pytest.mark.parametrize("min_zoom", ZOOM_LEVELS_1_24)
@pytest.mark.parametrize("max_zoom", [24])
def test_list_tiles_point_raster(point_raster_source):
    point_source, minz, maxz = point_raster_source
    _test_list_tiles_point_geometry(point_source, minz, maxz)


def _test_list_tiles_line_geometry(line_source, minz, maxz):
    if line_source is not None:
        tiles_ddf = list_tiles(line_source)
        assert len(tiles_ddf) == sum([2 ** z for z in range(minz, maxz + 1)])
        tiles_ddf = tiles_ddf.compute()
        tiles_ddf_by_zoom = tiles_ddf.groupby("z")
        for z, tiles_z in tiles_ddf_by_zoom:
            # at each zoom level, the generated tiles intersect with line y=0
            assert len(tiles_z) == 2 ** z
            assert np.all(np.unique(tiles_z["y"]) == [2 ** (z - 1)])
            assert np.all(np.sort(np.unique(tiles_z["x"])) == range(2 ** z))


@pytest.mark.parametrize("min_zoom", ZOOM_LEVELS_1_8)
@pytest.mark.parametrize("max_zoom", [8])
def test_list_tiles_line_vector(line_vector_source):
    line_source, minz, maxz = line_vector_source
    _test_list_tiles_line_geometry(line_source, minz, maxz)


@pytest.mark.parametrize("min_zoom", ZOOM_LEVELS_1_8)
@pytest.mark.parametrize("max_zoom", [8])
def test_list_tiles_line_raster(line_raster_source):
    line_source, minz, maxz = line_raster_source
    _test_list_tiles_line_geometry(line_source, minz, maxz)

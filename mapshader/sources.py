from os import path

import geopandas as gpd
import pandas as pd
import spatialpandas

from mapshader.colors import colors
from mapshader.io import load_raster
from mapshader.transforms import reproject_raster
from mapshader.transforms import reproject_vector


class MapSource():

    def __init__(self, name=None, df=None, data=None,
                 geometry_type=None, key=None,
                 text=None, fields=None, span=None, route=None,
                 xfield='geometry', yfield='geometry', zfield=None,
                 agg_func=None, raster_interpolate='linear',
                 shade_how='linear', cmap=colors['viridis'],
                 dynspread=None, extras=None):

        if fields is None and isinstance(df, (pd.DataFrame, gpd.GeoDataFrame)):
            fields = [dict(key=c, text=c, value=c) for c in df.columns if c != 'geometry']

        if extras is None:
            extras = []

        if span == 'min/max' and zfield is None and geometry_type != 'raster':
            raise ValueError('You must include a zfield for min/max scan calculation')

        self.name = name
        self.df = df
        self.data = data
        self.geometry_type = geometry_type
        self.key = key
        self.text = text
        self.fields = fields
        self.span = span
        self.route = route
        self.xfield = xfield
        self.yfield = yfield
        self.zfield = zfield
        self.agg_func = agg_func
        self.raster_agg_func = raster_interpolate
        self.shade_how = shade_how
        self.cmap = cmap
        self.dynspread = dynspread
        self.extras = extras

    @property
    def tile_url(self):
        url = (f'/{self.key}'
               '/tile'
               '/<z>/<x>/<y>')
        return url

    @property
    def image_url(self):
        url = (f'/{self.key}'
               '/image'
               '/<xmin>/<ymin>/<xmax>/<ymax>'
               '/<width>/<height>')
        return url

    @property
    def wms_url(self):
        url = (f'/{self.key}'
               '/wms')
        return url

    @property
    def geojson_url(self):
        url = (f'/{self.key}'
               '/geojson')
        return url

    @property
    def tile_defaults(self):
        return dict(x=0, y=0, z=0)

    @property
    def image_defaults(self):
        return dict(xmin=-20e6, ymin=-20e6, xmax=20e6, ymax=20e6, height=500, width=500)

    @property
    def geojson_defaults(self):
        return dict()


def world_countries_source():
    data = gpd.datasets.get_path('naturalearth_lowres')
    world = gpd.read_file(data)
    world = world[(world.name != "Antarctica") & (world.name != "Fr. S. Antarctic Lands")]
    world = reproject_vector(world)
    spgdf = spatialpandas.GeoDataFrame(world, geometry='geometry')
    return MapSource(name='World Countries',
                     geometry_type='polygon',
                     df=spgdf,
                     span='min/max',
                     xfield='geometry',
                     yfield='geometry',
                     zfield='pop_est',
                     agg_func='sum',
                     dynspread=None,
                     shade_how='linear',
                     key='world-countries',
                     text='World Countries')


def world_boundaries_source():

    from mapshader.transforms import line_geoseries_to_datashader_line

    data = gpd.datasets.get_path('naturalearth_lowres')
    world = gpd.read_file(data)
    world = world[(world.name != "Antarctica") & (world.name != "Fr. S. Antarctic Lands")]
    world = reproject_vector(world)

    # convert polys to datashader compatible lines
    world['geometry'] = world['geometry'].exterior

    line_df = line_geoseries_to_datashader_line(world['geometry'])

    if not len(world) == len(line_df):
        print('WARNING: dropping records during line conversion')

    return MapSource(name='World Boundaries',
                     geometry_type='line',
                     df=line_df,
                     cmap=['black', 'black'],
                     xfield='x',
                     yfield='y',
                     agg_func='max',
                     dynspread=2,
                     shade_how='linear',
                     key='world-boundaries',
                     text='World Boundaries')


def world_cities_source():
    data = gpd.datasets.get_path('naturalearth_cities')
    gdf = gpd.read_file(data)
    gdf = reproject_vector(gdf)
    gdf['X'] = gdf.geometry.apply(lambda p: p.x)
    gdf['Y'] = gdf.geometry.apply(lambda p: p.y)
    spgdf = spatialpandas.GeoDataFrame(gdf, geometry='geometry')
    return MapSource(name='World Cities',
                     geometry_type='point',
                     cmap=['black', 'black'],
                     df=spgdf,
                     xfield='X',
                     yfield='Y',
                     dynspread=2,
                     shade_how='linear',
                     key='world-cities',
                     text='World Cities')


def nybb_source():
    data = gpd.datasets.get_path('nybb')
    gdf = gpd.read_file(data)
    gdf = reproject_vector(gdf)
    spgdf = spatialpandas.GeoDataFrame(gdf, geometry='geometry')
    return MapSource(name='NYC Admin',
                     df=spgdf,
                     xfield='geometry',
                     yfield='geometry',
                     zfield='BoroCode',
                     agg_func='max',
                     span='min/max',
                     dynspread=None,
                     shade_how='linear',
                     geometry_type='polygon',
                     key='nybb',
                     text='NYC Admin')


def elevation_source():
    HERE = path.abspath(path.dirname(__file__))
    FIXTURES_DIR = path.join(HERE, 'tests', 'fixtures')
    elevation_path = path.join(FIXTURES_DIR, 'elevation.tif')
    arr = load_raster(elevation_path)
    arr.data = arr.data.astype('f8')
    arr = reproject_raster(arr)
    return MapSource(name='NYC Admin',
                     df=arr,
                     xfield='geometry',
                     yfield='geometry',
                     raster_interpolate='linear',
                     shade_how='linear',
                     span='min/max',
                     geometry_type='raster',
                     key='elevation',
                     text='Elevation')


def get_user_datasets() -> dict:
    return {}


# TODO: Add default line and raster datasets
default_datasets = {
    'world-countries': world_countries_source(),
    'world-boundaries': world_boundaries_source(),
    'world-cities': world_cities_source(),
    'nybb': nybb_source(),
    'elevation': elevation_source()
}

user_datasets = get_user_datasets()
datasets = {**default_datasets, **user_datasets}

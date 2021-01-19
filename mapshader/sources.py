import geopandas as gpd

import pandas as pd

import spatialpandas

from mapshader.colors import colors


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
    world = world.to_crs(epsg=3857)
    spgdf = spatialpandas.GeoDataFrame(world, geometry='geometry')
    return MapSource(name='World Countries',
                     geometry_type='polygon',
                     df=spgdf,
                     xfield='geometry',
                     yfield='geometry',
                     zfield='pop_est',
                     agg_func='sum',
                     dynspread=None,
                     shade_how='linear',
                     key='world-countries',
                     text='World Countries')


def world_cities_source():
    data = gpd.datasets.get_path('naturalearth_cities')
    gdf = gpd.read_file(data)
    gdf = gdf.to_crs(epsg=3857)
    gdf['X'] = gdf.geometry.apply(lambda p: p.x)
    gdf['Y'] = gdf.geometry.apply(lambda p: p.y)
    spgdf = spatialpandas.GeoDataFrame(gdf, geometry='geometry')
    return MapSource(name='World Cities',
                     geometry_type='point',
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
    gdf = gdf.to_crs(epsg=3857)
    spgdf = spatialpandas.GeoDataFrame(gdf, geometry='geometry')
    return MapSource(name='NYC Admin',
                     df=spgdf,
                     xfield='geometry',
                     yfield='geometry',
                     zfield='BoroCode',
                     agg_func='max',
                     dynspread=None,
                     shade_how='linear',
                     geometry_type='polygon',
                     key='nybb',
                     text='NYC Admin')


def get_user_datasets() -> dict:
    return {}


# TODO: Add default line and raster datasets
default_datasets = {
    'world-countries': world_countries_source(),
    'world-cities': world_cities_source(),
    'nybb': nybb_source()
}

user_datasets = get_user_datasets()
datasets = {**default_datasets, **user_datasets}

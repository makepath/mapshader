import geopandas as gpd

import pandas as pd
import numpy as np


def find_and_set_categoricals(df):
    '''
    Experimental utility to find undefined categorical categories
    '''

    categorical_fields = []
    non_categorical_object_fields = []

    for c in df.columns:

        print(c)

        if df[c].values.dtype == 'object':

            if len(df) > 3000 and len(np.unique(df[c].head(3000).astype('str'))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            elif len(df) > 1000 and len(np.unique(df[c].head(1000).astype('str'))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            elif len(np.unique(df[c].astype(str))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            else:
                non_categorical_object_fields.append(c)

        elif 'int' in str(df[c].values.dtype):

            if len(df) > 100 and len(np.unique(df[c])) < 20:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

    return categorical_fields, non_categorical_object_fields


class MapSource():

    def __init__(self, name=None, df=None, data=None,
                 geometry_type=None, key=None,
                 text=None, fields=None, span=None, route=None,
                 xfield='geometry', yfield='geometry'):

        if fields is None and isinstance(df, (pd.DataFrame, gpd.GeoDataFrame)):
            fields = [dict(key=c, text=c, value=c) for c in df.columns if c != 'geometry']

        self.name = name
        self.df = df
        self.data = data
        self.geometry_type = geometry_type
        self.key = key
        self.text = text
        self.fields = fields
        self.span = span
        self.route = span
        self.xfield = xfield
        self.yfield = yfield
        self.renderers = []  # TODO: Implement in future

    @property
    def tile_url(self):
        url = (f'/{self.key}'
                '/tile'
                '/<xfield>/<yfield>/<zfield>'
                '/<agg_func>/<cmap>/<how>'
                '/<z>/<x>/<y>/<dynspread>/<extras>')
        return url

    @property
    def image_url(self):
        url = (f'/{self.key}'
                '/map'
                '/<xfield>/<yfield>/<zfield>'
                '/<agg_func>/<cmap>/<how>'
                '/<xmin>/<xmax>/<ymin>/<ymax>'
                '/<width>/<height>'
                '/<dynspread>/<extras>')
        return url

    @property
    def geojson_url(self):
        url = (f'/{self.key}'
                '/geojson')
        return url

    @classmethod
    def from_object(obj):
        return MapSource(**obj)


def to_geojson(source: MapSource):
    # TODO: Add in where clause
    # TODO: Add in select by geometry
    # TODO: Add in limit and offset
    return source.df.to_json()


def to_tile(source, xfield, yfield, zfield, agg_func, cmap, how, z, x, y, dynspread=None, extras=None):
    x = int(x)
    y = int(y)
    z = int(z)
    dynspread = int(dynspread)

    url = f'tile/{xfield}/{yfield}/{zfield}/{agg_func}/{cmap}/{how}/{z}/{x}/{y}/{dynspread}/{extras}'

    if extras.lower() == 'none':
        extras = None

    if extras:
        try:
            extras = extras.split(',')
        except:
            print('WARNING: Unable to parse `extras` arg')
            extras = None

    dataset_obj = datasets[dataset]
    img = create_tile(source, xfield, yfield, zfield, agg_func,
                      colors[cmap], how, z, x, y, dynspread, extras).to_bytesio()

    return send_file(img, mimetype='image/png')


def to_image(source:MapSource):
    '''
    @app.route('/<dataset>')
    def serve_image(dataset):

        # parse params
        bounds = request.args.get('bounds')
        xmin, ymin, xmax, ymax = map(float, bounds.split(','))
        width = int(request.args.get('width'))
        height = int(request.args.get('height'))

        # shade image
        cvs = ds.Canvas(plot_width=width,
                        plot_height=height,
                        x_range=(xmin, xmax),
                        y_range=(ymin, ymax))
        agg = cvs.points(df, 'meterswest', 'metersnorth', ds.count_cat('race'))
        img = tf.shade(agg, color_key=color_key, how='eq_hist')
        img_io = img.to_bytesio()
        return send_file(img_io, mimetype='image/png')
    '''
    return 'IMAGE'

    cvs = ds.Canvas(plot_width=width,
                    plot_height=height,
                    x_range=(xmin, xmax),
                    y_range=(ymin, ymax))
    agg = cvs.points(df, 'meterswest', 'metersnorth', ds.count_cat('race'))
    img = tf.shade(agg, color_key=color_key, how='eq_hist')
    img_io = img.to_bytesio()
    return send_file(img_io, mimetype='image/png')


def world_countries_source():
    data = gpd.datasets.get_path('naturalearth_lowres')
    gdf = gpd.read_file(data)
    return MapSource(name='World Countries',
                     df=gdf,
                     geometry_type='polygon',
                     key='world-countries',
                     text='World Countries')


def world_cities_source():
    data = gpd.datasets.get_path('naturalearth_cities')
    gdf = gpd.read_file(data)
    return MapSource(name='World Cities',
                     df=gdf,
                     geometry_type='point',
                     key='world-cities',
                     text='World Cities')


def nybb_source():
    data = gpd.datasets.get_path('nybb')
    gdf = gpd.read_file(data)
    return MapSource(name='NYC Admin',
                     df=gdf,
                     geometry_type='polygon',
                     key='nybb',
                     text='NYC Admin')


def get_user_datasets() -> dict:
    return {}


default_datasets = {
    'world-countries': world_countries_source(),
    'world-cities': world_cities_source(),
    'nybb': nybb_source()
}

user_datasets = get_user_datasets()
datasets = {**default_datasets, **user_datasets}

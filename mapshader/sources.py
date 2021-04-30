from functools import lru_cache as memoized

import os
from os import path
import sys
import yaml

import geopandas as gpd

from mapshader.colors import colors
from mapshader.io import load_raster
from mapshader.io import load_vector
from mapshader.transforms import get_transform_by_name
import spatialpandas


class MapSource(object):

    def __init__(self,  # noqa: C901
                 name=None,
                 description=None,
                 filepath=None,
                 legend=None,
                 config_path=None,
                 data=None,
                 geometry_type=None,
                 key=None,
                 text=None,
                 fields=None,
                 span=None,
                 route=None,
                 geometry_field='geometry',
                 xfield='geometry',
                 yfield='geometry',
                 zfield=None,
                 agg_func=None,
                 raster_interpolate='linear',
                 shade_how='linear',
                 cmap=colors['viridis'],
                 color_key=None,
                 dynspread=None,
                 extras=None,
                 raster_padding=0,
                 service_types=None,
                 full_extent=None,
                 default_extent=None,
                 default_height=256,
                 default_width=256,
                 overviews=None,
                 transforms=None,
                 attrs=None,
                 preload=False):

        if fields is None and isinstance(data, (gpd.GeoDataFrame)):
            fields = [geometry_field]
            if zfield:
                fields.append(zfield)

        if extras is None:
            extras = []

        if transforms is None:
            transforms = []

        if overviews is None:
            overviews = {}

        if service_types is None:
            service_types = ('tile', 'image', 'wms', 'geojson')

        if span == 'min/max' and zfield is None and geometry_type != 'raster':
            raise ValueError('You must include a zfield for min/max scan calculation')

        if legend is not None and geometry_type == 'raster':

            if legend[0].get('value') is not None:
                cmap = {}
                for leg in legend:
                    cor = leg['color']
                    val = leg['value']
                    if isinstance(val, (list, tuple)):
                        val = tuple(val)
                    cmap[val] = cor

        val = 20037508.3427892
        if default_extent is None:
            default_extent = [-val, -val, val, val]

        self.name = name
        self.description = description
        self.filepath = filepath
        self.config_path = config_path
        self.geometry_type = geometry_type
        self.key = key
        self.text = text
        self.legend = legend
        self.fields = fields
        self.span = span
        self.route = route
        self.xfield = xfield
        self.raster_padding = 0
        self.yfield = yfield
        self.zfield = zfield
        self.agg_func = agg_func
        self.overviews = overviews
        self.raster_agg_func = raster_interpolate
        self.shade_how = shade_how
        self.cmap = cmap
        self.color_key = color_key
        self.dynspread = dynspread
        self.extras = extras
        self.service_types = service_types
        self.transforms = transforms
        self.default_extent = default_extent
        self.default_width = default_width
        self.default_height = default_height
        self.preload = preload
        self.geometry_field = geometry_field

        self.is_loaded = False
        self.data = data

        # autoload if overviews are present
        contains_overviews = bool(len([t for t in transforms if 'overviews' in t['name']]))

        if self.preload or contains_overviews:
            self.load()

    @property
    def load_func(self):
        raise NotImplementedError()

    def get_full_extent(self):
        raise NotImplementedError()

    def load(self):

        if self.is_loaded:
            return self

        if self.data is None:

            if self.config_path:
                ogcwd = os.getcwd()
                config_dir = path.abspath(path.dirname(self.config_path))
                os.chdir(config_dir)
                try:
                    data_path = path.abspath(path.expanduser(self.filepath))
                finally:
                    os.chdir(ogcwd)

            elif self.filepath.startswith('zip'):
                print('Zipfile Path', file=sys.stdout)
                data_path = self.filepath

            elif not path.isabs(self.filepath):
                print('Not Absolute', file=sys.stdout)
                data_path = path.abspath(path.expanduser(self.filepath))

            else:
                print('Using Given Filepath unmodified: config{self.config_file}', file=sys.stdout)
                data_path = self.filepath

            data = self.load_func(data_path)
        else:
            data = self.data

        if self.fields:
            data = data[self.fields]

        self.data = data
        self._finish_load()
        return self

    def _finish_load(self):

        if self.is_loaded:
            return self

        self._apply_transforms()

        self.is_loaded = True

    def _apply_transforms(self):

        print('# ----------------------', file=sys.stdout)
        print(f'# APPLYING TRANSFORMS {self.name}', file=sys.stdout)
        print('# ----------------------', file=sys.stdout)
        for trans in self.transforms:
            transform_name = trans['name']
            print(f'\tApplying {transform_name}', file=sys.stdout)
            func = get_transform_by_name(transform_name)
            args = trans.get('args', {})

            if 'overviews' in transform_name:
                self.overviews = func(self.data, **args)

            else:
                self.data = func(self.data, **args)

                # apply transforms to overviews if they exist
                for level, overview_data in self.overviews.items():
                    self.overviews[level] = func(overview_data, **args)

        return self

    @staticmethod
    def from_obj(obj: dict):
        transforms = obj.get('transforms')
        if transforms and isinstance(transforms, (list, tuple)):
            n = 'raster_to_categorical_points'
            has_to_vector = len([t for t in transforms if t['name'] == n])
        else:
            has_to_vector = False

        if obj['geometry_type'] == 'raster' or has_to_vector:
            return RasterSource(**obj)
        else:
            return VectorSource(**obj)


class RasterSource(MapSource):

    @property
    def load_func(self):
        return load_raster

    @property
    @memoized()
    def full_extent(self):
        return (self.data.coords['x'].min().compute().item(),
                self.data.coords['y'].min().compute().item(),
                self.data.coords['x'].max().compute().item(),
                self.data.coords['y'].max().compute().item())


class VectorSource(MapSource):

    @property
    def load_func(self):
        return load_vector

    @property
    @memoized()
    def full_extent(self):
        if isinstance(self.data, spatialpandas.GeoDataFrame):
            return self.data.to_geopandas()[self.geometry_field].total_bounds
        else:
            return self.data[self.geometry_field].total_bounds


class MapService():

    def __init__(self, source: MapSource, renderers=[]):
        self.source = source
        self.renderers = renderers

    @property
    def key(self):
        return f'{self.source.key}-{self.service_type}'

    @property
    def name(self):
        return f'{self.source.name} {self.service_type}'

    @property
    def legend_name(self):
        return f'{self.name}-legend'

    @property
    def default_extent(self):
        return self.source.default_extent

    @property
    def default_width(self):
        return self.source.default_width

    @property
    def default_height(self):
        return self.source.default_height

    @property
    def service_page_url(self):
        return f'/{self.key}'

    @property
    def legend_url(self):
        return f'/{self.key}/legend'

    @property
    def service_page_name(self):
        return f'/{self.key}-{self.service_type}'

    @property
    def service_url(self):
        raise NotImplementedError()

    @property
    def client_url(self):
        raise NotImplementedError()

    @property
    def default_url(self):
        raise NotImplementedError()

    @property
    def service_type(self):
        raise NotImplementedError()


class TileService(MapService):

    @property
    def service_url(self):
        return f'/{self.key}' + '/tile/<z>/<x>/<y>'

    @property
    def client_url(self):
        return f'/{self.key}' + '/tile/{z}/{x}/{y}'

    @property
    def default_url(self):
        return f'/{self.key}' + '/tile/0/0/0'

    @property
    def service_type(self):
        return 'tile'


class ImageService(MapService):

    @property
    def service_url(self):
        url = (f'/{self.key}'
               '/image'
               '/<xmin>/<ymin>/<xmax>/<ymax>'
               '/<width>/<height>')
        return url

    @property
    def client_url(self):
        return f'/{self.key}' + '/image/{XMIN}/{YMIN}/{XMAX}/{YMAX}/{width}/{height}'

    @property
    def default_url(self):
        xmin = self.default_extent[0]
        ymin = self.default_extent[1]
        xmax = self.default_extent[2]
        ymax = self.default_extent[3]
        width = self.default_width
        height = self.default_height
        return f'/{self.key}/image/{xmin}/{ymin}/{xmax}/{ymax}/{width}/{height}'

    @property
    def service_type(self):
        return 'image'

class WMSService(MapService):

    @property
    def service_url(self):
        url = f'/{self.key}/wms'
        return url

    @property
    def client_url(self, width=256, height=256):
        url = f'/{self.key}'
        url += '?bbox={XMIN},{YMIN},{XMAX},{YMAX}'
        url += f'&width={width}&height={height}'
        return url

    @property
    def default_url(self):
        xmin = self.default_extent[0]
        ymin = self.default_extent[1]
        xmax = self.default_extent[2]
        ymax = self.default_extent[3]
        width = self.default_width
        height = self.default_height
        return f'/{self.key}?bbox={xmin},{ymin},{xmax},{ymax}&width={width}&height={height}'

    @property
    def service_type(self):
        return 'wms'


class GeoJSONService(MapService):

    @property
    def service_url(self):
        url = f'/{self.key}/geojson'
        return url

    @property
    def client_url(self):
        url = f'/{self.key}/geojson'
        return url

    @property
    def default_url(self):
        return f'/{self.key}/geojson'

    @property
    def service_type(self):
        return 'geojson'


# ----------------------------------------------------------------------------
# DEFAULT MAP SOURCES
# ----------------------------------------------------------------------------

def world_countries_source():

    # construct transforms
    select_by_attrs_transform = dict(name='select_by_attributes',
                                     args=dict(field='name',
                                               value=['Antarctica', 'Fr. S. Antarctic Lands'],
                                               operator='NOT IN'))
    reproject_transform = dict(name='reproject_vector', args=dict(epsg=3857))
    sp_transform = dict(name='to_spatialpandas', args=dict(geometry_field='geometry'))
    overviews_transform = dict(name='build_vector_overviews',
                               args=dict(levels={'0': 10000,
                                                 '1': 2500,
                                                 '2': 1250,
                                                 '3': 650,
                                                 '4': 300,
                                                 '5': 150,
                                                 '6': 75,
                                                 '7': 32,
                                                 '8': 20,
                                                 '9': 10,
                                                 '10': 5},
                                         geometry_field='geometry'))
    transforms = [select_by_attrs_transform,
                  reproject_transform,
                  overviews_transform,
                  sp_transform]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'World Countries'
    source_obj['key'] = 'world-countries'
    source_obj['text'] = 'World Countries'
    source_obj['description'] = 'World Country Polygons'
    source_obj['geometry_type'] = 'polygon'
    source_obj['agg_func'] = 'max'
    source_obj['shade_how'] = 'linear'
    source_obj['span'] = 'min/max'
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'x'
    source_obj['yfield'] = 'y'
    source_obj['zfield'] = 'pop_est'
    source_obj['filepath'] = gpd.datasets.get_path('naturalearth_lowres')
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile', 'wms', 'image', 'geojson']

    return source_obj


def world_boundaries_source():

    # construct transforms
    select_by_attrs_transform = dict(name='select_by_attributes',
                                     args=dict(field='name',
                                               value=['Antarctica', 'Fr. S. Antarctic Lands'],
                                               operator='NOT IN'))
    reproject_transform = dict(name='reproject_vector', args=dict(epsg=3857))
    polygon_to_line_transform = dict(name='polygon_to_line', args=dict(geometry_field='geometry'))
    sp_transform = dict(name='to_spatialpandas', args=dict(geometry_field='geometry'))
    transforms = [select_by_attrs_transform,
                  polygon_to_line_transform,
                  reproject_transform,
                  sp_transform]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'World Boundaries'
    source_obj['key'] = 'world-boundaries'
    source_obj['text'] = 'World Boundaries'
    source_obj['description'] = 'World Country Boundaries'
    source_obj['geometry_type'] = 'line'
    source_obj['agg_func'] = 'max'
    source_obj['shade_how'] = 'linear'
    source_obj['cmap'] = ['aqua', 'aqua']
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'x'
    source_obj['yfield'] = 'y'
    source_obj['filepath'] = gpd.datasets.get_path('naturalearth_lowres')
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile', 'wms', 'image', 'geojson']

    return source_obj


def world_cities_source():

    # construct transforms
    reproject_transform = dict(name='reproject_vector', args=dict(epsg=3857))
    add_xy_fields_transform = dict(name='add_xy_fields', args=dict(geometry_field='geometry'))
    sp_transform = dict(name='to_spatialpandas', args=dict(geometry_field='geometry'))
    transforms = [reproject_transform, add_xy_fields_transform, sp_transform]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'World Cities'
    source_obj['key'] = 'world-cities'
    source_obj['text'] = 'World Cities'
    source_obj['description'] = 'World Cities Point Locations'
    source_obj['geometry_type'] = 'point'
    source_obj['agg_func'] = 'max'
    source_obj['cmap'] = ['aqua', 'aqua']
    source_obj['shade_how'] = 'linear'
    source_obj['dynspread'] = 2
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'X'
    source_obj['yfield'] = 'Y'
    source_obj['filepath'] = gpd.datasets.get_path('naturalearth_cities')
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile', 'wms', 'image', 'geojson']

    return source_obj


def nybb_source():

    # construct transforms
    reproject_transform = dict(name='reproject_vector', args=dict(epsg=3857))
    sp_transform = dict(name='to_spatialpandas', args=dict(geometry_field='geometry'))
    transforms = [reproject_transform, sp_transform]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'NYC Admin'
    source_obj['key'] = 'nyc-boroughs'
    source_obj['text'] = 'NYC Boroughs'
    source_obj['description'] = 'New York City Boroughs'
    source_obj['geometry_type'] = 'polygon'
    source_obj['agg_func'] = 'max'
    source_obj['shade_how'] = 'linear'
    source_obj['span'] = 'min/max'
    source_obj['dynspread'] = None
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'geometry'
    source_obj['yfield'] = 'geometry'
    source_obj['zfield'] = 'BoroCode'
    source_obj['filepath'] = gpd.datasets.get_path('nybb')
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile', 'wms', 'image', 'geojson']

    return source_obj


def elevation_source():

    # find data path
    HERE = path.abspath(path.dirname(__file__))
    FIXTURES_DIR = path.join(HERE, 'tests', 'fixtures')
    elevation_path = path.join(FIXTURES_DIR, 'elevation.tif')

    # construct transforms
    squeeze_transform = dict(name='squeeze', args=dict(dim='band'))
    cast_transform = dict(name='cast', args=dict(dtype='float64'))
    orient_transform = dict(name='orient_array')
    flip_transform = dict(name='flip_coords', args=dict(dim='y'))
    reproject_transform = dict(name='reproject_raster', args=dict(epsg=3857))
    transforms = [squeeze_transform,
                  cast_transform,
                  orient_transform,
                  flip_transform,
                  reproject_transform]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'Elevation'
    source_obj['key'] = 'elevation'
    source_obj['text'] = 'Elevation'
    source_obj['description'] = 'Global Elevation Dataset'
    source_obj['geometry_type'] = 'raster'
    source_obj['shade_how'] = 'linear'
    source_obj['cmap'] = ['white', 'black']
    source_obj['span'] = (58, 248)
    source_obj['raster_padding'] = 0
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'geometry'
    source_obj['yfield'] = 'geometry'
    source_obj['filepath'] = elevation_path
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile', 'wms', 'image', 'geojson']

    return source_obj


def elevation_source_netcdf():

    # find data path
    HERE = path.abspath(path.dirname(__file__))
    FIXTURES_DIR = path.join(HERE, 'tests', 'fixtures')
    elevation_path = path.join(FIXTURES_DIR, 'elevation.nc')

    # construct transforms
    transforms = []

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'Elevation NetCDF'
    source_obj['key'] = 'elevation-netcdf'
    source_obj['text'] = 'Elevation NetCDF'
    source_obj['description'] = 'Global Elevation Dataset (NetCDF)'
    source_obj['geometry_type'] = 'raster'
    source_obj['shade_how'] = 'linear'
    source_obj['cmap'] = ['white', 'black']
    source_obj['span'] = (58, 248)
    source_obj['raster_padding'] = 0
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'geometry'
    source_obj['yfield'] = 'geometry'
    source_obj['filepath'] = elevation_path
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile', 'wms', 'image', 'geojson']

    return source_obj


def parse_sources(source_objs, config_path=None, contains=None):

    service_classes = {
        'tile': TileService,
        'wms': WMSService,
        'image': ImageService,
        'geojson': GeoJSONService,
    }

    for source in source_objs:
        # create sources
        source_obj = MapSource.from_obj(source)

        for service_type in source['service_types']:
            source['config_path'] = config_path

            if contains and contains not in source.get('key'):
                continue

            # create services
            ServiceKlass = service_classes[service_type]

            # TODO: add renderers here...
            yield ServiceKlass(source=source_obj)


def get_services(config_path=None, include_default=True, contains=None, sources=None):

    source_objs = None

    if sources is not None:
        source_objs = sources

    elif config_path is None:
        print('No Config Found...using default services...', file=sys.stdout)
        source_objs = [world_countries_source(),
                       world_boundaries_source(),
                       world_cities_source(),
                       nybb_source(),
                       elevation_source(),
                       elevation_source_netcdf()]
    else:
        with open(config_path, 'r') as f:
            content = f.read()
            config_obj = yaml.load(content)
            source_objs = config_obj['sources']

        if include_default:
            source_objs += [world_countries_source(),
                            world_boundaries_source(),
                            world_cities_source(),
                            nybb_source(),
                            elevation_source()]

    for service in parse_sources(source_objs, config_path=config_path, contains=contains):
        yield service

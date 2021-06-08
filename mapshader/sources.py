from functools import lru_cache as memoized

import os
from os import path
import sys

import geopandas as gpd

from mapshader.colors import colors
from mapshader.io import load_raster
from mapshader.io import load_vector
from mapshader.transforms import get_transform_by_name

import spatialpandas


class MapSource(object):
    """
    This class represents a map source object.

    Parameters
    ----------
    name : str
        Service name.
    description : str
        Service description.
    filepath : str
        Relative path to the data file.
    legend : list of dict
        Service legend, which could be defined the name, color, value,
        and category.
    config_path : str
        Relative path to the config file.
    data : geopandas.GeoDataFrame
        Service source data.
    geometry_type : str
        Geometry type.
    key : str
        Service route root.
    text : str
        The service introduction text.
    fields : list of str
        The geometry fields.
    span : str or tuple of int;
        Min and max data values to use for colormap/alpha interpolation
        when wishing to override autoranging.
    geometry_field : str, default=geometry
        The geometry field name.
    xfield : str, default=geometry
        The x field name.
    yfield : str, default=geometry
        The y field name.
    zfield : str
        The z field name.
    agg_func : str
        Reduction to compute.
    raster_interpolate : str, default=linear
        Resampling mode when upsampling raster.
        Options include: nearest, linear.
    shade_how : str, default=linear
        The interpolation method to use. Valid strings are 'eq_hist',
        'cbrt', 'log', and 'linear'.
    cmap : list of colors or matplotlib.colors.Colormap, default=viridis
        The colormap to use for 2D agg arrays.
    color_key : dict or iterable
        The colors to use for a 3D (categorical) agg array.
    dynspread : int
        The maximum number of pixels to spread on all shape sides.
    extras : list of str
        The additional transforms over the data, which options could be
        'hillshade' or 'quantile'.
    raster_padding : int, default=0
        The padding to be added over the coordinates bounds range.
    service_types : list of str
        The service types, which options could be 'tile', 'image',
        'wms', and 'geojson'.
    full_extent : tuple of int
        The coordinate of the lower left corner and the coordinate of
        the upper right corner in map units.
    default_extent : list of int
        The service starting extent.
    default_height : int, default=256
        Height of the output aggregate in pixels.
    default_width : int, default=256
        Width of the output aggregate in pixels.
    overviews : dict
        The factors and values to be used when reducing the data
        resolution.
    transforms : list of dict
        The transforms to be applied over the data, which options could
        include: 'reproject_raster', 'reproject_vector', 'orient_array',
        'cast', 'flip_coords', 'build_raster_overviews', 'build_vector_overviews',
        'squeeze', 'to_spatialpandas', 'add_xy_fields', 'select_by_attributes',
        'polygon_to_line', and 'raster_to_categorical_points'.
    preload : bool, default=False
        Preload the data after the service started.
    """

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
        """
        Load the service data.
        """
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
    """
    This class represents a raster source object.

    Parameters
    ----------
    MapSource : mapshader.sources.MapSource
        The map source object.
    """

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
    """
    This class represents a vector source object.

    Parameters
    ----------
    MapSource : mapshader.sources.MapSource
        The map source object.
    """

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

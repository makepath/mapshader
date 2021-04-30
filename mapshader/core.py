import json
import sys

import datashader as ds
import numpy as np
import geopandas as gpd
import dask.array as da


import datashader.transfer_functions as tf
import datashader.reductions as rd
from datashader.colors import rgb

import xarray as xr

from xrspatial import hillshade
from xrspatial.classify import quantile
from xrspatial.utils import height_implied_by_aspect_ratio

from mapshader.mercator import MercatorTileDefinition
from mapshader.sources import MapSource


import spatialpandas


tile_def = MercatorTileDefinition(x_range=(-20037508.34, 20037508.34),
                                  y_range=(-20037508.34, 20037508.34))


def create_agg(source: MapSource,
               xmin: float = None, ymin: float = None,
               xmax: float = None, ymax: float = None,
               x: float = None, y: float = None,
               z: float = None,
               height: int = 256, width: int = 256):

    if x is not None and y is not None and z is not None:
        xmin, ymin, xmax, ymax = tile_def.get_tile_meters(x, y, z)

    elif xmin is None or xmax is None or ymin is None or ymax is None:
        raise ValueError('extent must be provided to create_agg()')

    xfield = source.xfield
    yfield = source.yfield
    zfield = source.zfield
    agg_func = source.agg_func
    geometry_type = source.geometry_type

    if z and z in source.overviews:
        print(f'Using overview: {z}', file=sys.stdout)
        dataset = source.overviews[z]
    else:
        dataset = source.data

    cvs = ds.Canvas(plot_width=width, plot_height=height,
                    x_range=(xmin, xmax), y_range=(ymin, ymax))

    if geometry_type == 'point':
        return point_aggregation(cvs, dataset, xfield, yfield, zfield, agg_func)

    elif geometry_type == 'line':
        return line_aggregation(cvs, dataset, zfield, agg_func)

    elif geometry_type == 'polygon':
        return polygon_aggregation(cvs, dataset, zfield, agg_func)

    elif geometry_type == 'raster':
        return raster_aggregation(cvs, dataset, agg_func, padding=source.raster_padding)
    else:
        raise ValueError('Unkown geometry type for {}'.format(dataset['name']))


def point_aggregation(cvs, data, xfield, yfield, zfield, agg_func):
    if zfield:
        return cvs.points(data, xfield, yfield, getattr(ds, agg_func)(zfield))
    else:
        return cvs.points(data, xfield, yfield)


def line_aggregation(cvs, data, zfield, agg_func):
    if zfield:
        return cvs.line(data,
                        geometry='geometry',
                        agg=getattr(ds, agg_func)(zfield))
    else:
        return cvs.line(data, geometry='geometry')


def polygon_aggregation(cvs, data, zfield, agg_func):
    if zfield:
        return cvs.polygons(data,
                            'geometry',
                            agg=getattr(ds, agg_func)(zfield))
    else:
        return cvs.polygons(data, 'geometry')


def get_data_array_extent(dataarray):
    return (dataarray.coords['x'].min().item(),
            dataarray.coords['y'].min().item(),
            dataarray.coords['x'].max().item(),
            dataarray.coords['y'].max().item())


def raster_aggregation(cvs, data, interpolate='linear', padding=0, agg_method=rd.max()):
    xmin, xmax = cvs.x_range
    ymin, ymax = cvs.y_range
    xdrange = (xmax - xmin) * (1 + 2 * padding)
    ydrange = (ymax - ymin) * (1 + 2 * padding)
    xsize = cvs.plot_width * (1 + 2 * padding)
    ysize = cvs.plot_height * (1 + 2 * padding)

    if padding > 0:
        new_xmin = xmin - xdrange
        new_ymin = ymin - ydrange
        new_xmax = xmin + xdrange
        new_ymax = xmin + ydrange
    else:
        new_xmin = xmin
        new_ymin = ymin
        new_xmax = xmax
        new_ymax = ymax

    stcvs = ds.Canvas(plot_width=xsize,
                      plot_height=ysize,
                      x_range=(new_xmin, new_xmax),
                      y_range=(new_ymin, new_ymax))

    try:
        agg = stcvs.raster(data, interpolate=interpolate, agg=agg_method)
    except ValueError:
        agg = xr.DataArray(np.zeros(shape=(ysize, xsize), dtype=np.uint32),
                           coords={'x': np.linspace(new_xmin, new_xmax, xsize),
                                   'y': np.linspace(new_ymin, new_ymax, ysize)},
                           dims=['x', 'y'])

    return agg


additional_transforms = {'hillshade': hillshade,
                         'quantile': quantile}

def apply_additional_transforms(source: MapSource, agg: xr.DataArray):
    agg = agg.astype('float64')
    agg.data[agg.data == 0] = np.nan
    for e in source.extras:
        if e in additional_transforms:
            trans = additional_transforms.get(e)
            if trans is not None:
                agg = trans(agg)
            else:
                raise ValueError(f'Invalid transform name {e}')

    return source, agg


def shade_discrete(agg, color_key, name='shaded', alpha=255, nodata=0):

    if not agg.ndim == 2:
        raise ValueError("agg must be 2D")

    data = ds.utils.orient_array(agg)

    # check for dask array
    if isinstance(data, da.Array):
        data = data.compute()
    else:
        data = data.copy()

    # support grouped color_key
    first_cat = tuple(color_key.keys())[0]
    if isinstance(first_cat, (list, tuple)):
        cats = []
        colors = []
        for categories, val in color_key.items():
            cor = rgb(val)
            for c in categories:
                cats.append(c)
                colors.append(cor)
    else:
        cats = color_key.keys()
        colors = [rgb(color_key[c]) for c in cats]

    rs, gs, bs = map(np.array, zip(*colors))
    h, w = agg.shape

    r = np.zeros((h, w), dtype=np.uint8)
    g = np.zeros((h, w), dtype=np.uint8)
    b = np.zeros((h, w), dtype=np.uint8)

    for i, c in enumerate(cats):
        value_mask = data == c
        r[value_mask] = rs[i]
        g[value_mask] = gs[i]
        b[value_mask] = bs[i]

    a = np.where(np.logical_or(np.isnan(r), r <= nodata), 0, alpha)
    img = np.dstack((r, g, b, a)).astype('uint8').view(dtype=np.uint32).reshape(a.shape)
    return tf.Image(img, coords=agg.coords, dims=agg.dims, name=name)


def shade_agg(source: MapSource, agg: xr.DataArray, xmin, ymin, xmax, ymax):
    df = source.data
    zfield = source.zfield
    geometry_type = source.geometry_type
    how = source.shade_how
    cmap = source.cmap
    span = source.span

    if isinstance(cmap, dict):
        agg.data = agg.data.astype(np.uint64)
        return shade_discrete(agg, color_key=cmap)
    else:
        if span and span == 'min/max' and geometry_type == 'raster':

            # TODO: make this work for dask

            # TODO: don't need to calculate min each time...move into MapSource
            print('Shade Raster with Span ({}, {})'.format(float(df.min().item()),
                                                           float(df.max().item()) + 1))
            img = tf.shade(agg, cmap=cmap,
                           how=how, span=(int(df.min(skipna=True).item()),
                                          int(df.max(skipna=True).item())+1))

            # TODO: don't do this unless we need to...check source.padding
            return img.loc[{'x': slice(xmin, xmax), 'y': slice(ymax, ymin)}]

        elif span and span == 'min/max':
            print('Shade with Span')
            return tf.shade(agg, cmap=cmap, how=how, span=(np.nanmin(df[zfield]),
                                                           np.nanmax(df[zfield])))
        elif isinstance(span, (tuple, list)):
            return tf.shade(agg, cmap=cmap, how=how, span=span)
        else:
            print('Shade without Span')
            return tf.shade(agg, cmap=cmap, how=how)

def to_raster(source: MapSource,
              xmin: float = None, ymin: float = None,
              xmax: float = None, ymax: float = None,
              height: int = None, width: int = None):

    if height is None and width is None:
        width = 1000

    sxmin, symin, sxmax, symax = source.full_extent

    if xmin is None:
        xmin = sxmin

    if ymin is None:
        ymin = symin

    if xmax is None:
        xmax = sxmax

    if ymax is None:
        ymax = symax

    # handle null h/w
    if height is None:
        x_range, y_range = ((xmin, xmax), (ymin, ymax))
        height = height_implied_by_aspect_ratio(width, x_range, y_range)

    if width is None:
        x_range, y_range = ((xmin, xmax), (ymin, ymax))
        width = height_implied_by_aspect_ratio(height, y_range, x_range)

    # handle out of bounds
    if xmin < sxmin and ymin < symin and xmax > symax and ymax > symax:
        agg = tf.Image(np.zeros(shape=(height, width), dtype=np.uint32),
                       coords={'x': np.linspace(xmin, xmax, width),
                               'y': np.linspace(ymin, ymax, height)},
                       dims=['x', 'y'])
        return agg

    return create_agg(source, xmin, ymin, xmax, ymax, None, None, None, height, width)


def render_map(source: MapSource,  # noqa: C901
               xmin: float = None, ymin: float = None,
               xmax: float = None, ymax: float = None,
               x: float = None, y: float = None,
               z: float = None,
               height: int = None, width: int = None, ):

    if x is not None and y is not None and z is not None:
        xmin, ymin, xmax, ymax = tile_def.get_tile_meters(x, y, z)

    sxmin, symin, sxmax, symax = source.full_extent

    # handle null extent
    if xmin is None:
        xmin = sxmin

    if ymin is None:
        ymin = symin

    if xmax is None:
        xmax = sxmax

    if ymax is None:
        ymax = symax

    # handle null h/w
    if height is None and width is None:
        width = 1000

    if height is None:
        x_range, y_range = ((xmin, xmax), (ymin, ymax))
        height = height_implied_by_aspect_ratio(width, x_range, y_range)

    if width is None:
        x_range, y_range = ((xmin, xmax), (ymin, ymax))
        width = height_implied_by_aspect_ratio(height, y_range, x_range)

    # handle out of bounds
    if xmin < sxmin and ymin < symin and xmax > symax and ymax > symax:
        agg = tf.Image(np.zeros(shape=(height, width), dtype=np.uint32),
                       coords={'x': np.linspace(xmin, xmax, width),
                               'y': np.linspace(ymin, ymax, height)},
                       dims=['x', 'y'])
        img = shade_agg(source, agg, xmin, ymin, xmax, ymax)
        return img

    agg = create_agg(source, xmin, ymin, xmax, ymax, x, y, z, height, width)

    if source.span and isinstance(source.span, (list, tuple)):
        agg = agg.where((agg >= source.span[0]) & (agg <= source.span[1]))

    source, agg = apply_additional_transforms(source, agg)
    img = shade_agg(source, agg, xmin, ymin, xmax, ymax)

    # apply dynamic spreading ----------
    if source.dynspread and source.dynspread > 0:
        img = tf.dynspread(img, threshold=1, max_px=int(source.dynspread))

    return img


def get_geojson(source: MapSource, simplify=None):

    if isinstance(source.data, spatialpandas.GeoDataFrame):
        gdf = source.data.to_geopandas()

    elif isinstance(source.data, gpd.GeoDataFrame):
        gdf = source.data

    else:
        # TODO: add proper line geojson (core.render_geojson)
        if source.geometry_type in ('line', 'raster'):
            return source.data.to_dict()
        return source.data

    if simplify:
        gdf = gdf.copy()
        gdf[source.geometry_field] = gdf[source.geometry_field].simplify(simplify)

    return gdf


def get_legend(source: MapSource):
    if source.legend is not None:
        return source.legend
    return []


def render_geojson(source: MapSource, simplify=None):
    geojson = get_geojson(source, simplify)

    if isinstance(geojson, dict):
        return json.dumps(geojson)

    return geojson.to_json()


def render_legend(source: MapSource):
    return json.dumps(render_legend(source))

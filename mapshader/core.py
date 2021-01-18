from threading import Thread
import fiona
from fiona.session import AWSSession

import geopandas as gpd
import pandas as pd

import datashader as ds
import numpy as np

import boto3
from copy import copy

import datashader.transfer_functions as tf

from pyproj import Proj, transform

from tileshader.mercator import MercatorTileDefinition


from xrspatial import hillshade
from xrspatial.classify import quantile

from mapshader.sources import datasets
from mapshader.colors import colors


tile_def = MercatorTileDefinition(x_range=(-20037508.34, 20037508.34),
                                  y_range=(-20037508.34, 20037508.34))


def create_agg(dataset, xfield, yfield, zfield, agg_func, x, y, z, height=256, width=256):

    xmin, ymin, xmax, ymax = tile_def.get_tile_meters(x, y, z)

    cvs = ds.Canvas(plot_width=width,
                    plot_height=height,
                    x_range=(xmin, xmax),
                    y_range=(ymin, ymax))

    if dataset['geometry'] == 'point':
        return point_aggregation(cvs, dataset, xfield, yfield, zfield, agg_func)
    elif dataset['geometry'] == 'line':
        return line_aggregation(cvs, dataset, xfield, zfield, agg_func)
    elif dataset['geometry'] == 'polygon':
        return polygon_aggregation(cvs, dataset, zfield, agg_func)
    elif dataset['geometry'] == 'raster':
        return raster_aggregation(lambda cvs: dataset['df'],
                                  xmin, ymin, xmax, ymax)
    elif dataset['geometry'] == 'dynamic-raster':
        return raster_aggregation(dataset['get_data'],
                                  xmin, ymin, xmax, ymax)
    else:
        raise ValueError('Unkown geometry type for {}'.format(dataset['name']))


def point_aggregation(cvs, dataset, xfield, yfield, zfield, agg_func):
    if zfield:
        return cvs.points(dataset['df'], xfield, yfield, getattr(ds, agg_func)(zfield))
    else:
        return cvs.points(dataset['df'], xfield, yfield)


def line_aggregation(cvs, dataset, xfield, zfield, agg_func):
    if zfield:
        return cvs.line(dataset['df'], xfield,
                        agg=getattr(ds, agg_func)(zfield))
    else:
        return cvs.line(dataset['df'], xfield)


def polygon_aggregation(cvs, dataset, zfield, agg_func):
    if zfield:
        return cvs.polygons(dataset['df'],
                            'geometry',
                            agg=getattr(ds, agg_func)(zfield))
    else:
        return cvs.polygons(dataset['df'], 'geometry')


def raster_aggregation(get_aggregate_func, xmin, ymin, xmax, ymax):
    xdrange = xmax - xmin
    ydrange = ymax - ymin
    stcvs = ds.Canvas(plot_width=256 * 3,
                      plot_height=256 * 3,
                      x_range=(xmin - xdrange, xmax + xdrange),
                      y_range=(ymin - ydrange, ymax + ydrange))
    return stcvs.raster(get_aggregate_func(stcvs))


additional_transforms = {'hillshade': hillshade,
                         'quantile': quantile}

def apply_additional_transforms(agg, extras):
    agg = agg.astype('float64')
    agg.data[agg.data == 0] = np.nan
    for e in extras:
        if e in additional_transforms:
            agg = additional_transforms[e](agg)


def shade_agg(dataset, agg, cmap, how, zfield, x, y, z):
    span = dataset.get('span')

    if isinstance(cmap, dict):
        return tf.shade(agg, color_key=cmap)
    else:
        if span and span == 'min/max' and dataset['geometry'] == 'raster':
            print('Shade Raster with Span ({}, {})'.format(int(dataset['df'].min().item()),
                                                           int(dataset['df'].max().item() + 1)))
            img = tf.shade(agg, cmap=cmap, how=how, span=(int(dataset['df'].min().item()),
                                                          int(dataset['df'].max().item())))
            xmin, ymin, xmax, ymax = tile_def.get_tile_meters(x, y, z)
            return img.loc[{'x': slice(xmin, xmax), 'y': slice(ymin, ymax)}]
        elif span and span == 'min/max':
            print('Shade with Span')
            return tf.shade(agg, cmap=cmap, how=how, span=(np.nanmin(dataset['df'][zfield]),
                                                           np.nanmax(dataset['df'][zfield])))
        elif isinstance(span, tuple):
            return tf.shade(agg, cmap=cmap, how=how, span=span)
        else:
            print('Shade without Span')
            return tf.shade(agg, cmap=cmap, how=how)


def create_tile(dataset, xfield, yfield, zfield, agg_func, cmap, how, z, x, y, dynspread, extras):
    '''
    span: dict<zoom_level_int:(min_value, max_value)
    '''

    # flags ----------------------------
    if zfield == 'None':
        zfield = None

    has_df = 'df' in dataset
    zfield_has_dtype = zfield and has_df and hasattr(dataset['df'][zfield], 'dtype')

    # handle categorical field ---------
    has_cat_zfield = zfield_has_dtype and isinstance(dataset['df'][zfield].dtype, pd.CategoricalDtype)
    if has_cat_zfield and isinstance(cmap, (list, tuple)):
        agg_func = 'count_cat'
        keys = list(dataset['df'][zfield].unique())
        color_range = list(np.arange(len(keys)))
        colors = [cmap[i % len(cmap)] for i in color_range]
        cmap = dict(zip(keys, colors))

    # handle categorical field ---------
    agg = create_agg(dataset, xfield, yfield, zfield, agg_func, x, y, z)

    # handle categorical field ---------
    if extras and isinstance(extras, list):
        apply_additional_transforms(agg, extras)

    # apply dynamic spreading ----------
    img = shade_agg(dataset, agg, cmap, how, zfield, x, y, z)

    # apply dynamic spreading ----------
    if dynspread and dynspread > 0:
        img = tf.dynspread(img, threshold=1, max_px=int(dynspread))

    return img


def _upload_tile(img, bucket, url):
    try:
        s3.upload_fileobj(img, bucket, url,
                          ExtraArgs={'ACL': 'public-read',
                                     'ContentType': 'image/png'})
    except:
        import sys
        print('Failed to write tile to S3', file=sys.stdout)



import rioxarray  # NOQA
import xarray as xr
import datashader as ds
import numpy as np
import pandas as pd
import geopandas as gpd
import spatialpandas

from xrspatial.utils import height_implied_by_aspect_ratio

wb_proj_str = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs'

wgs84_proj_str = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'

def reproject_raster(arr: xr.DataArray, epsg=3857):
    if epsg == 3857:
        return arr.rio.reproject(wb_proj_str)
    else:
        raise ValueError(f'Raster Projection Error: Invalid EPSG {epsg}')


def reproject_vector(gdf: gpd.GeoDataFrame, epsg=3857):
    return gdf.to_crs(epsg=epsg)


def flip_coords(arr, dim):
    args = {dim: list(reversed(arr.coords[dim]))}
    arr = arr.assign_coords(**args)
    return arr


def to_spatialpandas(gdf: gpd.GeoDataFrame, geometry_field='geometry'):
    return spatialpandas.GeoDataFrame(gdf, geometry=geometry_field)


def squeeze(arr, dim):
    return arr.squeeze().drop(dim)


def cast(arr, dtype):
    arr.data = arr.data.astype(dtype)
    return arr


def orient_array(arr):
    arr.data = ds.utils.orient_array(arr)
    return arr

def get_data_array_extent(dataarray):
    return (dataarray.coords['x'].min().item(),
            dataarray.coords['y'].min().item(),
            dataarray.coords['x'].max().item(),
            dataarray.coords['y'].max().item())

def canvas_like(dataarray):

    if isinstance(dataarray, xr.DataArray):
        extent = get_data_array_extent(dataarray)
    else:
        raise TypeError('like object must be DataArray')

    x_range = (extent[0], extent[2])
    y_range = (extent[1], extent[3])
    H = len(dataarray.coords['y'])
    W = len(dataarray.coords['x'])

    return ds.Canvas(plot_width=W, plot_height=H,
                     x_range=x_range, y_range=y_range)


def build_vector_overviews(gdf, levels, geometry_field='geometry'):
    values = {}
    overviews = {}
    for level, simplify_tol in levels.items():

        if simplify_tol in values:
            overviews[int(level)] = values[simplify_tol]

        simplified_gdf = gdf.copy()
        simplified_gdf[geometry_field] = simplified_gdf[geometry_field].simplify(simplify_tol)
        overviews[int(level)] = simplified_gdf
        values[simplify_tol] = simplified_gdf
    return overviews


def build_raster_overviews(arr, levels, interpolate='linear'):
    print(arr, levels)
    values = {}
    overviews = {}
    for level, resolution in levels.items():

        if resolution in values:
            overviews[int(level)] = values[resolution]

        cvs = canvas_like(arr)
        height = height_implied_by_aspect_ratio(resolution, cvs.x_range, cvs.y_range)
        cvs.plot_height = height
        cvs.plot_width = resolution
        agg = cvs.raster(arr, interpolate=interpolate).compute().chunk(512, 512)

        overviews[int(level)] = agg
        values[resolution] = agg
    return overviews


def add_xy_fields(gdf, geometry_field='geometry'):
    gdf['X'] = gdf[geometry_field].apply(lambda p: p.x)
    gdf['Y'] = gdf[geometry_field].apply(lambda p: p.y)
    return gdf


def select_by_attributes(gdf, field, value, operator='IN'):

    if operator == 'IN':
        return gdf[gdf[field].isin(value)]

    elif operator == 'NOT IN':
        return gdf[~gdf[field].isin(value)]

    elif operator == 'EQUALS':
        return gdf[gdf[field] == value]

    elif operator == 'NOT EQUALS':
        return gdf[gdf[field] != value]

    elif operator == 'LT':
        return gdf[gdf[field] < value]

    elif operator == 'GT':
        return gdf[gdf[field] > value]

    elif operator == 'LTE':
        return gdf[gdf[field] <= value]

    elif operator == 'GTE':
        return gdf[gdf[field] >= value]


def polygon_to_line(gdf, geometry_field='geometry'):
    gdf[geometry_field] = gdf[geometry_field].boundary
    return gdf


_transforms = {
    'reproject_raster': reproject_raster,
    'reproject_vector': reproject_vector,
    'orient_array': orient_array,
    'cast': cast,
    'flip_coords': flip_coords,
    'build_raster_overviews': build_raster_overviews,
    'build_vector_overviews': build_vector_overviews,
    'squeeze': squeeze,
    'to_spatialpandas': to_spatialpandas,
    'add_xy_fields': add_xy_fields,
    'select_by_attributes': select_by_attributes,
    'polygon_to_line': polygon_to_line,
}


def get_transform_by_name(name: str):
    return _transforms[name]

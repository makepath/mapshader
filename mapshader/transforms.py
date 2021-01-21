import rioxarray  # NOQA
import xarray as xr
import datashader as ds
import numpy as np
import pandas as pd
import geopandas as gpd
import datashader as ds

from xrspatial.utils import height_implied_by_aspect_ratio

wb_proj_str = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs'

wgs84_proj_str = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'

def reproject_raster(arr: xr.DataArray, epsg=3857):
    if epsg == 3857:
        return arr.rio.reproject(wb_proj_str)
    else:
        raise ValueError(f'Raster Projection Error: Invalid EPSG {epsg}')
    pass


def reproject_vector(gdf: gpd.GeoDataFrame, epsg=3857):
    return gdf.to_crs(epsg=epsg)


def flip_coords(arr, dim):
    args = {dim: list(reversed(arr.coords[dim]))}
    arr = arr.assign_coords(**args)
    return arr


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

def canvas_like(dataarray, plot_height=None, plot_width=None):

    if isinstance(dataarray, xr.DataArray):
        extent = get_data_array_extent(dataarray)
    else:
        raise TypeError('like object must be DataArray')

    x_range = (extent[0], extent[2])
    y_range = (extent[1], extent[3])
    H = plot_height if plot_height else len(dataarray.coords['y'])
    W = plot_width if plot_width else len(dataarray.coords['x'])

    return ds.Canvas(plot_width=W, plot_height=H,
                     x_range=x_range, y_range=y_range)

def build_raster_overviews(arr, levels=(1000, 2000, 4000), interpolate='linear'):

    overviews = []
    for level in levels:
        cvs = canvas_like(arr)
        height = height_implied_by_aspect_ratio(level, cvs.x_range, cvs.y_range)
        cvs.plot_height = height
        cvs.plot_width = level
        agg = cvs.raster(arr, interpolate=interpolate)
        overviews.append(agg)
    return overviews


_transforms = {
    'reproject_raster': reproject_raster,
    'reproject_vector': reproject_vector,
    'orient_array': orient_array,
    'cast': cast,
    'flip_coords': flip_coords,
    'build_raster_overviews': build_raster_overviews,
    'squeeze': squeeze
}

def get_transform_by_name(name: str):
    return _transforms[name]


def line_geoseries_to_datashader_line(series: gpd.GeoSeries):
    # TODO: This is slow! Make this faster!
    xs = []
    ys = []
    for s in series.values:
        try:
            coords = s.coords.xy
            xs += coords[0].tolist()
            ys += coords[1].tolist()

            xs.append(np.nan)
            ys.append(np.nan)
        except:
            continue

    return pd.DataFrame(dict(x=xs, y=ys))

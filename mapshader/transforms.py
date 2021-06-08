import sys
import rioxarray  # NOQA - always import before xarray...
import xarray as xr
import dask.array as da
import datashader as ds
import geopandas as gpd
import spatialpandas

from xrspatial.utils import height_implied_by_aspect_ratio

wb_proj_str = ('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0'
               ' +units=m +nadgrids=@null +wktext +no_defs')

wgs84_proj_str = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'

us_national_equal_area_str = (
    '+proj=laea +lat_0=45 +lon_0=-100 +x_0=0 +y_0=0 +a=6370997 '
    '+b=6370997 +units=m +no_defs'
)

projections = {
    3857: wb_proj_str,
    4326: wgs84_proj_str,
    2163: us_national_equal_area_str
}

def reproject_raster(arr: xr.DataArray, epsg=3857):
    """
    Reproject raster data.

    Parameters
    ----------
    arr : xarray.DataArray
        The raster data.
    epsg : int
        The coordinate systems code.

    Returns
    -------
    reproj_data : xarray.DataArray
        The reprojected data.
    """
    global projections

    try:
        proj_str = projections[epsg]
        return arr.rio.reproject(proj_str)
    except KeyError:
        raise ValueError(f'Raster Projection Error: Invalid EPSG {epsg}')


def reproject_vector(gdf: gpd.GeoDataFrame, epsg=3857):
    """
    Reproject vector data.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The vector data.
    epsg : int
        The coordinate systems code.

    Returns
    -------
    reproj_data : geopandas.GeoDataFrame
        The reprojected data.
    """
    return gdf.to_crs(epsg=epsg)


def flip_coords(arr, dim):
    """
    Flip the geometry coordinates.

    Parameters
    ----------
    arr : xarray.DataArray
        The data source.
    dim : str
        The coordinate field name.

    Returns
    -------
    flipped_data : xarray.DataArray
        The flipped coordinates data.
    """
    args = {dim: list(reversed(arr.coords[dim]))}
    arr = arr.assign_coords(**args)
    return arr


def to_spatialpandas(gdf: gpd.GeoDataFrame, geometry_field='geometry'):
    """
    Convert a ``geopandas.GeoDataFrame`` to ``spatialpandas.GeoDataFrame``.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The data source.
    geometry_field : str
        Geometry field on GeoDataFrame

    Returns
    -------
    spatial_gdf : spatialpandas.GeoDataFrame
    """
    return spatialpandas.GeoDataFrame(gdf, geometry=geometry_field)


def squeeze(arr, dim):
    """
    Return a new ``xarray.DataArray`` with squeezed data.

    Parameters
    ----------
    arr : xarray.DataArray
        The data source.
    dim : str
        Drop a specific field name.

    Returns
    -------
    squeezed_data : xarray.DataArray
        The squeezed data.
    """
    return arr.squeeze().drop(dim)


def cast(arr, dtype):
    """
    Cast the data to a specific data type.

    Parameters
    ----------
    arr : xarray.DataArray
        The data source.
    dtype : str
        Data type.

    Returns
    -------
    casted_data : xarray.DataArray
        The casted data.
    """
    arr.data = arr.data.astype(dtype)
    return arr


def orient_array(arr):
    """
    Reorients the array to a canonical orientation depending on
    whether the x and y-resolution values are positive or negative.

    Parameters
    ----------
    arr : xarray.DataArray
        Data to be reoriented

    Returns
    -------
    reoriented_data : numpy.ndarray
        Reoriented 2d NumPy ndarray
    """
    arr.data = ds.utils.orient_array(arr)
    return arr

def get_data_array_extent(dataarray):
    """
    Get the coordinate of the lower left corner and the coordinate of
    the upper right corner in map units.

    Parameters
    ----------
    dataarray : xarray.DataArray
        The input datasource.

    Returns
    -------
    extent : tuple of integers
        A tuple of ``(xmin, ymin, xmax, ymax)`` values.
    """
    return (dataarray.coords['x'].min().item(),
            dataarray.coords['y'].min().item(),
            dataarray.coords['x'].max().item(),
            dataarray.coords['y'].max().item())

def canvas_like(dataarray):
    """
    Get a ``datashader.Canvas`` according to a ``xarray.DataArray`` features.

    Parameters
    ----------
    dataarray : xarray.DataArray
        The input datasource.

    Returns
    -------
    canvas : datashader.Canvas
        An abstract canvas representing the space in which to bin.
    """

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
    """
    Reduce the vector data resolution.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The vector data.
    levels : dict
        The factors and values to be used when reducing the data
        resolution.
    geometry_field : str, default=geometry
        The geometry field name.

    Returns
    -------
    overviews : geopandas.GeoDataFrame
        The reduced resolution vector data.
    """
    values = {}
    overviews = {}
    for level, simplify_tol in levels.items():

        msg = f'Generating Vector Overview level {level} at {simplify_tol} simplify tolerance'
        print(msg, file=sys.stdout)

        if simplify_tol in values:
            overviews[int(level)] = values[simplify_tol]
            continue

        simplified_gdf = gdf.copy()
        simplified_gdf[geometry_field] = simplified_gdf[geometry_field].simplify(simplify_tol)
        overviews[int(level)] = simplified_gdf
        values[simplify_tol] = simplified_gdf
    return overviews


def build_raster_overviews(arr, levels, interpolate='linear'):
    """
    Reduce the raster data resolution.

    Parameters
    ----------
    arr : xarray.DataArray
        The raster data.
    levels : dict
        The factors and values to be used when reducing the data
        resolution.
    interpolate : str, default=linear
        Resampling mode when upsampling raster.
        Options include: nearest, linear.

    Returns
    -------
    overviews : xarray.DataArray
        The reduced resolution raster data.
    """
    values = {}
    overviews = {}
    for level, resolution in levels.items():

        print(f'Generating Raster Overview level {level} at {resolution} pixel width',
              file=sys.stdout)

        if resolution in values:
            overviews[int(level)] = values[resolution]
            continue

        cvs = canvas_like(arr)
        height = height_implied_by_aspect_ratio(resolution, cvs.x_range, cvs.y_range)
        cvs.plot_height = height
        cvs.plot_width = resolution
        agg = (cvs.raster(arr, interpolate=interpolate)
                  .compute()
                  .chunk(512, 512)
                  .persist())

        overviews[int(level)] = agg
        values[resolution] = agg

    return overviews


def add_xy_fields(gdf, geometry_field='geometry'):
    """
    Extract x and y fields from geometry and create new columns with them.
    """
    gdf['X'] = gdf[geometry_field].apply(lambda p: p.x)
    gdf['Y'] = gdf[geometry_field].apply(lambda p: p.y)
    return gdf


def select_by_attributes(gdf, field, value, operator='IN'):
    """
    Filter a ``geopandas.GeoDataFrame`` data.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The vector data.
    field : str
        Column to be filtered.
    value : int or float
        Value to compare when filtering.
    operator : str, default=IN
        Arithmetic operator to be used when filtering.
        Options include: IN, NOT IN, EQUALS, NOT EQUALS, LT, GT, LTE,
        and GTE.

    Returns
    -------
    filtered_data : geopandas.GeoDataFrame
        The filtered data.
    """

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
    """
    Convert geometry type from polygon to line.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The vector data.
    geometry_field : str, default=geometry
        The geometry field name.

    Returns
    -------
    gdf : geopandas.GeoDataFrame
        The converted data.
    """
    gdf[geometry_field] = gdf[geometry_field].boundary
    return gdf


def raster_to_categorical_points(arr, cats: dict, dim: str = 'data'):
    """
    Convert raster data to categorical points.

    Parameters
    ----------
    arr : xarray.DataArray
        The raster data.
    cats : dict
        Categories colors.
    dim : str, default=data
        The categorical column name.

    Returns
    -------
    df : pandas.DataFrame
        The converted data.
    """
    df = None
    if isinstance(arr, da.Array):
        df = arr.compute().to_dataframe()
    else:
        df = arr.to_dataframe()

    df = df.head(1000000)
    df.reset_index(inplace=True)
    df[dim] = [dim].astype('int')
    df[dim] = [dim].astype('category')
    df[dim].cat.categories = [cats.get(s) for s in df[dim].cat.categories]
    return df


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
    'raster_to_categorical_points': raster_to_categorical_points
}


def get_transform_by_name(name: str):
    """
    Get transform function by their name.

    Parameters
    ----------
    name : str
        The transform function name.
    """
    return _transforms[name]

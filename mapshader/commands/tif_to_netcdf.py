from os import path
import sys

import click
import xarray as xr

from mapshader.transforms import cast
from mapshader.transforms import flip_coords
from mapshader.transforms import orient_array
from mapshader.transforms import reproject_raster
from mapshader.transforms import squeeze


@click.command(
    no_args_is_help=True,
    context_settings=dict(help_option_names=['-h', '--help']),
    short_help='Convert GeoTIFF raster file format into a NetCDF file.',
    help=(
        'Convert GeoTIFF raster file format into a NetCDF file '
        'given the `FILEPATH` relative path.'
    ),
)
@click.argument(
    'filepath',
    type=str,
    required=True,
)
@click.option(
    '--x',
    type=str,
    default='x',
    show_default=True,
    help='The x dimension name.',
)
@click.option(
    '--y',
    type=str,
    default='y',
    show_default=True,
    help='The y dimension name.',
)
@click.option(
    '--chunks',
    type=tuple,
    default=(512, 512),
    show_default=True,
    help='Coerce into dask arrays with the given chunks.',
)
@click.option(
    '--data_variable',
    type=str,
    default='data',
    show_default=True,
    help='The data variable name.',
)
@click.option(
    '--fill_na',
    type=int,
    default=-9999,
    show_default=True,
    help='Fill NaN values with the given value.',
)
@click.option(
    '-c',
    '--cast',
    'dtype',
    default='int16',
    show_default=True,
    help='Cast the data to the given type.',
)
@click.option(
    '-r',
    '--reproject',
    'crs',
    type=int,
    default=3857,
    show_default=True,
    help='Reproject the data to the given CRS.',
)
def tif_to_netcdf(
    filepath,
    x,
    y,
    chunks,
    data_variable,
    fill_na,
    dtype,
    crs,
):
    '''
    Convert GeoTIFF raster file format into a NetCDF file given the
    `FILEPATH` relative path.

    Parameters
    ----------
    filepath : str
        GeoTIFF raster file relative path.
    x : str
        The x dimension name.
    y : str
        The y dimension name.
    chunks : tuple of int
        The dask array chunk size for the x and y dimension.
    data_variable : str
        The data variable name.
    fill_na : int or float
        Fill NaN values with the given value.
    dtype : str
        Cast the data to the given type.
    crs : int
        Reproject the data to the given CRS.
    '''
    input_file = path.abspath(path.expanduser(filepath))
    output_file = input_file.replace('.tif', '.nc')

    print(
        'Converting {0} from GeoTIFF to NetCDF file'.format(input_file),
        file=sys.stdout,
    )

    arr = xr.open_rasterio(input_file)

    # Check if the given dimensions exist
    for dimension in (x, y):
        if dimension not in arr.dims:
            raise click.BadParameter(
                "The dimension name {} doesn't exist.".format(dimension)
            )

    arr = squeeze(arr, [d for d in arr.dims if d != x and d != y])
    arr = cast(arr, dtype=dtype)
    arr = orient_array(arr)
    arr = flip_coords(arr, dim=y)
    arr = reproject_raster(arr, epsg=crs)

    dataset = xr.Dataset(
        data_vars={data_variable: (['y', 'x'], arr.chunk(chunks).data)},
        coords={'x': arr.coords[x], 'y': arr.coords[y]},
    )
    dataset.attrs = dict(name=data_variable)
    dataset.to_netcdf(
        path=output_file,
        encoding={data_variable: {'_FillValue': fill_na}},
    )

    print(
        'Conversion complete: {0}'.format(output_file),
        file=sys.stdout,
    )

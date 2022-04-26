from os.path import expanduser, splitext

import geopandas as gpd
import numpy as np
import xarray as xr

from mapshader.multifile import SharedMultiFile


def load_raster(file_path, transforms, force_recreate_overviews,
                xmin=None, ymin=None, xmax=None, ymax=None, chunks=None,
                layername='data'):
    """
    Load raster data.

    Parameters
    ----------
    file_path : str
        Relative path to the file.
    xmin : float
        X-axis minimum range.
    ymin : float
        Y-axis minimum range.
    xmax : float
        X-axis maximum range.
    ymax : float
        Y-axis maximum range.
    layername : str, default=data
        Data layer name.

    Returns
    -------
    arr : xarray.DataArray
        The loaded data.
    """

    file_extension = splitext(file_path)[1]
    if not file_extension:
        raise RuntimeError(f"file_path does not have a file extension: {file_path}")

    arr = None

    if '*' in file_path or file_extension == '.vrt':
        if file_extension in ['.nc', '.tif', '.vrt']:
            arr = SharedMultiFile.get(file_path, transforms, force_recreate_overviews)

    else:
        if file_extension == '.tif':
            arr = xr.open_rasterio(expanduser(file_path), chunks={'y': 512, 'x': 512})

            if hasattr(arr, 'nodatavals'):
                if np.issubdtype(arr.data.dtype, np.integer):
                    arr.data = arr.data.astype('f8')

                for val in arr.nodatavals:
                    arr.data[arr.data == val] = np.nan

            arr.name = file_path

        elif file_extension == '.nc':
            # TODO: add chunk parameter to config
            arr = xr.open_dataset(file_path, chunks={'x': 512, 'y': 512})[layername]
            arr['name'] = file_path

    if arr is None:
        raise TypeError(f"Unable to load raster {file_path}")

    return arr


def load_vector(filepath: str, transforms, force_recreate_overviews):
    """
    Load vector data.

    Parameters
    ----------
    filepath : str
        Relative path to the file.

    Returns
    -------
    gpd : geopandas.DataFrame
        The loaded data.
    """
    return gpd.read_file(filepath)

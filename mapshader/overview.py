import dask.bag as db
import numpy as np
import os
from rasterio.enums import Resampling
import xarray as xr

from .transforms import get_transform_by_name


# There is some code duplication here with MultiFileRaster which should be refactored.

def _apply_transforms(da, transforms):
    # This may be called with either a single xr.DataArray that is a single band of a single
    # NetCDF file, or with the merged output from a number of files called from load_bounds().
    for trans in transforms:
        transform_name = trans['name']
        func = get_transform_by_name(transform_name)
        args = trans.get('args', {})

        if 'overviews' in transform_name:
            pass
        else:
            da = func(da, **args)

    return da

def _get_crs(ds):
    crs = ds.rio.crs
    if not crs:
        # Fallback for reading spatial_ref written in strange way.
        crs = ds.spatial_ref.spatial_ref
    return crs

def _overview_combine(da1, da2):
    # Elementwise maximum taking into account nans.
    return xr.where(np.logical_and(np.isfinite(da1), ~(da1 > da2)), da1, da2)

def _overview_map(filename, band, overview_crs, overview_shape, overview_transform, transforms):
    with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
        da = ds[band]
        da = da.squeeze()
        crs = _get_crs(ds)
        da.rio.set_crs(crs, inplace=True)

    da = _apply_transforms(da, transforms)

    # Reproject to same grid as overview.
    da = da.rio.reproject(
        dst_crs=overview_crs,
        shape=overview_shape,
        transform=overview_transform,
        # resampling=Resampling.average,  # Prefer this, but gives missing pixels.
        resampling=Resampling.bilinear,
        nodata=np.nan)

    return da

def create_single_band_overview(filenames, overview_shape, overview_transform, overview_crs, band,
                                overview_filename, transforms):
    bag = db.from_sequence(filenames)

    # Map from filename to reprojected xr.DataArray.
    bag = bag.map(lambda filename: _overview_map(
        filename, band, overview_crs, overview_shape, overview_transform, transforms))

    # Combine xr.DataArrays using elementwise maximum taking into account nans.
    bag = bag.fold(_overview_combine)

    overview = bag.compute()

    # Remove attrs that can cause problem serializing xarrays.
    for key in ["grid_mapping"]:
        if key in overview.attrs:
            del overview.attrs[key]

    # Save overview as geotiff.
    print(f"Writing overview {overview_filename}", flush=True)
    try:
        overview.rio.to_raster(overview_filename)
    except:  # noqa: E722
        if os.path.isfile(overview_filename):
            os.remove(overview_filename)
        raise

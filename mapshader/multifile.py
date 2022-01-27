from affine import Affine
import geopandas as gpd
from glob import glob
import numpy as np
import os
from rasterio.enums import Resampling
import rioxarray  # noqa: F401
from shapely.geometry import Polygon
from threading import Lock
import xarray as xr

from .mercator import MercatorTileDefinition
from .transforms import get_transform_by_name


tile_def = MercatorTileDefinition(x_range=(-20037508.34, 20037508.34),
                                  y_range=(-20037508.34, 20037508.34))

class SharedMultiFile:
    """
    Simple thread-safe implementation of shared MultiFileNetCDF objects.

    Client code never instantiates a MultiFileNetCDF object directly, instead
    it calls the get() method of this class.  This uses a lock to ensure that
    only one MultiFileNetCDF is ever created and is shared between all the
    clients.
    """
    _lock = Lock()
    _lookup = {}

    @classmethod
    def get(cls, file_path, transforms, force_recreate_overviews):
        with cls._lock:
            shared = cls._lookup.get(file_path, None)
            if not shared:
                shared = MultiFileNetCDF(file_path, transforms, force_recreate_overviews)
                cls._lookup[file_path] = shared
        return shared


class MultiFileNetCDF:
    """
    Proxy for multiple netCDF files that provides a similar interface to
    xr.DataArray.

    This is an interim solution until we replace the objects returned by
    load_raster() and load_vector() with a considered class hierarchy.
    """
    def __init__(self, file_path, transforms, force_recreate_overviews):
        self._file_path = file_path
        self._base_dir = os.path.split(file_path)[0]

        filenames = glob(file_path)
        if not filenames:
            raise RuntimeError(f"Unable to read any files from path {file_path}")

        self._lock = Lock()  # Limits reading of underlying data files to a single thread,
        self._bands = None
        xmins = []
        xmaxs = []
        ymins = []
        ymaxs = []
        polygons = []

        # No thread locking required here as this is done by SharedMultiFile.get().
        for filename in filenames:
            with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                if not self._bands:
                    self._bands = list(ds.data_vars.keys())

                # Can be any one of the DataArrays in the Dataset.
                da = list(ds.values())[0]
                da.rio.set_crs(self._get_crs(ds), inplace=True)
                da = self._apply_transforms(da, transforms)

                # x, y limits determined from coords.
                # Could have been stored as attributes instead?
                xmin = da.x.min().item()
                xmax = da.x.max().item()
                ymin = da.y.min().item()
                ymax = da.y.max().item()

            xmins.append(xmin)
            xmaxs.append(xmax)
            ymins.append(ymin)
            ymaxs.append(ymax)
            polygons.append(Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]))

        # Create GeoDataFrame containing grid information.
        self._grid = gpd.GeoDataFrame(dict(
            geometry=polygons,
            filename=filenames,
            xmin=xmins,
            xmax=xmaxs,
            ymin=ymins,
            ymax=ymaxs,
        ))

        # Actually it is slightly larger than this by half a pixel in each direction
        self._total_bounds = self._grid.total_bounds  # [xmin, ymin, xmax, ymax]

        # Overviews are dealt with separately as they need access to all the combined data.
        # Assume create overviews for each band in the files.
        raster_overviews = list(filter(lambda t: t["name"] == "build_raster_overviews", transforms))
        if len(raster_overviews) > 1:
            raise RuntimeError("build_raster_overviews may only appear once in transforms")
        elif len(raster_overviews) > 0:
            self._create_overviews(raster_overviews[0], transforms, force_recreate_overviews)

    def _apply_transforms(self, da, transforms):
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

    def _create_overviews(self, raster_overviews, transforms, force_recreate_overviews=False):
        print("_create_overviews", raster_overviews)

        overview_directory = self._get_overview_directory()
        if not os.path.isdir(overview_directory):
            os.makedirs(overview_directory)

        # Bounds of entire CRS.
        xmin, ymin, xmax, ymax = tile_def.get_tile_meters(0, 0, 0)

        for level, resolution in raster_overviews["args"]["levels"].items():
            if not force_recreate_overviews:
                # If overviews exist for all bands at this level can abort early.
                if all([os.path.isfile(self._get_overview_filename(band, level))
                        for band in self._bands]):
                    print(f"Overviews exist for all bands at level {level} {self._bands}",
                          flush=True)
                    continue

            # Overview shape, transform and CRS.
            overview_shape = (resolution, resolution)

            dx = (xmax - xmin) / resolution
            dy = (ymax - ymin) / resolution
            overview_transform = Affine.translation(xmin, ymin)*Affine.scale(dx, dy)

            # CRS could be read from first loaded file (after transformation).
            # But it is always EPSG:3857.
            overview_crs = "EPSG:3857"

            # Open a block of files at a time for writing to overview DataArray.
            # Block size of one file initially.
            # Each file needs transforms applied before it can be resampled/reprojected.
            for band in self._bands:
                overview_filename = self._get_overview_filename(band, level)
                if not force_recreate_overviews and os.path.isfile(overview_filename):
                    print(f"Overview already exists {overview_filename}", flush=True)
                    continue

                overview = None
                for filename in self._grid.filename:
                    with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                        da = ds[band]
                        crs = self._get_crs(ds)
                        da.rio.set_crs(crs, inplace=True)

                    da = self._apply_transforms(da, transforms)

                    # Reproject to same grid as overview.
                    da = da.rio.reproject(
                        dst_crs=overview_crs,
                        shape=overview_shape,
                        transform=overview_transform,
                        resampling=Resampling.average,
                        nodata=np.nan)

                    if overview is None:
                        overview = da
                    else:
                        # Elementwise maximum taking into account nans.
                        overview = xr.where(
                            np.logical_and(np.isfinite(overview), ~(overview > da)),
                            overview,
                            da)

                # Save overview as geotiff.
                print(f"Writing overview {overview_filename}", flush=True)
                overview.rio.to_raster(overview_filename)

                if 1:
                    import matplotlib.pyplot as plt
                    plt.pcolor(overview)
                    plt.show()

#    values = {}
#    overviews = {}
#    for level, resolution in levels.items():
#
#        print(f'Generating Raster Overview level {level} at {resolution} pixel width',
#              file=sys.stdout)
#
#        if resolution in values:
#            overviews[int(level)] = values[resolution]
#            continue
#
#        cvs = canvas_like(arr)
#        height = height_implied_by_aspect_ratio(resolution, cvs.x_range, cvs.y_range)
#        cvs.plot_height = height
#        cvs.plot_width = resolution
#        agg = (cvs.raster(arr, interpolate=interpolate)
#                  .compute()
#                  .chunk(512, 512)
#                  .persist())
#
#        overviews[int(level)] = agg
#        values[resolution] = agg
#
#    return overviews

    def _get_crs(self, ds):
        crs = ds.rio.crs
        if not crs:
            # Fallback for reading spatial_ref written in strange way.
            crs = ds.spatial_ref.spatial_ref
        return crs

    def _get_overview_directory(self):
        return os.path.join(self._base_dir, "overviews")

    def _get_overview_filename(self, band, level):
        return os.path.join(self._get_overview_directory(), f"{level}_{band}.tif")

    def full_extent(self):
        with self._lock:
            return self._total_bounds

    def load_bounds(self, xmin, ymin, xmax, ymax, band, transforms):
        # Load data for required bounds from disk and return xr.DataArray containing it.
        # Not storing the loaded data in this class, relying on caller freeing the returned object
        # when it has finished with it.  May need to implement a cacheing strategy here?

        # Need to test what happens with data that crosses longitude discontinuity.

        # Polygon of interest needs to be in files' CRS.
        polygon = Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])
        intersects = self._grid.intersects(polygon)  # pandas.Series of booleans.
        intersects = self._grid[intersects]  # geopandas.GeoDataFrame

        # If nothing intersects region of interest, send back empty DataArray.
        # Should be able to identify this earlier in the pipeline.
        if intersects.empty:
            return xr.DataArray()

        arrays = []
        crs = None
        with self._lock:
            for i, filename in enumerate(intersects.filename):
                with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                    da = ds[band]
                    if i == 0:
                        crs = self._get_crs(ds)
                        da.rio.set_crs(crs, inplace=True)
                    arrays.append(da)

        merged = xr.merge(arrays)
        # merged = merge_arrays(arrays)  # This gives mismatch between bounds and transform???

        merged = merged[band]
        merged.rio.set_crs(crs, inplace=True)

        with self._lock:
            merged = self._apply_transforms(merged, transforms)

        return merged

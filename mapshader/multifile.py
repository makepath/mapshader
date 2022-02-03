from affine import Affine
import geopandas as gpd
from glob import glob
import itertools
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

        self._lock = Lock()  # Limits reading of underlying data files to a single thread.
        self._bands = None
        self._overviews = None  # dict[tuple[int level, str band], xr.Dataset].  Loaded on demand.
        xmins = []
        xmaxs = []
        ymins = []
        ymaxs = []
        polygons = []

        # No thread locking required here as this is done by SharedMultiFile.get().
        for filename in filenames:
            with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                if not self._bands:
                    self._bands = [key for key in ds.data_vars.keys() if key != "spatial_ref"]

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

    def _create_single_band_overview(self, overview_shape, overview_transform, overview_crs, band,
                                     overview_filename, transforms, band_limits):
        # Open a block of files at a time for writing to overview DataArray.
        # Block size of one file initially.
        # Each file needs transforms applied before it can be resampled/reprojected.
        calc_limits = band_limits[0] is None or band_limits[1] is None
        overview = None
        for filename in self._grid.filename:
            with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                da = ds[band]
                crs = self._get_crs(ds)
                da.rio.set_crs(crs, inplace=True)

            da = self._apply_transforms(da, transforms)

            if calc_limits:
                min_ = da.min().item()
                max_ = da.max().item()
                # Update limits in place.
                band_limits[0] = min_ if band_limits[0] is None else min(band_limits[0], min_)
                band_limits[1] = max_ if band_limits[1] is None else max(band_limits[1], max_)

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

        # Remove attrs that can cause problem serializing xarrays.
        for key in ["grid_mapping"]:
            if key in overview.attrs:
                del overview.attrs[key]

        overview.attrs["limits"] = band_limits

        # Save overview as geotiff.
        print(f"Writing overview {overview_filename}", flush=True)
        try:
            overview.rio.to_raster(overview_filename)
        except:  # noqa: E722
            if os.path.isfile(overview_filename):
                os.remove(overview_filename)
            raise

    def _create_overviews(self, raster_overviews, transforms, force_recreate_overviews=False):
        overview_directory = self._get_overview_directory()
        if not os.path.isdir(overview_directory):
            os.makedirs(overview_directory)

        # Bounds of entire CRS.
        xmin, ymin, xmax, ymax = tile_def.get_tile_meters(0, 0, 0)

        levels_and_resolutions = raster_overviews["args"]["levels"]  # dict[int, int]
        tuple_keys = itertools.product(levels_and_resolutions.keys(), self._bands)
        self._overviews = dict.fromkeys(tuple_keys, None)
        band_limits = dict.fromkeys(self._bands, [None, None])

        for level, resolution in levels_and_resolutions.items():
            if not force_recreate_overviews:
                # If overviews exist for all bands at this level can abort early.
                if all([os.path.isfile(self._get_overview_filename(level, band))
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

            for band in self._bands:
                overview_filename = self._get_overview_filename(level, band)
                if not force_recreate_overviews and os.path.isfile(overview_filename):
                    print(f"Overview already exists {overview_filename}", flush=True)
                    continue

                self._create_single_band_overview(
                    overview_shape, overview_transform, overview_crs, band, overview_filename,
                    transforms, band_limits[band])

    def _get_crs(self, ds):
        crs = ds.rio.crs
        if not crs:
            # Fallback for reading spatial_ref written in strange way.
            crs = ds.spatial_ref.spatial_ref
        return crs

    def _get_overview_directory(self):
        return os.path.join(self._base_dir, "overviews")

    def _get_overview_filename(self, level, band):
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

    def load_overview(self, level, band):
        key = (level, band)
        if self._overviews is None or key not in self._overviews:
            return None

        with self._lock:
            ds = self._overviews[key]

            if ds is None:
                filename = self._get_overview_filename(level, band)
                print("Reading overview", filename)

                ds = rioxarray.open_rasterio(filename, chunks=dict(y=512, x=512))
                ds = ds.squeeze()
                self._overviews[key] = ds
            else:
                print(f"Cached overview {level} {band}")

        return ds

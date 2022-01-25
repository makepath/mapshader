import geopandas as gpd
from glob import glob
from pyproj import CRS, Transformer
import rioxarray  # noqa: F401
from shapely.geometry import Polygon
from threading import Lock
import xarray as xr

from .transforms import get_transform_by_name


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
    def get(cls, file_path, transforms):
        with cls._lock:
            shared = cls._lookup.get(file_path, None)
            if not shared:
                shared = MultiFileNetCDF(file_path, transforms)
                cls._lookup[file_path] = shared
        return shared


class MultiFileNetCDF:
    """
    Proxy for multiple netCDF files that provides a similar interface to
    xr.DataArray.

    This is an interim solution until we replace the objects returned by
    load_raster() and load_vector() with a considered class hierarchy.
    """
    def __init__(self, file_path, transforms):
        filenames = glob(file_path)
        if not filenames:
            raise RuntimeError(f"Unable to read any files from path {file_path}")

        self._lock = Lock()  # Limits reading of underlying data files to a single thread,
        xmins = []
        xmaxs = []
        ymins = []
        ymaxs = []
        polygons = []

        # No thread locking required here as this is done by SharedMultiFile.get().
        for filename in filenames:
            with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
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

    def _apply_transforms(self, da, transforms):
        for trans in transforms:
            transform_name = trans['name']
            func = get_transform_by_name(transform_name)
            args = trans.get('args', {})

            if 'overviews' in transform_name:
                pass
            else:
                da = func(da, **args)

        return da

    def _get_crs(self, ds):
        crs = ds.rio.crs
        if not crs:
            # Fallback for reading spatial_ref written in strange way.
            crs = ds.spatial_ref.spatial_ref
        return crs

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
        #merged = merge_arrays(arrays)  # This gives mismatch between bounds and transform???

        merged = merged[band]
        merged.rio.set_crs(crs, inplace=True)

        with self._lock:
            merged = self._apply_transforms(merged, transforms)

        return merged

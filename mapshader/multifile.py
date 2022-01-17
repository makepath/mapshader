import geopandas as gpd
from glob import glob
from pyproj import CRS, Transformer
import rioxarray  # noqa: F401
from shapely.geometry import Polygon
import xarray as xr


class SharedMultiFile:
    """
    Simple implementation of shared MultiFileNetCDF objects.
    """
    _lookup = {}

    @classmethod
    def get(cls, file_path):
        shared = cls._lookup.get(file_path, None)
        if not shared:
            cls._lookup[file_path] = shared = MultiFileNetCDF(file_path)
        return shared


class MultiFileNetCDF:
    """
    Proxy for multiple netCDF files that provides a similar interface to
    xr.DataArray.

    This is an interim solution until we replace the objects returned by
    load_raster() and load_vector() with a considered class hierarchy.
    """
    def __init__(self, file_path):
        filenames = glob(file_path)
        self._crs_file = None
        self._bands = None
        xmins = []
        xmaxs = []
        ymins = []
        ymaxs = []
        polygons = []

        for filename in filenames:
            with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                if self._crs_file is None:
                    self._crs_file = ds.attrs["crs"]
                    self._bands = list(ds.data_vars.keys())
                # Should really check CRS is the same across all files.

                # x, y limits determined from coords.
                # Could have been stored as attributes instead?
                xmin = ds.x.min().item()
                xmax = ds.x.max().item()
                ymin = ds.y.min().item()
                ymax = ds.y.max().item()

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

        # We don't yet have the CRS that the data needs to be in, so store
        # loaded CRS and will reproject later.

        if self._crs_file:
            self._grid.set_crs(self._crs_file, inplace=True)

        # Actually it is slightly larger than this by half a pixel in each direction
        self._total_bounds = self._grid.total_bounds  # [xmin, ymin, xmax, ymax]

        # Redirect calls like obj.rio.reproject() to obj.reproject().
        # This is an unpleasant temporary solution.
        self.rio = self

        self._crs_reproject = None

    def full_extent(self):
        return self._total_bounds

    def load_bounds(self, xmin, ymin, xmax, ymax, band):
        # Load data for required bounds from disk and return xr.DataArray containing it.
        # Not storing the loaded data in this class, relying on caller freeing the returned object
        # when it has finished with it.  May need to implement a cacheing strategy here?

        # Need to test what happens with data that crosses longitude discontinuity.

        # Polygon of interest needs to be in files' CRS.
        if self._crs_reproject:
            transformer = Transformer.from_crs(self._crs_reproject, self._crs_file)
            xmin, ymin = transformer.transform(xmin, ymin)
            xmax, ymax = transformer.transform(xmax, ymax)
            if ymax < -179.999999 and self._crs_file == CRS("EPSG:4326"):
                # Botch to deal with dodgy reprojection.
                ymax = 180.0

        polygon = Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])
        intersects = self._grid.intersects(polygon)  # pandas.Series of booleans.
        intersects = self._grid[intersects]  # geopandas.GeoDataFrame

        arrays = []
        for i, filename in enumerate(intersects.filename):
            with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                arr = ds[band]
                if i == 0:
                    arr.rio.write_crs(self._crs_file, inplace=True)  # Only the first needs CRS set.
                arrays.append(arr)

        # If nothing intersects region of interest, send back empty DataArray.
        # Should be able to identify this earlier in the pipeline.
        if not arrays:
            return xr.DataArray()

        merged = xr.merge(arrays)
        # merged = merge_arrays(arrays)  # This gives mismatch between bounds and transform???

        merged = merged[band]

        if self._crs_reproject:
            merged = merged.rio.reproject(self._crs_reproject)

        return merged

    def reproject(self, proj_str):
        if self._crs_reproject:
            # Already reprojected so do not repeat.
            return self

        self._crs_reproject = proj_str

        # Reproject the total bounds.
        # Assuming x and y transforms are independent.
        # This will not be necessary when required CRS is passed to constructor.
        transformer = Transformer.from_crs(self._crs_file, self._crs_reproject)
        xmin, ymin, xmax, ymax = self._total_bounds
        xmin, ymin = transformer.transform(xmin, ymin)
        xmax, ymax = transformer.transform(xmax, ymax)
        self._total_bounds = (xmin, ymin, xmax, ymax)

        # Coordinates from individual netcdf files will be reprojected each time they are loaded.

        return self

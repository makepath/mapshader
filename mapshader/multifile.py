import geopandas as gpd
from glob import glob
from pyproj import CRS, Transformer
import rioxarray  # noqa: F401
from shapely.geometry import Polygon
import xarray as xr

class MultiFileNetCDF:
    """
    Proxy for multiple netCDF files that provides a similar interface to
    xr.DataArray.

    This is an interim solution until we replace the objects returned by
    load_raster() and load_vector() with a considered class hierarchy.
    """
    def __init__(self, file_path):
        print("==> MultiFileNetCDF.__init__ XXX", file_path, flush=True)

        filenames = glob(file_path)
        self._crs_file = None
        xmins = []
        xmaxs = []
        ymins = []
        ymaxs = []
        polygons = []

        for i, filename in enumerate(filenames):
            with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                if self._crs_file is None:
                    self._crs_file = ds.attrs["crs"]
                # Should really check CRS is the same across all files.

                # x, y limits determined from coords.
                # Could have been stored as attributes instead?
                xmin = ds.x.min().item()
                xmax = ds.x.max().item()
                ymin = ds.y.min().item()
                ymax = ds.y.max().item()
                #print("==> Bounds on import", filename, ds.rio.bounds(), flush=True)

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
        #print("==> Total bounds", self._total_bounds, flush=True)

        # Redirect calls like obj.rio.reproject() to obj.reproject().
        # This is an unpleasant temporary solution.
        self.rio = self

        self._crs_reproject = None

    def full_extent(self):
        return self._total_bounds

    def load(self, xmin, ymin, xmax, ymax):
        # Load data for required bounds from disk and return xr.DataArray containing it.
        # Not storing the loaded data in this class, relying on caller freeing the returned object
        # when it has finished with it.  May need to implement a cacheing strategy here?
        print("==> LOAD", xmin, ymin, xmax, ymax, flush=True)
        print("==>      total_bounds", self._total_bounds, flush=True)

        band_wanted = "green"  # This needs to be selected by user.

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
        #print("POLYGON", polygon, flush=True)
        intersects = self._grid.intersects(polygon)  # pandas.Series of booleans.
        #print("INTERSECTS", intersects, flush=True)
        intersects = self._grid[intersects]  # geopandas.GeoDataFrame
        #print(intersects)

        print("==> NUMBER OF FILES TO LOAD", len(intersects), flush=True)

        arrays = []
        for i, filename in enumerate(intersects.filename):
            with xr.open_dataset(filename, chunks=dict(y=512, x=512)) as ds:
                arr = ds[band_wanted]
                if i == 0:
                    arr.rio.write_crs(self._crs_file, inplace=True)  # Only the first needs CRS set.
                arrays.append(arr)

        # If nothing intersects region of interest, send back empty DataArray.
        # Should be able to identify this earlier in the pipeline.
        if not arrays:
            print("EARLY EXIT", flush=True)
            return xr.DataArray()

        merged = xr.merge(arrays)
        # merged = merge_arrays(arrays)  # This gives mismatch between bounds and transform???

        merged = merged[band_wanted]

        if self._crs_reproject:
            merged = merged.rio.reproject(self._crs_reproject)

        return merged

    def reproject(self, proj_str):
        if self._crs_reproject:
            raise RuntimeError("Cannot call reproject more than once")

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

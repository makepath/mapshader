from affine import Affine

import rioxarray
import xarray as xr
import datashader as ds
import geopandas as gpd

def load_raster(filepath: str):
    da = xr.open_rasterio(filepath)
    da = da.squeeze().drop("band")
    da.data = ds.utils.orient_array(da)
    # move pixel centers (do we need this?)
    # transform = Affine.from_gdal(*da.attrs['transform'])
    # nx, ny = da.sizes['x'], da.sizes['y']
    # x, y = np.meshgrid(np.arange(nx)+0.5, np.arange(ny)+0.5) * transform
    return da

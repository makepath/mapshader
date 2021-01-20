import rioxarray
import xarray as xr
import datashader as ds
import geopandas as gpd


def load_raster(filepath: str):
    da = xr.open_rasterio(filepath)
    #res = ds.utils.calc_res(da)
    #da.data = ds.utils.orient_array(da, res=(abs(res[0]), -1 * abs(res[1])))
    # move pixel centers (do we need this?)
    # transform = Affine.from_gdal(*da.attrs['transform'])
    # nx, ny = da.sizes['x'], da.sizes['y']
    # x, y = np.meshgrid(np.arange(nx)+0.5, np.arange(ny)+0.5) * transform
    return da


def load_vector(filepath: str):
    return gpd.read_file(filepath)

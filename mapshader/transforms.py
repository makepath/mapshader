import rioxarray
import xarray as xr
import datashader as ds
import geopandas as gpd

wb_proj_str = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs'

wgs84_proj_str = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'

def reproject_raster(arr:xr.DataArray, epsg=3857):
    if epsg == 3857:
        return arr.rio.reproject("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    else:
        raise ValueError(f'Raster Projection Error: Invalid EPSG {epsg}')
    pass


def reproject_vector(gdf:gpd.GeoDataFrame, epsg=3857):
    return gdf.to_crs(epsg=epsg)


def load_raster(filepath: str):
    from affine import Affine
    da = xr.open_rasterio(filepath)
    da = da.squeeze().drop("band")
    da.data = ds.utils.orient_array(da)
    return da
    # move pixel centers (do we need this?)
    # transform = Affine.from_gdal(*da.attrs['transform'])
    # nx, ny = da.sizes['x'], da.sizes['y']
    # x, y = np.meshgrid(np.arange(nx)+0.5, np.arange(ny)+0.5) * transform

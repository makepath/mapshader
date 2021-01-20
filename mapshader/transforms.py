import rioxarray  # NOQA
import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd

wb_proj_str = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs'

wgs84_proj_str = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'

def reproject_raster(arr: xr.DataArray, epsg=3857):
    if epsg == 3857:
        return arr.rio.reproject(wb_proj_str)
    else:
        raise ValueError(f'Raster Projection Error: Invalid EPSG {epsg}')
    pass


def reproject_vector(gdf: gpd.GeoDataFrame, epsg=3857):
    return gdf.to_crs(epsg=epsg)


def line_geoseries_to_datashader_line(series: gpd.GeoSeries):
    # TODO: This is slow! Make this faster!
    xs = []
    ys = []
    for s in series.values:
        try:
            coords = s.coords.xy
            xs += coords[0].tolist()
            ys += coords[1].tolist()

            xs.append(np.nan)
            ys.append(np.nan)
        except:
            continue

    return pd.DataFrame(dict(x=xs, y=ys))

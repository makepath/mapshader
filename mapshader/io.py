import rioxarray
import xarray as xr
import datashader as ds
import geopandas as gpd
import numpy as np
from affine import Affine

from os.path import expanduser


def load_raster(file_path, xmin=None, ymin=None,
                xmax=None, ymax=None, chunks=None,
                layername='data'):

    if file_path.endswith('.tif'):

        arr = xr.open_rasterio(expanduser(file_path),
                               chunks={'y': 512, 'x': 512})

        if hasattr(arr, 'nodatavals'):

            if np.issubdtype(arr.data.dtype, np.integer):
                arr.data = arr.data.astype('f8')

            for val in arr.nodatavals:
                arr.data[arr.data == val] = np.nan

        arr.name = file_path

    elif file_path.endswith('.nc'):
        # TODO: add chunk parameter to config
        arr = xr.open_dataset(file_path, chunks={'x': 512, 'y': 512})[layername]
        arr['name'] = file_path

    else:
        raise TypeError(f"Unable to load raster {file_path}")

    return arr


def load_vector(filepath: str):
    return gpd.read_file(filepath)


def has_postgis():

    from sqlalchemy.exc import OperationalError

    try:
        conn = get_postgis_connection()
        conn.connect()
        return True
    except OperationalError:
        return False


def doesnt_have_postgis():
    return not has_postgis()


def get_postgis_connection():
    from sqlalchemy import create_engine

    database = environ.get('PGDATABASE', 'template_postgis')
    host = environ.get('PGHOST', '127.0.0.1')
    port = environ.get('PGPORT', '5432')
    user = environ.get('PGUSER', 'postgres')
    password = environ.get('PGPASSWORD', '')

    return create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")


def get_layer_from_postgis(layername, rows=None, where='1=1', geom_col='geometry'):

    from sqlalchemy import text as normalize_sql

    conn = get_postgis_connection()

    sql = f'SELECT * FROM {layername}'

    if where:
        sql += f' WHERE {normalize_sql(where)}'

    if rows:
        sql += f' LIMIT {rows}'

    sql += ';'

    df = gpd.GeoDataFrame.from_postgis(sql,
                                       conn,
                                       geom_col=geom_col)
    return df

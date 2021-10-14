from mapshader.core import render_map, to_raster
from mapshader.sources import MapSource



def get_source_single_tif():
    #filepath = '/home/data/copernicus_dem_90/Copernicus_DSM_COG_30_N48_00_E018_00_DEM.tif'
    filepath = '/home/data/etopo/ETOPO1_Ice_c_geotiff.tif'

    # construct transforms
    squeeze_transform = dict(name='squeeze', args=dict(dim='band'))
    cast_transform = dict(name='cast', args=dict(dtype='float64'))
    reproject_transform = dict(name='reproject_raster', args=dict(epsg=3857))
    transforms = [squeeze_transform,
                  cast_transform,
                  reproject_transform]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'Single raster tile'
    source_obj['key'] = 'a'
    source_obj['text'] = 'a'
    source_obj['description'] = 'Single raster tile'
    source_obj['filepath'] = filepath
    source_obj['geometry_type'] = 'raster'
    source_obj['shade_how'] = 'linear'
    source_obj['span'] = 'min/max'
    source_obj['dynspread'] = None
    source_obj['raster_padding'] = 0
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'geometry'
    source_obj['yfield'] = 'geometry'
    #source_obj['zfield'] = 'BoroCode'
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile']

    return source_obj


def get_source_gtopo30():
    filepath = '/home/data/gtopo30/gt30w*.tif'

    # construct transforms
    squeeze_transform = dict(name='squeeze', args=dict(dim='band'))
    cast_transform = dict(name='cast', args=dict(dtype='float64'))
    reproject_transform = dict(name='reproject_raster', args=dict(epsg=3857))
    transforms = [squeeze_transform,
                  #cast_transform,
                  reproject_transform]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'gtopo30'
    source_obj['key'] = 'gtopo30'
    source_obj['text'] = 'gtopo30'
    source_obj['description'] = 'gtopo30'
    source_obj['filepath'] = filepath
    source_obj['geometry_type'] = 'raster'
    source_obj['shade_how'] = 'linear'
    source_obj['span'] = 'min/max'
    source_obj['dynspread'] = None
    source_obj['raster_padding'] = 0
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'geometry'
    source_obj['yfield'] = 'geometry'
    source_obj['zfield'] = 'z'
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile']

    return source_obj


def get_source_multi_tif():
    filepath = '/home/data/copernicus_dem_30/grand_canyon/Copernicus_DSM_COG_10_*_DEM.tif'

    # construct transforms
    squeeze_transform = dict(name='squeeze', args=dict(dim='band'))
    reproject_transform = dict(name='reproject_raster', args=dict(epsg=3857))
    transforms = [
        squeeze_transform,
        reproject_transform,
    ]

    # construct value obj
    source_obj = dict()
    source_obj['name'] = 'Grand Canyon (Copernicus 30 m)'
    source_obj['key'] = 'grand_canyon'
    source_obj['text'] = 'grand_canyon'
    source_obj['description'] = 'Grand Canyon (Copernicus 30 m)'
    source_obj['filepath'] = filepath
    source_obj['geometry_type'] = 'raster'
    source_obj['shade_how'] = 'linear'
    source_obj['span'] = 'min/max'
    source_obj['dynspread'] = None
    source_obj['raster_padding'] = 0
    source_obj['raster_interpolate'] = 'linear'
    source_obj['xfield'] = 'geometry'
    source_obj['yfield'] = 'geometry'
    source_obj['transforms'] = transforms
    source_obj['service_types'] = ['tile']

    return source_obj



def main():
    source_obj = get_source_multi_tif()

    source = MapSource.from_obj(source_obj).load()

    if 1:
        #import pdb
        #pdb.set_trace()
        arr = to_raster(source, width=100)
        #print("AAAAAA raster")
        print(arr)
    else:
        arr = render_map(source, width=100)
        #print("AAAAA render_map")
        print(arr)

main()

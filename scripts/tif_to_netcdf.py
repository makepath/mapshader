import xarray as xr

from mapshader.transforms import squeeze
from mapshader.transforms import cast
from mapshader.transforms import orient_array
from mapshader.transforms import flip_coords
from mapshader.transforms import reproject_raster


def run(input_file, output_file, chunks=(512, 512),
        name='data', scale_factor=0.1, fill_value=-9999):

    arr = xr.open_rasterio(input_file)
    arr = squeeze(arr, 'band')
    arr = cast(arr, dtype='float64')
    arr = orient_array(arr)
    arr = flip_coords(arr, dim='y')  # do we need this?
    arr = reproject_raster(arr, epsg=3857)

    dataset = xr.Dataset({name: (['y', 'x'], arr.chunk(chunks))},
                         coords={'x': arr.coords['x'],
                                 'y': arr.coords['y']})
    dataset.attrs = dict(name=name)
    dataset.to_netcdf(output_file, encoding={'data': {'dtype': 'int16',
                                                      'scale_factor': 0.1,
                                                      '_FillValue': -9999}})


if __name__ == '__main__':

    import sys
    from argparse import ArgumentParser
    from os import path

    parser = ArgumentParser()
    parser.add_argument('-i')
    parser.add_argument('-o')
    parsed = parser.parse_args()

    input_file = path.abspath(path.expanduser(parsed.i))
    print(f'Converting {input_file} from TIFF to NetCDF File', file=sys.stdout)

    if not parsed.o:
        output_file = input_file.replace('.tif', '.nc')
    else:
        output_file = path.abspath(path.expanduser(parsed.o))

    run(input_file, output_file)
    print(f'Conversion Complete: {output_file}', file=sys.stdout)

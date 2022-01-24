import filecmp
from os import path
import shutil

from click import BadParameter
from click.testing import CliRunner
from rasterio.errors import RasterioIOError

from mapshader.commands.tif_to_netcdf import tif_to_netcdf
from mapshader.tests.data import FIXTURES_DIR


def test_invalid_y_dimension_name():
    runner = CliRunner()
    input_file = path.join(FIXTURES_DIR, 'shade.tif')

    result = runner.invoke(
        tif_to_netcdf, [input_file, '--x', '1'], standalone_mode=False
    )
    assert isinstance(result.exception, BadParameter)


def test_invalid_x_dimension_name():
    runner = CliRunner()
    input_file = path.join(FIXTURES_DIR, 'shade.tif')

    result = runner.invoke(
        tif_to_netcdf, [input_file, '--x', '1'], standalone_mode=False
    )
    assert isinstance(result.exception, BadParameter)


def test_invalid_input_file():
    runner = CliRunner()
    input_file = path.join(FIXTURES_DIR, 'counties_3857.gpkg')

    result = runner.invoke(tif_to_netcdf, [input_file], standalone_mode=False)
    assert isinstance(result.exception, RasterioIOError)


def test_invalid_input_file_path():
    runner = CliRunner()
    input_file = path.join(FIXTURES_DIR, 'nd.tif')

    result = runner.invoke(tif_to_netcdf, [input_file], standalone_mode=False)
    assert isinstance(result.exception, RasterioIOError)


def test_invalid_dtype_cast():
    runner = CliRunner()
    input_file = path.join(FIXTURES_DIR, 'shade.tif')

    result = runner.invoke(
        tif_to_netcdf, [input_file, '--cast', 'int2'], standalone_mode=False
    )
    assert isinstance(result.exception, TypeError)


def test_invalid_reprojection():
    runner = CliRunner()
    input_file = path.join(FIXTURES_DIR, 'shade.tif')

    result = runner.invoke(
        tif_to_netcdf, [input_file, '--reproject', '123'], standalone_mode=False
    )
    assert isinstance(result.exception, ValueError)


def test_valid_conversion(tmpdir):
    runner = CliRunner()

    input_filename = 'shade.tif'
    output_filename = 'shade.nc'

    input_filepath = tmpdir.join(input_filename).strpath
    output_filepath = tmpdir.join(output_filename).strpath
    expected_output_filepath = path.join(FIXTURES_DIR, output_filename)

    shutil.copy2(path.join(FIXTURES_DIR, input_filename), input_filepath)
    runner.invoke(tif_to_netcdf, [input_filepath], standalone_mode=False)

    # xarray.to_netcdf can produce NETCDF3 or 4 files depending on availability of scipy.io and
    # python netCDF4 libraries.  Need to check both possibilities.
    if not filecmp.cmp(output_filepath, expected_output_filepath):
        # Files differ, but may just be different netcdf version so check contents.
        from numpy.testing import assert_array_almost_equal
        import xarray as xr

        a = xr.open_dataset(output_filepath)
        b = xr.open_dataset(expected_output_filepath)
        assert a.attrs == b.attrs
        assert a.spatial_ref == b.spatial_ref
        assert_array_almost_equal(a.coords["x"], b.coords["x"])
        assert_array_almost_equal(a.coords["y"], b.coords["y"])
        assert_array_almost_equal(a.data, b.data)

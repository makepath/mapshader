from glob import glob
import numpy as np
import os
import pytest
import rioxarray  # noqa: F401
import subprocess
import xarray as xr

from .common import check_and_create_large_geotiff


def create_tiles():
    check_and_create_large_geotiff()

    top_directory = os.path.join("examples", "large_vrt")
    tile_directory = os.path.join(top_directory, "tiles")
    vrt_file = os.path.join(top_directory, "large_vrt.vrt")
    if not os.path.isfile(vrt_file):
        if not os.path.isdir(tile_directory):
            print(f"Creating directory {tile_directory}")
            os.makedirs(tile_directory)

        # Split single large GeoTIFF into multiple tiles.
        tiff_file = os.path.join("examples", "large_geotiff", "large_geotiff.tif")
        tile_size = 8192
        cmd = ["gdal_retile.py", "-ps", str(tile_size), str(tile_size), "-targetDir",
               tile_directory, tiff_file]
        subprocess.run(cmd)

        # Create VRT for tile set.
        tile_names = glob(os.path.join(tile_directory, "*.tif"))
        tile_names.sort()
        cmd = ["gdalbuildvrt", vrt_file] + tile_names
        subprocess.run(cmd)


@pytest.mark.large
def test_large_vrt_create():
    create_tiles()


@pytest.mark.large
def test_large_vrt_create_overviews():
    create_tiles()

    yaml_file = os.path.join("examples", "large_vrt.yaml")
    cmd = ["mapshader", "build-raster-overviews", yaml_file]
    subprocess.run(cmd)


@pytest.mark.large
@pytest.mark.parametrize("z, shape", [
    [0, (55, 256)],
    [1, (228, 512)],
    [2, (457, 1024)],
    [3, (911, 2048)],
    [4, (1819, 4094)],
    [5, (3636, 8186)],
    [6, (7269, 16371)],
])
def test_large_vrt_overview_files(z, shape):
    directory = os.path.join("examples", "large_vrt", "overviews")
    filename = os.path.join(directory, f"{z}_band_data.nc")
    assert os.path.isfile(filename)

    ds = xr.open_dataset(filename, chunks=dict(y=2048, x=2048))
    da = ds["band_data"]
    assert da.dtype == np.float32
    assert da.shape == shape

    assert 0.0 <= da.min().compute().item() < 1.0
    assert 0.0 < da.max().compute().item() <= 1.0

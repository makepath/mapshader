import numpy as np
import os
import pytest
import rioxarray  # noqa: F401
import subprocess
import xarray as xr

from .common import check_and_create_large_geotiff


@pytest.mark.large
def test_large_geotiff_create():
    check_and_create_large_geotiff()


@pytest.mark.large
def test_large_geotiff_create_overviews():
    check_and_create_large_geotiff()

    yaml_file = os.path.join("examples", "large_geotiff.yaml")
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
def test_large_geotiff_overview_files(z, shape):
    directory = os.path.join("examples", "large_geotiff", "overviews")
    filename = os.path.join(directory, f"{z}_band_data.nc")
    assert os.path.isfile(filename)

    ds = xr.open_dataset(filename, chunks=dict(y=2048, x=2048))
    da = ds["band_data"]
    assert da.dtype == np.float32
    assert da.shape == shape

    assert 0.0 <= da.min().compute().item() < 1.0
    assert 0.0 < da.max().compute().item() <= 1.0

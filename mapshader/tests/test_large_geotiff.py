import math
import numpy as np
import os
import pytest
import rioxarray  # noqa: F401
import subprocess
import xarray as xr


def check_and_create_large_geotiff():
    directory = os.path.join("examples", "large_geotiff")
    filename = "large_geotiff.tif"
    full_filename = os.path.join(directory, filename)

    if os.path.isfile(full_filename):
        # File already exists, so abort.
        return

    if not os.path.isdir(directory):
        print(f"Creating directory {directory}")
        os.makedirs(directory)

    crs = "EPSG:3857"
    x_limits = [-2e7, 2e7]
    y_limits = [0.2e7, 1e7]

    nx = 115000  # 10 GB

    dx = (x_limits[1] - x_limits[0]) / (nx-1)
    ny = math.ceil((y_limits[1] - y_limits[0]) / dx) + 1

    # Fix y_limits to work with ny
    y_limits[1] = y_limits[0] + (ny-1)*dx

    x = np.linspace(x_limits[0], x_limits[1], nx, dtype=np.float32)
    y = np.linspace(y_limits[0], y_limits[1], ny, dtype=np.float32)

    rng = np.random.default_rng(92741)
    data = rng.random((ny, nx), dtype=np.float32)

    dims = ["y", "x"]
    ds = xr.Dataset(
        data_vars=dict(band=(dims, data)),
        coords=dict(y=y, x=x),
        attrs=dict(description="large geotiff data", crs=crs),
    )

    ds.rio.to_raster(full_filename)

    file_size_gb = os.path.getsize(full_filename) / (1024**3)
    print(f"shape {ds['band'].shape}, file size {file_size_gb:.3f} GB")


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

    ds = xr.open_dataset(filename, chunks=dict(y=512, x=512))
    da = ds["band_data"]
    assert da.dtype == np.float32
    assert da.shape == shape

    assert da.min().compute().item() >= 0.0
    assert da.max().compute().item() <= 1.0

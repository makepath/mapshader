from glob import glob
import numpy as np
import os
import pytest
import rioxarray  # noqa: F401
import subprocess
import xarray as xr


def check_and_create_multi_netcdf():
    directory = os.path.join("examples", "multi_netcdf")
    if not os.path.isdir(directory):
        print(f"Creating directory {directory}")
        os.makedirs(directory)

    crs = "EPSG:4326"

    # Number of files.
    nx_tile = 50
    ny_tile = 20

    filenames = glob(os.path.join(directory, "multi_*.nc"))
    if len(filenames) == nx_tile*ny_tile:
        # If the target directory contains the correct number of netcdf files,
        # assume it is correct and do not regenerate it.
        return

    # Grid points per tile.
    ny, nx = 50, 100
    lon_start = -90.0
    lat_start = -40.0
    scale = 1.5  # Degrees per tile.
    dx = scale / nx
    dy = scale / ny

    rng = np.random.default_rng(92741)
    dims = ["y", "x"]

    for j in range(ny_tile):
        for i in range(nx_tile):
            x = np.linspace(lon_start + i*scale + dx/2, lon_start + (i+1)*scale - dx/2, nx)
            y = np.linspace(lat_start + j*scale + dy/2, lat_start + (j+1)*scale - dy/2, ny)
            y = y[::-1]
            filename = f"multi_{j:03}_{i:03}.nc"
            full_filename = os.path.join(directory, filename)

            # 2 bands.
            constant = rng.random(size=(ny, nx), dtype=np.float32)
            increasing = rng.random(size=(ny, nx), dtype=np.float32) + j

            ds = xr.Dataset(
                data_vars=dict(
                    constant=(dims, constant),
                    increasing=(dims, increasing),
                ),
                coords=dict(y=y, x=x),
                attrs=dict(description="Test multi netcdf data", crs=crs),
            )

            ds.to_netcdf(full_filename)
            print(f"Written file {full_filename}")


@pytest.mark.large
def test_multi_netcdf_create_overviews():
    check_and_create_multi_netcdf()

    yaml_file = os.path.join("examples", "multi_netcdf.yaml")
    cmd = ["mapshader", "build-raster-overviews", yaml_file]
    subprocess.run(cmd)


@pytest.mark.large
@pytest.mark.parametrize("z, shape", [
    [0, (28, 57)],
    [1, (80, 145)],
    [2, (158, 288)],
    [3, (312, 572)],
    [4, (619, 1141)],
    [5, (1235, 2278)],
    [6, (2467, 4554)],
])
@pytest.mark.parametrize("band", ("constant", "increasing"))
def test_multi_netcdf_overview_files(band, z, shape):
    directory = os.path.join("examples", "multi_netcdf", "overviews")
    filename = os.path.join(directory, f"{z}_{band}.nc")
    assert os.path.isfile(filename)

    ds = xr.open_dataset(filename, chunks=dict(y=512, x=512))
    da = ds[band]
    assert da.dtype == np.float32
    assert da.shape == shape

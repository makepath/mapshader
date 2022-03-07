import math
import numpy as np
import os
import pytest
import rioxarray
import subprocess
import xarray as xr
import yaml

from mapshader.sources import MapSource
from mapshader.core import render_map


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

    #nx = 10000  # 0.075 GB
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
def test_large_geotiff_read_overviews():
    directory = os.path.join("examples", "large_geotiff", "overviews")
    for overview in range(7):
        filename = os.path.join(directory, f"{overview}_band_data.nc")
        if not os.path.isfile(filename):
            pytest.xfail("Overviews do not exist")

    yaml_file = os.path.join("examples", "large_geotiff.yaml")
    with open(yaml_file, 'r') as f:
        content = f.read()
        config_obj = yaml.safe_load(content)
        source_obj = config_obj['sources'][0]

    source = MapSource.from_obj(source_obj)
    source = source.load()

    for z in range(8):
        x = 2**(z-1) - 1
        if x < 0:
            x = 0
        y = 0 if z < 2 else round(2**(z-1.65))

        img = render_map(source, x=x, y=y, z=z, height=256, width=256)
        one_color_component = img & 0xff
        min_, max_ = one_color_component.min(), one_color_component.max()
        assert max_ > 0
        assert min_ < max_

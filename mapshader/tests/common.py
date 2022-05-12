import math
import numpy as np
import os
import rioxarray  # noqa: F401
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

    nx = 36200  # 1 GB

    dx = (x_limits[1] - x_limits[0]) / (nx-1)
    ny = math.ceil((y_limits[1] - y_limits[0]) / dx) + 1

    # Fix y_limits to work with ny
    y_limits[1] = y_limits[0] + (ny-1)*dx

    x = np.linspace(x_limits[0], x_limits[1], nx, dtype=np.float32)
    y = np.linspace(y_limits[1], y_limits[0], ny, dtype=np.float32)

    x2 = np.expand_dims(x, axis=0)
    y2 = np.expand_dims(y, axis=1)
    rng = np.random.default_rng(92741)
    data = 0.4 + 0.4*np.sin(x2 / 3e5)*np.cos(y2 / 3e5) + 0.2*rng.random((ny, nx), dtype=np.float32)

    dims = ["y", "x"]
    ds = xr.Dataset(
        data_vars=dict(band=(dims, data)),
        coords=dict(y=y, x=x),
        attrs=dict(description="large geotiff data", crs=crs),
    )

    ds.rio.to_raster(full_filename)

    file_size_gb = os.path.getsize(full_filename) / (1024**3)
    print(f"shape {ds['band'].shape}, file size {file_size_gb:.3f} GB")

# Create multiple netcdf files that are adjacent tiles containing the same
# multiple variables.
# Each tile is 1x1 degree for simplicity, EPSG 4326.

import numpy as np
import rioxarray
import xarray as xr


lat_limits = (0, 3)  # Integer min and max latitude
lon_limits = (0, 4)  # Integer min and max longitude
ny, nx = 4, 5        # Grid points per tile.


dx = 1.0 / nx
dy = 1.0 / ny

rng = np.random.default_rng(92741)

red_min = np.nan
red_max = np.nan
green_min = np.nan
green_max = np.nan
blue_min = np.nan
blue_max = np.nan

for lat in range(lat_limits[0], lat_limits[1]):
    for lon in range(lon_limits[0], lon_limits[1]):
        # Randomly remove some tiles.
        if rng.random(1)[0] > 0.8:
            continue

        x = np.linspace(lon + dx/2, lon + 1 - dx/2, nx)
        y = np.linspace(lat + dy/2, lat + 1 - dy/2, ny)
        filename = f"dummy_{lon}_{lat}.nc"

        red = rng.random(size=(ny, nx), dtype=np.float32)
        green = rng.random(size=(ny, nx), dtype=np.float32) + lon
        blue = rng.random(size=(ny, nx), dtype=np.float32) + lat

        dims = ["y", "x"]
        ds = xr.Dataset(
            data_vars=dict(
                red=(dims, red),
                green=(dims, green),
                blue=(dims, blue),
            ),
            coords=dict(y=y, x=x),            
            attrs=dict(
                description="dummy data",
                crs="epsg:4326",
            ),
        )

        ds.to_netcdf(filename)
        print(f"Written file {filename}", ds.rio.bounds(), x.min(), y.min(), x.max(), y.max())
        
        red_min = np.nanmin((red_min, red.min()))
        red_max = np.nanmax((red_max, red.max()))
        green_min = np.nanmin((green_min, green.min()))
        green_max = np.nanmax((green_max, green.max()))
        blue_min = np.nanmin((blue_min, blue.min()))
        blue_max = np.nanmax((blue_max, blue.max()))

print(f"red limits: {red_min} {red_max}")
print(f"green limits: {green_min} {green_max}")
print(f"blue limits: {blue_min} {blue_max}")

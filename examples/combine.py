import geopandas as gpd
from glob import glob
from rioxarray.merge import merge_arrays, merge_datasets
from shapely.geometry import Polygon
import xarray as xr


file_pattern = "dummy_*.nc"


# def combine_netcdfs

crs = None
filenames = []
xmins = []
xmaxs = []
ymins = []
ymaxs = []
polygons = []

for filename in glob(file_pattern):
    with xr.open_dataset(filename, chunks=dict(y=250, x=250)) as ds:
        attrs = ds.attrs

        if crs is None:
            crs = attrs["crs"]
        elif attrs["crs"] != crs:
            raise RuntimeError(f"NetCDF files do not all have the same CRS {crs}")

        # x, y limits determined from coords.
        # Could have been stored as attributes instead?
        xmin = ds.x.min().item()
        xmax = ds.x.max().item()
        ymin = ds.y.min().item()
        ymax = ds.y.max().item()

        print("Bounds on import", ds.rio.bounds())

    filenames.append(filename)
    xmins.append(xmin)
    xmaxs.append(xmax)
    ymins.append(ymin)
    ymaxs.append(ymax)

    polygons.append(Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]))

# Create GeoDataFrame containing grid information.
gdf = gpd.GeoDataFrame(dict(
    geometry=polygons,
    filename=filenames,
    xmin=xmins,
    xmax=xmaxs,
    ymin=ymins,
    ymax=ymaxs,
))

if crs:
    gdf.set_crs(crs, inplace=True)

print(gdf)
print("Total bounds", gdf.total_bounds)

if 0:
    import matplotlib.pyplot as plt
    gdf.plot("xmin")
    plt.show()

# Polygon of interest
xmin = 1.2; xmax = 2.5; ymin = 0.5; ymax = 3.2
#xmin = -1; xmax = 4; ymin = -1; ymax = 4
polygon = Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])

if 0:
    # This is too much, it is creating and returning new clipped polygons.
    intersection = gdf.intersection(polygon)  # Returns GeoSeries of polygons, some of which are empty
    print(type(intersection), intersection)
    print(intersection.total_bounds)

intersects = gdf.intersects(polygon)  # Returns pd.Series of booleans.
print(type(intersects), intersects)

if 1:
    # Need to identify which netcdf files to open, then combine them...
    intersect_gdf = gdf[intersects]
    #print(intersect_gdf.filename)

    band_wanted = "green"

    #datasets = []
    arrays = []
    crs = None
    for i, filename in enumerate(intersect_gdf.filename):
        #print("AAA", filename)
        with xr.open_dataset(filename, chunks=dict(y=250, x=250)) as ds:
            arr = ds[band_wanted]
            if i == 0:
                arr.rio.write_crs(ds.crs, inplace=True)  # Only the first needs CRS set.
            arrays.append(arr)
            #datasets.append(ds)
        #if len(arrays) == 1:
        #    break

    print("Files loaded", len(arrays))
    for i, a in enumerate(arrays):
        print("array", i)
        print("  bounds", a.rio.bounds())
        print("  crs", a.rio.crs)
        print("  transform", a.rio.transform())

    if 1:
        merged = xr.merge(arrays)  # This works.
    else:
        merged = merge_arrays(arrays)  # This gives mismatch between bounds and transform.

    print(merged)
    print(merged.rio.bounds())
    print(merged.rio.crs)
    print(merged.rio.transform())

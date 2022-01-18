from mapshader.sources import MapSource
from mapshader.core import render_map
import PIL
import yaml


yaml_file = "example_multiband/multiband_netcdf.yaml"

with open(yaml_file, 'r') as f:
    content = f.read()
    config_obj = yaml.safe_load(content)
    source_objs = config_obj['sources']

sources = []
for source_obj in source_objs:
    sources.append(MapSource.from_obj(source_obj))

print(sources)


# Want tile containing slightly positive lat and lon
def run(x, y, z, index, j):
    print("XYZ", x, y, z)

    img = render_map(source, x=x, y=y, z=z, height=256, width=256)  # xarray Image 8x8

    bytes = img.to_bytesio()
    pillow_img = PIL.Image.open(bytes)
    pillow_img.save(f"out_{j}_{index}.png", format="png")

def xyz_contains_data(z):
    ntiles = 2**z  # In both x and y directions.
    x = ntiles // 2
    y = max(x-1, 0)
    return x, y, z


for j in range(3):
    source = sources[j].load()

    i = 0
    for z in range(0, 3):
        x, y, z = xyz_contains_data(z)
        run(x, y, z, i, j)
        i += 1

    # run(x-1, y, z, i, j)

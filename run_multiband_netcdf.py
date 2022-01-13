from mapshader.sources import MapSource
from mapshader.core import render_map
import PIL
import yaml


yaml_file = "multiband_netcdf.yaml"


with open(yaml_file, 'r') as f:
    content = f.read()
    config_obj = yaml.safe_load(content)
    source_obj = config_obj['sources'][0]

s = MapSource.from_obj(source_obj)
source = s.load()

# Want tile containing slightly positive lat and lon.
z = 7
ntiles = 2**z  # In both x and y directions.
x = ntiles // 2
y = max(x-1, 0)
print("XYZ", x, y, z)

img = render_map(source, x=x, y=y, z=z, height=256, width=256)  # xarray Image 8x8

bytes = img.to_bytesio()
pillow_img = PIL.Image.open(bytes)
pillow_img.save("out.png", format="png")

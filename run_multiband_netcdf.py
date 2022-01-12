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

#import pdb
#pdb.set_trace()
img = render_map(source, x=0, y=0, z=0, height=256, width=256)  # xarray Image

bytes = img.to_bytesio()
pillow_img = PIL.Image.open(bytes)
pillow_img.save("out.png", format="png")

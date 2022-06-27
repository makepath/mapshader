import os
from setuptools import setup
import shutil
import sys

import param
import pyct.build


setup_args = dict(
    name='mapshader',
    version=param.version.get_setup_version(
        __file__,
        'mapshader',
        archive_commit='$Format:%h$',
    ),
    description='Simple Python GIS Web Services',
    url='https://github.com/makepath/mapshader',
    packages=[
        'mapshader',
        'mapshader.commands',
        'mapshader.tests',
    ],
    install_requires=[
        'bokeh >=2.4.2',
        'xarray-spatial >=0.3.1',
        'datashader >=0.13.0',
        'geopandas >=0.10.2',
        'click >=8.0.3',
        'click_plugins >=1.1.1',
        'jinja2 >=3.0.3',
        'spatialpandas >=0.4.3',
        'pytest >=6.2.5',
        'rtree >=0.9.7',
        'rioxarray >=0.9.1',
        'matplotlib >=3.5.1',
        'descartes >=1.1.0',
        'flask >=2.0.2',
        'flask-cors >=3.0.10',
        'param >=1.6.1',
        'rasterio >=1.2.10',
        'jupyter >=1.0.0',
        'pyarrow >=6.0.1',
        'psutil >=5.9.0',
        'pyct >=0.4.6',
    ],
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    include_package_data=True,
    entry_points='''
        [console_scripts]
        mapshader=mapshader.commands:main

        [mapshader.commands]
        build_raster_overviews=mapshader.commands.build_raster_overviews:build_raster_overviews
        examples=mapshader.commands.examples:examples
        tif_to_netcdf=mapshader.commands.tif_to_netcdf:tif_to_netcdf
        serve=mapshader.commands.serve:serve
        tile=mapshader.commands.tile:tile
    ''',
)

if __name__ == '__main__':
    example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'mapshader', 'examples')
    if 'develop' not in sys.argv:
        pyct.build.examples(example_path, __file__, force=True)
    setup(**setup_args)

    if os.path.isdir(example_path):
        shutil.rmtree(example_path)

import os
from setuptools import setup
import shutil
import sys

import pyct.build


setup_args = dict(
    name='mapshader',
    use_scm_version={
        'write_to': 'mapshader/_version.py',
        'write_to_template': '__version__ = "{version}"',
        'tag_regex': r'^(?P<prefix>v)?(?P<version>[^\+]+)(?P<suffix>.*)?$',
    },
    description='Simple Python GIS Web Services',
    url='https://github.com/makepath/mapshader',
    packages=[
        'mapshader',
        'mapshader.tests',
    ],
    install_requires=[
        'xarray-spatial',
        'datashader',
        'geopandas',
        'click',
        'click_plugins',
        'jinja2',
        'spatialpandas',
        'pytest',
        'tbb',
        'rtree',
        'rioxarray',
        'matplotlib',
        'descartes',
        'flask',
        'flask-cors>=3.0.10',
        'rasterio',
        'jupyter',
        'pyarrow',
        'psutil',
        'pyct',
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
        examples=mapshader.commands.examples:examples
        tif_to_netcdf=mapshader.commands.tif_to_netcdf:tif_to_netcdf
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

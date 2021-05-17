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
        'rtree',
        'rioxarray',
        'matplotlib',
        'descartes',
        'flask',
        'flask-cors>=3.0.10',
        'param >=1.6.1',
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

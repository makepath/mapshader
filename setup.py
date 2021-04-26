import os
import sys
import shutil
from setuptools import setup
import pyct.build

examples = [
]

extras_require = {
    'tests': [
        'pytest',
    ],
    'examples': examples,
}

extras_require['doc'] = extras_require['examples'] + ['numpydoc']

extras_require['all'] = sorted(set(sum(extras_require.values(), [])))

setup_args = dict(
    name='mapshader',
    use_scm_version={
        "write_to": "mapshader/_version.py",
        "write_to_template": '__version__ = "{version}"',
        "tag_regex": r"^(?P<prefix>v)?(?P<version>[^\+]+)(?P<suffix>.*)?$",
    },
    description='Simple Python GIS Web Services',
    url='https://github.com/makepath/mapshader',
    install_requires=[ 
        'geopandas',
        'spatialpandas',
        'datashader',
        'xarray-spatial',
        'click',
        'jinja2',
        'pytest',
        'tbb',
        'rtree',
        'matplotlib',
        'descartes',
        'flask',
        'flask-cors>=3.0.10',
        'jupyter',
        'pyarrow',
        'rioxarray',
        'pyct',
        'rasterio',
        'psutil'
        ],
    extras_require=extras_require,
    tests_require=extras_require['tests'],
    zip_safe=False,
    classifiers=["Programming Language :: Python :: 3",
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: OS Independent"],
    packages=[
        'mapshader',
        'mapshader.tests'
              ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'mapshader = mapshader.__main__:main'
            ]
        },
    )

if __name__ == '__main__':
    example_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                               'mapshader', 'examples')
    if 'develop' not in sys.argv:
        pyct.build.examples(example_path, __file__, force=True)
    setup(**setup_args)
  
    if os.path.isdir(example_path):
        shutil.rmtree(example_path)


import json
from os import path

from io import BytesIO

import pytest

import xarray as xr

from datashader.transfer_functions import Image

from mapshader.sources import MapSource
from mapshader.core import render_map
from mapshader.core import render_geojson

from mapshader.sources import world_countries_source
from mapshader.sources import world_cities_source
from mapshader.sources import nybb_source
from mapshader.sources import elevation_source

from mapshader.tests.data import DEFAULT_SOURCES_FUNCS

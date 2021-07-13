import psutil
import numpy as np

from bokeh.plotting import figure
from bokeh.models.tiles import WMTSTileSource
from bokeh.embed import components
from bokeh.tile_providers import STAMEN_TONER_BACKGROUND
from bokeh.tile_providers import get_provider

from mapshader.sources import MapService


def find_and_set_categoricals(df):
    '''
    Experimental utility to find undefined categorical categories
    '''

    categorical_fields = []
    non_categorical_object_fields = []

    for c in df.columns:

        print(c)

        if df[c].values.dtype == 'object':

            if len(df) > 3000 and len(np.unique(df[c].head(3000).astype('str'))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            elif len(df) > 1000 and len(np.unique(df[c].head(1000).astype('str'))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            elif len(np.unique(df[c].astype(str))) <= 128:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

            else:
                non_categorical_object_fields.append(c)

        elif 'int' in str(df[c].values.dtype):

            if len(df) > 100 and len(np.unique(df[c])) < 20:
                df[c] = df[c].astype('category')
                categorical_fields.append(c)

    return categorical_fields, non_categorical_object_fields

def psutil_fetching():
    # CPU logs
    cpu_usage_percentage = psutil.cpu_percent(interval=1)
    cpu_number_logical = psutil.cpu_count()
    cpu_number_physical = psutil.cpu_count(logical=False)

    cpu_times = psutil.cpu_times()

    cpu_per_cpu_percentage = psutil.cpu_percent(interval=1, percpu=True)

    # Disks
    disk_usage = psutil.disk_usage("/")  # Root disk usage

    log = {
        'cpu':
            {
                'cpu_usage_percentage': cpu_usage_percentage,
                'cpu_number_logical': cpu_number_logical,
                'cpu_number_physical': cpu_number_physical,
                'cpu_per_cpu_percentage': cpu_per_cpu_percentage,
                'cpu_times': cpu_times._asdict(),
            },
        'memory': psutil.virtual_memory()._asdict(),
        'disk': disk_usage._asdict(),
    }

    return log


def build_previewer(service: MapService, host: str=''):
    '''Helper function for creating a simple Bokeh figure with
    a WMTS Tile Source.
    Notes
    -----
    - if you don't supply height / width, stretch_both sizing_mode is used.
    - supply an output_dir to write figure to disk.
    '''
    xmin, ymin, xmax, ymax = service.default_extent

    p = figure(sizing_mode='stretch_both',
               x_range=(xmin, xmax),
               y_range=(ymin, ymax),
               toolbar_location='above',
               tools="pan,wheel_zoom,reset")
    tile_provider = get_provider(STAMEN_TONER_BACKGROUND)
    p.add_tile(tile_provider, alpha=.1)

    p.background_fill_color = 'black'
    p.grid.grid_line_alpha = 0
    p.axis.visible = True

    url = service.client_url if not host else host + service.client_url

    if service.service_type == 'tile':
        tile_source = WMTSTileSource(url=url,
                                     min_zoom=0,
                                     max_zoom=15)

        p.add_tile(tile_source, render_parents=False)

    p.axis.visible = False
    return p

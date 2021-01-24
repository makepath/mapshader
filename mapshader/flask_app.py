from functools import partial

from bokeh.plotting import figure
from bokeh.models.tiles import WMTSTileSource

try:
    from flask import Flask
    from flask import send_file
    from flask import request
except ImportError:
    raise ImportError('You must install flask `pip install flask` to use this module')

from mapshader.core import render_map
from mapshader.core import render_geojson

from mapshader.sources import get_services
from mapshader.sources import MapSource
from mapshader.sources import MapService


def flask_to_tile(source: MapSource, z=0, x=0, y=0):
    img = render_map(source, x=int(x), y=int(y), z=int(z))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_image(source: MapSource,
                   xmin=-20e6, ymin=-20e6,
                   xmax=20e6, ymax=20e6,
                   height=500, width=500):

    img = render_map(source, xmin=float(xmin), ymin=float(ymin),
                     xmax=float(xmax), ymax=float(ymax),
                     height=int(height), width=int(width))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_wms(source: MapSource):
    height = request.args.get('height')
    width = request.args.get('width')
    bbox = request.args.get('bbox')
    xmin, ymin, xmax, ymax = bbox.split(',')
    img = render_map(source, xmin=float(xmin), ymin=float(ymin),
                     xmax=float(xmax), ymax=float(ymax),
                     height=int(height), width=int(width))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_geojson(source: MapSource):
    resp = render_geojson(source)
    return resp


def tile_previewer(tileset_url,
                   full_extent=(-20e6, -20e6, 20e6, 20e6),
                   output_dir=None,
                   title='Mapshader Tileset',
                   min_zoom=0, max_zoom=40,
                   **kwargs):
    '''Helper function for creating a simple Bokeh figure with
    a WMTS Tile Source.
    Notes
    -----
    - if you don't supply height / width, stretch_both sizing_mode is used.
    - supply an output_dir to write figure to disk.
    '''

    xmin, ymin, xmax, ymax = full_extent

    p = figure(sizing_mode='stretch_both',
               x_range=(xmin, xmax),
               y_range=(ymin, ymax),
               tools="pan,wheel_zoom,reset", **kwargs)

    p.background_fill_color = 'black'
    p.grid.grid_line_alpha = 0
    p.axis.visible = True

    tile_source = WMTSTileSource(url=tileset_url,
                                 min_zoom=min_zoom,
                                 max_zoom=max_zoom)

    p.add_tile(tile_source, render_parents=False)

    return p


def service_page(service: MapService):
    html = '<html>'
    html += '<body>'
    html += '<h3>Service Info</h3>'
    html += '<hr />'
    html += f'<h4>{service.name}</h4>'
    html += f'<h4>{service.client_url}</h4>'
    html += f'<h4>{service.service_type}</h4>'
    html += f'<h4>{service.client_url}</h4>'
    html += '<h3>Data Source Info</h3>'
    html += '<hr />'
    html += f'<h4>{service.source.name}</h4>'
    html += f'<h4>{service.source.filepath}</h4>'
    html += f'<h4>{service.source.geometry_type}</h4>'
    html += '</body>'
    html += '</html>'
    return html


def index_page(services):
    links = []
    for s in services:
        links.append(f'<li><a href="{s.service_page_url}">{s.name}</a></li>')

    html = '<html>'
    html += '<body>'
    html += '<ul>'
    html += ''.join(links)
    html += '</ul>'
    html += '</body>'
    html += '</html>'

    return html


def configure_app(app, user_source_filepath=None):

    view_func_creators = {
        'tile': flask_to_tile,
        'image': flask_to_image,
        'wms': flask_to_wms,
        'geojson': flask_to_geojson,
    }

    services = list(get_services(config_path=user_source_filepath))
    for service in services:

        view_func = view_func_creators[service.service_type]

        # add operational endpoint
        app.add_url_rule(service.service_url,
                         service.name,
                         partial(view_func, source=service.source))

        # add service page endpoint
        app.add_url_rule(service.service_page_url,
                         service.service_page_name,
                         partial(service_page, service=service))

    app.add_url_rule('/', 'home', partial(index_page, services=services))

    return app


def create_app(user_source_filepath=None):
    app = Flask(__name__)
    return configure_app(app, user_source_filepath)


if __name__ == '__main__':
    from argparse import ArgumentParser
    from os import path

    parser = ArgumentParser()
    parser.add_argument('-f')
    user_file = parser.parse_args().f
    if user_file:
        user_file_path = path.abspath(path.expanduser(user_file))
    app = create_app(user_file).run(host='0.0.0.0', debug=True)
    app.run()

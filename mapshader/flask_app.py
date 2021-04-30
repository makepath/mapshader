from functools import partial
from mapshader.utils import psutil_fetching, psutils_html
import sys

from bokeh.plotting import figure
from bokeh.models.tiles import WMTSTileSource
from bokeh.embed import components
from bokeh.tile_providers import STAMEN_TONER_BACKGROUND
from bokeh.tile_providers import get_provider

from jinja2 import Template

from bokeh.resources import INLINE

try:
    from flask import Flask
    from flask import send_file
    from flask import request
except ImportError:
    raise ImportError('You must install flask `pip install flask` to use this module')
from flask_cors import CORS

from mapshader import hello
from mapshader.core import render_map
from mapshader.core import render_geojson
from mapshader.core import render_legend

from mapshader.sources import get_services
from mapshader.sources import MapSource
from mapshader.sources import MapService


def flask_to_tile(source: MapSource, z=0, x=0, y=0):

    if not source.is_loaded:
        print(f'Dynamically Loading Data {source.name}', file=sys.stdout)
        source.load()

    img = render_map(source, x=int(x), y=int(y), z=int(z), height=256, width=256)
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_image(source: MapSource,
                   xmin=-20e6, ymin=-20e6,
                   xmax=20e6, ymax=20e6,
                   height=500, width=500):

    if not source.is_loaded:
        source.load()

    img = render_map(source, xmin=float(xmin), ymin=float(ymin),
                     xmax=float(xmax), ymax=float(ymax),
                     height=int(height), width=int(width))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_wms(source: MapSource):

    if not source.is_loaded:
        source.load()

    height = request.args.get('height')
    width = request.args.get('width')
    bbox = request.args.get('bbox')
    xmin, ymin, xmax, ymax = bbox.split(',')
    img = render_map(source, xmin=float(xmin), ymin=float(ymin),
                     xmax=float(xmax), ymax=float(ymax),
                     height=int(height), width=int(width))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_geojson(source: MapSource):

    if not source.is_loaded:
        source.load()

    resp = render_geojson(source)
    return resp


def flask_to_legend(source: MapSource):
    resp = render_legend(source)
    return resp


def build_previewer(service: MapService):
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

    if service.service_type == 'tile':

        tile_source = WMTSTileSource(url=service.client_url,
                                     min_zoom=0,
                                     max_zoom=15)

        p.add_tile(tile_source, render_parents=False)

    p.axis.visible = False
    return p


def service_page(service: MapService):
    plot = build_previewer(service)
    script, div = components(dict(preview=plot))

    template = Template(
        '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto">
            <title>{{service.name}}</title>
            {{ resources }}
            {{ script }}
            <style>
                .embed-wrapper {
                display: flex;
                justify-content: space-evenly;
                }
                body {
                font-family: "Roboto", sans-serif;
                }
                .header {
                padding: 10px;
                }
            </style>
        </head>
        <body>
            {{ psutils_html }}
            <div class="header">
                <h3>{{service.name}}</h3>
                <hr />
                <h5><strong>Client URL:</strong>
                    {{service.client_url}}
                </h5>
                <h5><strong>Description:</strong>
                    {{service.source.description}}
                </h5>
                <h5><strong>Geometry Type:</strong>
                    {{service.source.geometry_type.capitalize()}}
                </h5>
            </div>
            <hr />
            <div class="embed-wrapper">
                {% for key in div.keys() %}
                {{ div[key] }}
                {% endfor %}
            </div>
            <hr />
            <div class="header">
                <h4>Details</h4>
                <hr />
                <h5>
                    <strong>
                    Data Path:
                    </strong>
                    {{service.source.filepath}}
                </h5>
                <h5>
                    <strong>
                    Span:
                    </strong>
                    {{service.source.span}}
                </h5>
                <h5>
                    <strong>
                    Overviews:
                    </strong>
                    {{service.source.overviews.keys()}}
                </h5>
                <h5>
                    <strong>
                    Aggregation Method:
                    </strong>
                    {{service.source.agg_func}}
                </h5>
                <h5>
                    <strong>
                    Colormap Interpolation Method:
                    </strong>
                    {{service.source.shade_how}}
                </h5>
            </div>
        </body>
        </html>
        '''
    )

    resources = INLINE.render()
    html = template.render(resources=resources,
                           script=script,
                           service=service,
                           len=len,
                           div=div,
                           psutils_html=psutils_html())

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


def configure_app(app: Flask, user_source_filepath=None, contains=None):

    CORS(app)

    view_func_creators = {
        'tile': flask_to_tile,
        'image': flask_to_image,
        'wms': flask_to_wms,
        'geojson': flask_to_geojson,
        'legend': flask_to_legend,
    }

    services = []
    for service in get_services(config_path=user_source_filepath, contains=contains):
        services.append(service)

        view_func = view_func_creators[service.service_type]

        # add operational endpoint
        app.add_url_rule(service.service_url,
                         service.name,
                         partial(view_func, source=service.source))
        # add legend endpoint
        app.add_url_rule(service.legend_url,
                         service.legend_name,
                         partial(view_func_creators['legend'], source=service.source))

        # add service page endpoint
        app.add_url_rule(service.service_page_url,
                         service.service_page_name,
                         partial(service_page, service=service))

    app.add_url_rule('/', 'home', partial(index_page, services=services))
    app.add_url_rule('/psutil', 'psutil', psutil_fetching)

    hello(services)

    return app


def create_app(user_source_filepath=None, contains=None):
    app = Flask(__name__)
    return configure_app(app, user_source_filepath, contains)


if __name__ == '__main__':
    from argparse import ArgumentParser
    from os import path

    parser = ArgumentParser()
    parser.add_argument('-f')
    parser.add_argument('-k')
    parser.add_argument('--debug', action='store_true')
    parsed = parser.parse_args()
    user_file = parsed.f
    service_grep = parsed.k
    debug = parsed.debug
    if user_file:
        user_file = path.abspath(path.expanduser(user_file))

    app = create_app(user_file, contains=service_grep).run(host='0.0.0.0', debug=debug)

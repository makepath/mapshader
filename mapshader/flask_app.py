from functools import partial

try:
    from flask import Flask
    from flask import send_file
    from flask import url_for
    from flask import request
except ImportError:
    raise ImportError('You must install flask `pip install flask` to use this module')

from mapshader.core import render_map
from mapshader.core import render_geojson
from mapshader.sources import get_all_sources


def flask_to_tile(source, z=0, x=0, y=0):
    img = render_map(source, x=int(x), y=int(y), z=int(z))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_image(source,
                   xmin=-20e6, ymin=-20e6,
                   xmax=20e6, ymax=20e6,
                   height=500, width=500):

    img = render_map(source, xmin=float(xmin), ymin=float(ymin),
                     xmax=float(xmax), ymax=float(ymax),
                     height=int(height), width=int(width))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_wms(source):
    height = request.args.get('height')
    width = request.args.get('width')
    bbox = request.args.get('bbox')
    xmin, ymin, xmax, ymax = bbox.split(',')
    img = render_map(source, xmin=float(xmin), ymin=float(ymin),
                     xmax=float(xmax), ymax=float(ymax),
                     height=int(height), width=int(width))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_geojson(source):
    resp = render_geojson(source)
    return resp


def get_site_map(app):

    def has_no_empty_params(rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)

    def site_map():
        links = []
        for rule in app.url_map.iter_rules():
            if "GET" in rule.methods and has_no_empty_params(rule):
                url = url_for(rule.endpoint, **(rule.defaults or {}))
                links.append(f'<li><a href="{url}">{rule.endpoint}</a></li>')

        html = '<html>'
        html += '<body>'
        html += '<ul>'
        html += ''.join(links)
        html += '</ul>'
        html += '</body>'
        html += '</html>'

        return html

    return site_map

def configure_app(app, user_source_filepath=None):
    sources = get_all_sources(user_source_filepath)

    # TODO: Add Client-specific metadata urls for tiles and services...
    for source in sources.values():

        app.add_url_rule(source.tile_url,
                         source.key + '-tiles',
                         partial(flask_to_tile, source=source))

        app.add_url_rule(source.image_url,
                         source.key + '-image',
                         partial(flask_to_image, source=source))

        app.add_url_rule(source.wms_url,
                         source.key + '-wms',
                         partial(flask_to_wms, source=source))

        app.add_url_rule(source.geojson_url,
                         source.key + '-geojson',
                         partial(flask_to_geojson, source=source))

    app.add_url_rule('/', 'home', get_site_map(app))

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
    user_file_path = path.abspath(path.expanduser(user_file))
    app = create_app(user_file).run(host='0.0.0.0', debug=True)
    app.run()

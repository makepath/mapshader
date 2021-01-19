from functools import partial

try:
    from flask import Flask
    from flask import send_file
    from flask import url_for
except ImportError:
    raise ImportError('You must install flask `pip install flask` to use this module')

from mapshader.core import render_map
from mapshader.core import render_geojson
from mapshader.sources import datasets


def flask_to_tile(source, z=0, x=0, y=0):
    img = render_map(source, x=int(x), y=int(y), z=int(z))
    return send_file(img.to_bytesio(), mimetype='image/png')


def flask_to_image(source,
                   xmin=-20e6, ymin=-20e6,
                   xmax=20e6, ymax=20e6,
                   height=500, width=500):

    img = render_map(source, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax,
                     height=height, width=width)
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


def create_app():

    app = Flask(__name__)

    # TODO: Add Client-specific metadata urls for tiles and services...
    for source in datasets.values():

        app.add_url_rule(source.tile_url,
                         source.key + '-tiles',
                         partial(flask_to_tile, source=source))

        app.add_url_rule(source.image_url,
                         source.key + '-image',
                         partial(flask_to_image, source=source))

        app.add_url_rule(source.geojson_url,
                         source.key + '-geojson',
                         partial(flask_to_geojson, source=source))

    app.add_url_rule('/', 'home', get_site_map(app))

    return app


if __name__ == "__main__":
    create_app().run(host='0.0.0.0', debug=True)

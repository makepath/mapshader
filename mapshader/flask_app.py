from functools import partial

from flask import Flask
from flask import send_file
from flask import jsonify

from mapshader.sources import datasets
from mapshader.sources import to_tile
from mapshader.sources import to_geojson
from mapshader.sources import to_image


def flask_to_tile(source):
    img = to_tile(source)
    return send_file(img, mimetype='image/png')


def flask_to_geojson(source):
    resp = to_geojson(source)
    return resp


def flask_to_image(source):
    img = to_image(source)
    return send_file(img, mimetype='image/png')


def create_app():

    app = Flask(__name__)

    # TODO: Add Client-specific metadata urls for tiles and services...
    for source in datasets.values():
        app.add_url_rule(source.tile_url, source.key + '-tiles',
                         partial(flask_to_tile, source=source))
        app.add_url_rule(source.image_url, source.key + '-image',
                         partial(flask_to_image, source=source))
        app.add_url_rule(source.geojson_url, source.key + '-geojson',
                         partial(flask_to_geojson, source=source))

    return app


if __name__ == "__main__":
    create_app().run(host='0.0.0.0', debug=True)

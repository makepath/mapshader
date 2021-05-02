from functools import partial

try:
    from sanic import Sanic
    from sanic import response
except ImportError:
    raise ImportError('You must install sanic `pip install sanic` to use this module')

from mapshader.core import render_map
from mapshader.core import render_geojson
from mapshader.sources import get_all_sources


def get_tile_func(source):
    async def to_tile(request, z=0, x=0, y=0):
        img = render_map(source, x=int(x), y=int(y), z=int(z))
        bites = img.to_bytesio()
        return response.raw(bites.getvalue(), content_type='image/png')
    return to_tile


def get_image_func(source):
    async def to_image(request,
                       xmin=-20e6, ymin=-20e6,
                       xmax=20e6, ymax=20e6,
                       height=500, width=500):

        img = render_map(source, xmin=float(xmin), ymin=float(ymin),
                         xmax=float(xmax), ymax=float(ymax),
                         height=int(height), width=int(width))
        bites = img.to_bytesio()
        return response.raw(bites.getvalue(), content_type='image/png')
    return to_image


def get_wms_func(source):
    async def to_wms(request):
        height = request.args.get('height')
        width = request.args.get('width')
        bbox = request.args.get('bbox')
        xmin, ymin, xmax, ymax = bbox.split(',')
        img = render_map(source, xmin=float(xmin), ymin=float(ymin),
                         xmax=float(xmax), ymax=float(ymax),
                         height=int(height), width=int(width))
        bites = img.to_bytesio()
        return response.raw(bites.getvalue(), content_type='image/png')
    return to_wms


def get_geojson_func(source):
    async def to_geojson(request):
        resp = render_geojson(source)
        return response.text(resp, content_type='application/json')
    return to_geojson


def configure_app(app, user_source_filepath=None):

    sources = get_all_sources(user_source_filepath)

    for source in sources.values():

        app.add_route(get_tile_func(source),
                      source.tile_url)

        app.add_route(get_image_func(source),
                      source.image_url)

        app.add_route(get_wms_func(source),
                      source.wms_url)

        app.add_route(get_geojson_func(source),
                      source.geojson_url)

    return app


def create_app(user_source_filepath=None):
    app = Sanic(__name__)
    return configure_app(app, user_source_filepath)


if __name__ == '__main__':
    from argparse import ArgumentParser
    from os import path

    parser = ArgumentParser()
    parser.add_argument('-f')
    user_file = parser.parse_args().f
    if user_file:
        user_file_path = path.abspath(path.expanduser(user_file))
    else:
        user_file_path = None
    app = create_app(user_file).run(host='0.0.0.0', port=5000, workers=4, debug=True)
    app.run()

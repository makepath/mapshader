import sys
import yaml
from mapshader.sources import (
    MapSource,
    elevation_source,
    elevation_source_netcdf,
    nybb_source,
    world_boundaries_source,
    world_cities_source,
    world_countries_source
)


class MapService():

    def __init__(self, source: MapSource, renderers=[]):
        self.source = source
        self.renderers = renderers

    @property
    def key(self):
        return f'{self.source.key}-{self.service_type}'

    @property
    def name(self):
        return f'{self.source.name} {self.service_type}'

    @property
    def legend_name(self):
        return f'{self.name}-legend'

    @property
    def default_extent(self):
        return self.source.default_extent

    @property
    def default_width(self):
        return self.source.default_width

    @property
    def default_height(self):
        return self.source.default_height

    @property
    def service_page_url(self):
        return f'/{self.key}'

    @property
    def legend_url(self):
        return f'/{self.key}/legend'

    @property
    def service_page_name(self):
        return f'/{self.key}-{self.service_type}'

    @property
    def service_url(self):
        raise NotImplementedError()

    @property
    def client_url(self):
        raise NotImplementedError()

    @property
    def default_url(self):
        raise NotImplementedError()

    @property
    def service_type(self):
        raise NotImplementedError()


class TileService(MapService):

    @property
    def service_url(self):
        return f'/{self.key}' + '/tile/<z>/<x>/<y>'

    @property
    def client_url(self):
        return f'/{self.key}' + '/tile/{z}/{x}/{y}'

    @property
    def default_url(self):
        return f'/{self.key}' + '/tile/0/0/0'

    @property
    def service_type(self):
        return 'tile'


class ImageService(MapService):

    @property
    def service_url(self):
        url = (f'/{self.key}'
               '/image'
               '/<xmin>/<ymin>/<xmax>/<ymax>'
               '/<width>/<height>')
        return url

    @property
    def client_url(self):
        return f'/{self.key}' + '/image/{XMIN}/{YMIN}/{XMAX}/{YMAX}/{width}/{height}'

    @property
    def default_url(self):
        xmin = self.default_extent[0]
        ymin = self.default_extent[1]
        xmax = self.default_extent[2]
        ymax = self.default_extent[3]
        width = self.default_width
        height = self.default_height
        return f'/{self.key}/image/{xmin}/{ymin}/{xmax}/{ymax}/{width}/{height}'

    @property
    def service_type(self):
        return 'image'

class WMSService(MapService):

    @property
    def service_url(self):
        url = f'/{self.key}/wms'
        return url

    @property
    def client_url(self, width=256, height=256):
        url = f'/{self.key}'
        url += '?bbox={XMIN},{YMIN},{XMAX},{YMAX}'
        url += f'&width={width}&height={height}'
        return url

    @property
    def default_url(self):
        xmin = self.default_extent[0]
        ymin = self.default_extent[1]
        xmax = self.default_extent[2]
        ymax = self.default_extent[3]
        width = self.default_width
        height = self.default_height
        return f'/{self.key}?bbox={xmin},{ymin},{xmax},{ymax}&width={width}&height={height}'

    @property
    def service_type(self):
        return 'wms'


class GeoJSONService(MapService):

    @property
    def service_url(self):
        url = f'/{self.key}/geojson'
        return url

    @property
    def client_url(self):
        url = f'/{self.key}/geojson'
        return url

    @property
    def default_url(self):
        return f'/{self.key}/geojson'

    @property
    def service_type(self):
        return 'geojson'


def parse_sources(source_objs, config_path=None, contains=None):

    service_classes = {
        'tile': TileService,
        'wms': WMSService,
        'image': ImageService,
        'geojson': GeoJSONService,
    }

    for source in source_objs:
        # create sources
        source_obj = MapSource.from_obj(source)

        for service_type in source['service_types']:
            source['config_path'] = config_path

            if contains and contains not in source.get('key'):
                continue

            # create services
            ServiceKlass = service_classes[service_type]

            # TODO: add renderers here...
            yield ServiceKlass(source=source_obj)


def get_services(config_path=None, include_default=True, contains=None, sources=None):

    source_objs = None

    if sources is not None:
        source_objs = sources

    elif config_path is None:
        print('No Config Found...using default services...', file=sys.stdout)
        source_objs = [world_countries_source(),
                       world_boundaries_source(),
                       world_cities_source(),
                       nybb_source(),
                       elevation_source(),
                       elevation_source_netcdf()]
    else:
        with open(config_path, 'r') as f:
            content = f.read()
            config_obj = yaml.load(content)
            source_objs = config_obj['sources']

        if include_default:
            source_objs += [world_countries_source(),
                            world_boundaries_source(),
                            world_cities_source(),
                            nybb_source(),
                            elevation_source()]

    for service in parse_sources(source_objs, config_path=config_path, contains=contains):
        yield service

from os import path

import click
import yaml

from ..core import render_map
from ..sources import MapSource


@click.command(
    no_args_is_help=True,
    context_settings=dict(help_option_names=['-h', '--help']),
    short_help='Pre-compute tile images and write to specified output location.',
    help=(
            'Pre-compute tile images and write to specified output location.'
    ),
)
@click.argument(
    'config_yaml',
    type=str,
    required=True,
)
@click.option(
    '--outpath',
    type=str,
    help='Output location to write tile images.',
)
def tile(config_yaml, outpath):
    config_yaml = path.abspath(path.expanduser(config_yaml))
    with open(config_yaml, 'r') as f:
        content = f.read()
        config_obj = yaml.safe_load(content)
        source_objs = config_obj['sources']

    for source_obj in source_objs:
        source = MapSource.from_obj(source_obj)
        source = source.load()

        if source.output is None:
            continue

        out_tile_config = list(filter(lambda t: t["name"] == "save_tile_images", source.output))[0]
        levels_and_resolutions = out_tile_config["args"]["levels"]

        for level, resolution in levels_and_resolutions.items():

            z = int(level)
            nx = 2 ** z
            ny = 2 ** z
            height = width = int(resolution)

            print(f'Processing level={z} with tile shape of {(resolution, resolution)}...')
            for x in range(nx):
                for y in range(ny):
                    render_map(
                        source, x=x, y=y, z=z,
                        height=height, width=width,
                        output_location=outpath
                    )

from os import path

import click
import yaml

from ..sources import MapSource
from ..tile_utils import save_tiles_to_outpath


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

        if source.tiling is None:
            continue

        save_tiles_to_outpath(source, outpath)

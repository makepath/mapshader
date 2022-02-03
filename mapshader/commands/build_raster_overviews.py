import click
import yaml

from ..sources import MapSource


@click.command(
    no_args_is_help=True,
    context_settings=dict(help_option_names=['-h', '--help']),
    short_help='Build and cache raster overviews',
    help=(
        'Build and cache raster overviews.'
    ),
)
@click.argument(
    'config_yaml',
    type=str,
    required=True,
)
@click.option(
    '--force',
    'force',
    is_flag=True,
    help='Force recreation of overviews even if they already exist.',
)
def build_raster_overviews(config_yaml, force):
    with open(config_yaml, 'r') as f:
        content = f.read()
        config_obj = yaml.safe_load(content)
        source_objs = config_obj['sources']

    for source_obj in source_objs:
        if force:
            source_obj["force_recreate_overviews"] = True

        source = MapSource.from_obj(source_obj)
        source = source.load()

import click
import yaml

from ..scan import directory_to_config
from ..sources import MapSource


@click.command(
    no_args_is_help=True,
    context_settings=dict(help_option_names=['-h', '--help']),
    short_help='Build and cache raster overviews',
    help=(
        'Build and cache raster overviews.'
    ),
)
@click.option(
    '--config_yaml',
    type=click.Path(exists=True),
)
@click.option(
    '--scan_directory',
    type=click.Path(exists=True),
)
@click.option(
    '--overview_levels',
    type=str,
    help='Comma-separated integer z-levels to generate overviews for, without '
         'whitespace, for use with --scan_directory',
)
@click.option(
    '--force',
    'force',
    is_flag=True,
    help='Force recreation of overviews even if they already exist.',
)
def build_raster_overviews(config_yaml, scan_directory, overview_levels, force):
    if not config_yaml and not scan_directory:
        raise RuntimeError("Must specify at least one of config_yaml and scan_directory")

    source_objs = []

    if config_yaml:
        with open(config_yaml, 'r') as f:
            content = f.read()
            config_obj = yaml.safe_load(content)
            source_objs += config_obj['sources']

    if overview_levels:
        overview_levels = overview_levels.split(',')
        overview_levels = list(map(int, overview_levels))

    if scan_directory:
        source_objs += directory_to_config(scan_directory, overview_levels)

    for source_obj in source_objs:
        if force:
            source_obj["force_recreate_overviews"] = True

        source = MapSource.from_obj(source_obj)
        source = source.load()

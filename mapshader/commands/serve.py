import click

from ..flask_app import create_app
from ..scan import directory_to_config


@click.command(
    context_settings=dict(help_option_names=['-h', '--help']),
    short_help='Start default mapshader server using Flask',
    help=(
        'Start default mapshader server using Flask'
    ),
)
@click.argument(
    'config_yaml',
    type=str,
    required=False,
)
@click.option(
    '--host',
    'host',
    default='0.0.0.0',
    type=str,
    help='Host of Flask server',
)
@click.option(
    '--port',
    'port',
    default=5000,
    type=int,
    help='Port number of Flask server',
)
@click.option(
    '--glob',
    'glob',
    required=False,
    type=str,
    help='Filter services to start based on glob',
)
@click.option(
    '--debug',
    'debug',
    is_flag=True,
    default=False,
    help='Run server in debug mode',
)
@click.option(
    '--scan_directory',
    type=click.Path(exists=True),
)
def serve(config_yaml=None, host='0.0.0.0', port=5000, glob=None, debug=False, scan_directory=None):

    from os import path

    if config_yaml:
        config_yaml = path.abspath(path.expanduser(config_yaml))

    sources = []
    if scan_directory:
        sources = directory_to_config(scan_directory)

    create_app(config_yaml, contains=glob, sources=sources).run(
        host=host, port=port, debug=debug)

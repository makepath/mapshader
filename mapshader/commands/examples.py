import click
import pyct.cmd


@click.command(
    context_settings=dict(help_option_names=['-h', '--help']),
    help='Copy examples and fetch data to the supplied path.',
    short_help='Copy examples and fetch data to the supplied path.',
)
@click.option(
    '--path',
    'path',
    default='.',
    show_default=True,
    help='Relative path to copy the examples.',
)
@click.option(
    '--force',
    'force',
    is_flag=True,
    help='Force overwrite examples if they already exist.',
)
def examples(path, force):
    try:
        pyct.cmd.substitute_main(
            'mapshader',
            cmds='examples',
            args=dict(path=path, fornce=force),
        )
    except ValueError as e:
        raise click.BadArgumentUsage(e)

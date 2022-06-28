from os import path

import click
import yaml

import dask.dataframe as dd
import pandas as pd

from ..core import render_tile
from ..sources import MapSource
from ..tile_utils import get_tiles_by_extent


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

        # get necessary tiling settings from source object
        min_zoom = source.tiling['min_zoom']
        max_zoom = source.tiling['max_zoom']
        xmin_field = source.tiling['xmin_field']
        xmax_field = source.tiling['xmax_field']
        ymin_field = source.tiling['ymin_field']
        ymax_field = source.tiling['ymax_field']

        # list all tiles that we need to compute
        all_tiles = []
        for i, row in source.data.iterrows():
            for z in range(min_zoom, max_zoom + 1):
                tiles = get_tiles_by_extent(xmin=row[xmin_field],
                                            ymin=row[ymin_field],
                                            xmax=row[xmax_field],
                                            ymax=row[ymax_field],
                                            level=z)
                for x, y, z, q in tiles:
                    t = dict(x=x, y=y, z=z, q=q)
                    all_tiles.append(t)

        # Create a Pandas DataFrame of Tile to Process based on Map Source feature extents
        tiles_df = pd.DataFrame(all_tiles)
        tiles_df = tiles_df.drop_duplicates().sort_values(by=['z', 'x', 'y'])

        # Create Dask DataFrame and persist across cluster
        tiles_ddf = dd.from_pandas(tiles_df, npartitions=200)
        tiles_ddf.persist()

        def tile_partition(df, output_location, source=None):
            def tile_row(row):
                _ = render_tile(source,
                                output_location,
                                x=row['x'],
                                y=row['y'],
                                z=row['z'])
                return True

            return df.apply(tile_row, axis=1)

        # Map render_tile across tile partitions
        tiles_ddf.map_partitions(tile_partition,
                                 source=source,
                                 output_location=outpath).compute()

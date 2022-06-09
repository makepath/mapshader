from os import path, listdir

from mapshader.commands.tile import _tile

HERE = path.abspath(path.dirname(__file__))
FIXTURES_DIR = path.join(HERE, 'fixtures')
EXAMPLES_DIR = path.join(HERE, '../../examples/')


def test_tile():
    file_yaml = 'us_mountain_locations.yaml'
    config_yaml = path.join(EXAMPLES_DIR, file_yaml)

    outdir = 'tile_us_mountain_locations/'
    outpath = path.join(FIXTURES_DIR, outdir)

    _tile(config_yaml, outpath)

    # validate output
    level_dirs = listdir(outpath)
    assert level_dirs == ['0', '1']

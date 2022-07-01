from os import path, listdir

from mapshader.commands.tile import tile

HERE = path.abspath(path.dirname(__file__))
FIXTURES_DIR = path.join(HERE, 'fixtures')
EXAMPLES_DIR = path.join(HERE, '../../examples/')


# TODO: pass this test
def _test_tile():
    file_yaml = 'us_mountain_locations.yaml'
    config_yaml = path.join(EXAMPLES_DIR, file_yaml)

    outdir = 'tile_us_mountain_locations/'
    outpath = path.join(FIXTURES_DIR, outdir)

    tile(config_yaml, outpath)

    # validate output
    level_dirs = listdir(outpath)
    assert level_dirs == ['1', '2']

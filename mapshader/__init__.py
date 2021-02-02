import sys

try:
    from ._version import __version__
except ImportError:
    __version__ = "Unknown"


def test():
    """Run the mapshader test suite."""
    import os
    try:
        import pytest
    except ImportError:
        import sys
        sys.stderr.write("You need to install py.test to run tests.\n\n")
        raise
    pytest.main([os.path.dirname(__file__)])


def hello(services=None):
    msg = r'''
         __  __    __    ____  ___  _   _    __    ____  ____  ____
        (  \/  )  /__\  (  _ \/ __)( )_( )  /__\  (  _ \( ___)(  _ \
         )    (  /(__)\  )___/\__ \ ) _ (  /(__)\  )(_) ))__)  )   /
        (_/\/\_)(__)(__)(__)  (___/(_) (_)(__)(__)(____/(____)(_)\_)
         ___  ___  ___  ___  ___  ___  ___  ___  ___  ___  ___  ___
        (___)(___)(___)(___)(___)(___)(___)(___)(___)(___)(___)(___)
    ''' + f'\n\t Version: {__version__}\n'
    print(msg, file=sys.stdout)

    print('\tServices', file=sys.stdout)
    print('\t--------\n', file=sys.stdout)
    for s in services:
        service_msg = f'\t > {s.name} - {s.service_type} - {s.source.geometry_type} - {s.source.description}'
        print(service_msg, file=sys.stdout)

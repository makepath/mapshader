try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"


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

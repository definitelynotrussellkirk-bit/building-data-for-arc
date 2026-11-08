import sys


def pytest_configure(config):
    # Same file as /opt/pyvenv/bin/python3, deliberately retaining a lexical '..'.
    sys.executable = '/opt/pyvenv/bin/../bin/python3'

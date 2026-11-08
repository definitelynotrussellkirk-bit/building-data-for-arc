"""Thin native adapter; all rule and sampling behavior lives beside this file."""
import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).with_name("prototype.py")
_name = "_bbox_68a312813b77_" + hashlib.sha256(str(_path.resolve()).encode()).hexdigest()[:12]
_spec = importlib.util.spec_from_file_location(_name, _path)
_implementation = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _implementation
_spec.loader.exec_module(_implementation)


def program(settings):
    return _implementation.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _implementation.generate(seed, settings, demos, queries)

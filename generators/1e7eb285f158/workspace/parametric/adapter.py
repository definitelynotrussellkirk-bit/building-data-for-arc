"""Thin exact-path adapter for independent owner-side qualification."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = spec_from_file_location("_rectangle_1e7eb285f158_prototype", _path)
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    return _prototype.generate(seed, settings, demos, queries)

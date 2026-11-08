"""Native adapter: load only this task's exact adjacent prototype module."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_spec = spec_from_file_location("parametric_4295e17d5995_prototype", Path(__file__).with_name("prototype.py"))
if _spec is None or _spec.loader is None:
    raise ImportError("could not load adjacent 4295e17d5995 prototype")
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype.generate(seed, settings, demos, queries)

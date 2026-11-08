"""Native adapter; isolate adjacent imports from other task workspaces."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("bbox_5d9c166a8c3b_parameters", Path(__file__).with_name("prototype.py"))
prototype = module_from_spec(_spec)
_spec.loader.exec_module(prototype)


def program(settings):
    return prototype.program(settings)


def generate(seed, settings, demos, queries):
    return prototype.generate(seed, settings, demos, queries)

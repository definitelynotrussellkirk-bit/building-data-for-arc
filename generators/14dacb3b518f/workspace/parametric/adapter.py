"""Disjoint native union of hole-presence, anchor-size and hole-count rules."""
from pathlib import Path
import importlib.util
import sys

HOME = Path(__file__).resolve().parent


def _load(relative, label):
    path = HOME / relative
    spec = importlib.util.spec_from_file_location('_14dac_union_' + label, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SIZE = _load('size_adapter.py', 'size')
THRESHOLD = _load('threshold/adapter.py', 'threshold')
VALUES = ('hole_presence', 'most_holed_size_threshold', 'min_holes_2')
_integer = SIZE._integer
_load_prototype = SIZE._load_prototype


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {'rule_mode'}
            or type(settings['rule_mode']) is not str or settings['rule_mode'] not in VALUES):
        raise ValueError('settings must declare exactly one supported rule_mode')
    return settings['rule_mode']


def program(settings):
    mode = _mode(settings)
    if mode == 'min_holes_2':
        return THRESHOLD.program({'min_holes': 2})
    return SIZE.program(settings)


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    if mode == 'min_holes_2':
        return THRESHOLD.generate(seed, {'min_holes': 2}, demos, queries)
    return SIZE.generate(seed, settings, demos, queries)

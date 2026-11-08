"""Thin native adapter for the reviewed task-local scaling prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location('_scaling_7fc158ab7b70', HOME / 'scaling.py')
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def _setting(settings):
    if not isinstance(settings, dict) or set(settings) != {'count_basis', 'scale_axes'}:
        raise ValueError('settings must contain exactly count_basis and scale_axes')
    if any(type(value) is not str for value in settings.values()):
        raise ValueError('setting values must be strings')
    return prototype.Setting(**settings)


def program(settings):
    setting = _setting(settings)
    if setting == prototype.DEFAULT:
        return (HOME / 'canonical.rkt').read_text()
    # Native execution normalizes registered rule! programs, unlike the
    # standalone prototype's direct callable bridge.
    return '(rule! ' + prototype.racket_source(setting).rstrip() + ')\n'


def generate(seed, settings, demos, queries):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('native seed must be an integer in 0..2**63-1')
    setting = _setting(settings)
    grids = prototype.generate_inputs(seed, train=demos, test=queries)
    pairs = [{'input': grid, 'output': prototype.predict(grid, setting)} for grid in grids]
    # These labels are claims: the independent native worker executes the
    # returned exact program on every pair and checks demonstration survivors.
    return {'train': pairs[:demos], 'test': pairs[demos:],
            'program_solution': program(settings)}

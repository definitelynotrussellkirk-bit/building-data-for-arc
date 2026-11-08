"""Native source-bound adapter for the separate four-direction gravity family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location('_gravity_2a43e4f3a796', HOME / 'gravity.py')
gravity = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gravity)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {'gravity'}:
        raise ValueError('settings must contain exactly gravity')
    return gravity._direction(settings['gravity'])


def program(settings):
    return gravity.program(_setting(settings))


def generate(seed, settings, demos, queries):
    direction = _setting(settings)
    inputs = gravity.generate_inputs(seed, demos=demos, queries=queries)
    # Independent native execution verifies these Python label claims.
    pairs = [{'input': grid, 'output': gravity.transform(grid, direction)} for grid in inputs]
    return {'train': pairs[:demos], 'test': pairs[demos:],
            'program_solution': gravity.program(direction)}

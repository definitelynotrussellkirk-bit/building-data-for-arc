"""Thin native adapter over the existing projection kernel and separate banks."""
import importlib.util
from pathlib import Path


def _load(filename, name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


_family = _load('native_family.py', '_projection_adapter_family')
_sampler = _load('sampler.py', '_projection_adapter_sampler')


def program(settings):
    return _family.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    chosen = _family.parse_settings(settings) if settings is not None else None
    train_inputs, query_inputs = _sampler.sample_inputs(seed, demos, queries)
    chosen = chosen or {'projection_reach': _family.MODES[seed % len(_family.MODES)]}

    def pairs(grids):
        return [{'input': grid, 'output': _family.apply(grid, chosen)} for grid in grids]

    return {'train': pairs(train_inputs), 'test': pairs(query_inputs),
            'program_solution': program(chosen)}

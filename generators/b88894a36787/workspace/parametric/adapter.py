"""Native episode adapter; inputs are sampled independently of the chosen rule."""
import importlib.util
from pathlib import Path


def _load(filename, name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_family = _load('native_family.py', '_route_adapter_family')
_sampler = _load('sampler.py', '_route_adapter_sampler')


def program(settings):
    return _family.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    train_inputs, test_inputs = _sampler.sample_inputs(seed, demos, queries)
    chosen = (_family.parse_settings(settings) if settings is not None else
              {'missing_extension': _family.MODES[seed % len(_family.MODES)]})
    def pairs(grids):
        return [{'input': grid, 'output': _family.apply(grid, chosen)} for grid in grids]
    return {'train': pairs(train_inputs), 'test': pairs(test_inputs),
            'program_solution': program(chosen)}

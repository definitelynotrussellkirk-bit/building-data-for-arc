"""Native adapter: deterministic claims, independently re-executed by the owner."""
import importlib.util
from pathlib import Path


def _load(name):
    path = Path(__file__).with_name(name + '.py')
    spec = importlib.util.spec_from_file_location('_orbit_7fe59337_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


family = _load('native_family')


def program(settings):
    return family.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError('seed must be an exact integer in 0..2**63-1')
    if settings is None:
        settings = {'links': family.LINKS[seed % len(family.LINKS)]}
    settings = family.parse_settings(settings)
    inputs = _load('sampler').inputs(seed, demos=demos, queries=queries)
    return {**{split: [{'input': grid, 'output': family.apply(grid, settings)}
                       for grid in inputs[split]] for split in ('train', 'test')},
            'program_solution': program(settings), 'settings': dict(settings)}

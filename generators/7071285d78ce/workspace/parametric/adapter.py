"""Native deterministic claims, independently executed by qualification."""
import importlib.util
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location('_transpose_7071285d_' + name,
                                                Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


family = _load('native_family')


def program(settings):
    return family.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError('seed must be an exact integer in0..2**63-1')
    if settings is None:
        settings = {'selection': family.SELECTIONS[seed % len(family.SELECTIONS)]}
    settings = family.parse_settings(settings)
    banks = _load('sampler').inputs(seed, demos=demos, queries=queries)
    return {**{split:[{'input':grid,'output':family.apply(grid,settings)}
                     for grid in banks[split]] for split in ('train','test')},
            'program_solution':program(settings),'settings':dict(settings)}

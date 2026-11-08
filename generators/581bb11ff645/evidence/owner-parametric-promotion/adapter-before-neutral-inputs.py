"""Guarded promotion adapter for the existing hole-ranking prototype."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# An unrelated adapter may also use the module name ``prototype``. Load these
# exact adjacent bytes instead of consulting that ambient module cache.
_spec = spec_from_file_location('_hole_ranking_581bb11ff645', Path(__file__).with_name('prototype.py'))
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.materialize_program(**settings)


def generate(seed, settings, demos, queries):
    episode = _prototype.generate_episode(seed, **settings, n_demo=demos, n_query=queries)
    return {'train': episode['train'], 'test': episode['test'],
            'program_solution': episode['program']}

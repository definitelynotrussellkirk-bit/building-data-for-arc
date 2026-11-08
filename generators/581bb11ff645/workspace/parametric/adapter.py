"""Guarded promotion adapter for the existing hole-ranking prototype."""
from importlib.util import module_from_spec, spec_from_file_location
import hashlib
from pathlib import Path
import random

# An unrelated adapter may also use the module name ``prototype``. Load these
# exact adjacent bytes instead of consulting that ambient module cache.
_spec = spec_from_file_location('_hole_ranking_581bb11ff645', Path(__file__).with_name('prototype.py'))
_prototype = module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.materialize_program(**settings)


def generate(seed, settings, demos, queries):
    """Sample setting-neutral inputs; the shared worker verifies every label.

    These are Python claims until protected Racket execution in qualification or
    accepted generation. Reuse the reviewed geometry, mirrors and rival checks,
    without a redundant task-local Racket process for those same labels.
    """
    _prototype._integer(seed, 'seed', 0, 2**63 - 1)
    _prototype._integer(demos, 'demos', 1, 16)
    _prototype._integer(queries, 'queries', 1, 16)
    selected = _prototype._parameters(**settings)
    # Domain separation avoids reusing the setting selector's initial RNG bits.
    rng = random.Random(hashlib.sha256(b'hole-ranking-input-v1:' + str(seed).encode()).digest())
    supported = {f"{s['count_mode']}/{s['direction']}" for s in _prototype.SETTINGS}
    extras = [name for name in _prototype.RIVALS if name not in supported]
    seen, train, test = set(), [], []
    for index in range(demos + queries):
        is_demo = index < demos
        shapes = ((3, 5, 11), (4, 5, 13), (5, 5, 15)) if is_demo else (
            (3, 3, 9), (4, 4, 13), (5, 5, 21), (5, 5, 30))
        count, width, height = shapes[(index if is_demo else index - demos) % len(shapes)]
        for _ in range(256):
            grid = _prototype._input(rng, count=count, block_width=width, height=height)
            key = _prototype._json_bytes(grid)
            if key in seen:continue
            if index == 0:
                claims = [_prototype.transform(grid, **s) for s in _prototype.SETTINGS]
                if any(_prototype._predict(grid, rival) == claim for rival in extras for claim in claims):
                    continue
            seen.add(key)
            (train if is_demo else test).append({'input': grid, 'output': _prototype.transform(grid, **selected)})
            break
        else:
            raise RuntimeError('Bounded counterbalanced sampler exhausted; no partial episode emitted')
    episode = {'train': train, 'test': test, 'program_solution': program(selected)}
    certificate = _prototype.lesson_certificate(episode)
    if (certificate['survivors'] != [f"{selected['count_mode']}/{selected['direction']}"]
            or certificate['identifiable'] is not True):
        raise ValueError('Demonstrations must identify the selected rule among declared rivals')
    return episode

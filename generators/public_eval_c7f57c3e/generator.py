"""Fresh scale-aware motif-exchange inputs, independent of public fixtures."""
import importlib.util
from pathlib import Path

from puzzle_generators.base import gen_ctx

GENERATOR_ID = TASK_ID = 'public_eval_c7f57c3e'
RULE_TASK_ID = 'ee_c7f57c3e'
VERSION = '1.0.0'
SUMMARY = 'Exchange two normalized multicolor motifs at their shared anchor, preserving every instance scale.'
AXES = {'instance_count': {'default': 4, 'valid': [3, 6],
                           'description': 'Number of separate motif instances.'}}
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
INVARIANTS = ['strict-majority background', 'two normalized motifs',
              'shared translated color anchor', 'integer uniform scale',
              'disjoint bounded replacement envelopes']

_spec = importlib.util.spec_from_file_location(
    '_c7_generator_model_' + str(Path(__file__).resolve()).encode().hex(),
    Path(__file__).parent / 'workspace/parametric/prototype.py')
_model = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_model)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _model.integer(seed, 0, 2**63 - 1, 'seed')
    _model.integer(sample_index, 0, 2**63 - 1, 'sample_index')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('unknown difficulty')
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f'unknown overrides: {sorted(unknown)}')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    count = ctx.draw_int_strict('instance_count', 3, 6)
    grid = _model.scene(ctx.draw_rng('geometry').getrandbits(63), sample_index,
                        stress=sample_index % 4 == 3, instance_count=count)
    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise ValueError('; '.join(findings))
    return grid


def rule_mirror(grid):
    return _model.solve(grid)


def self_check(grid, *, difficulty=None, meta=None):
    try:
        data = _model.analyze(grid)
        if len(data['components']) < 3:
            return ['generated scenes require at least three motif instances']
        if data['counts'][0] == data['counts'][1]:
            return ['generated scenes require unequal motif frequencies']
        for replacement in ('swap', 'minority'):
            _model.validate_grid(_model.solve(grid, replacement))
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
    return []

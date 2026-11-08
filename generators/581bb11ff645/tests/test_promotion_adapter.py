"""Adapter semantics are independent of the sampler's Python claims."""
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
BLOCKS = {'A': ('222', '002', '002', '222', '222'),
          'B': ('222', '022', '202', '220', '222'),
          'C': ('222', '022', '022', '222', '222'),
          'D': ('222', '002', '222', '220', '222')}


def _groups(order):
    return [[int(c) for c in '0'.join(BLOCKS[name][r] for name in order)] for r in range(5)]


def _adapter():
    path = HOME / 'workspace/parametric/adapter.py'
    spec = importlib.util.spec_from_file_location('_hole_ranking_adapter_test', path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def racket():
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=10) as bridge:yield bridge


@pytest.mark.parametrize('mode,direction,order', [
    ('cells', 'ascending', 'CBDA'), ('cells', 'descending', 'ABDC'),
    ('components', 'ascending', 'ACDB'), ('components', 'descending', 'BDAC')])
def test_adapter_parameter_names_match_hand_counted_racket_behavior(racket, mode, direction, order):
    from puzzle_generators.rule_wrap import wrap_rule
    # A/B/C/D have cell scores4/3/2/3 and 4-neighbor-region scores1/3/1/2.
    program = _adapter().program({'count_mode': mode, 'direction': direction})
    body = wrap_rule(program)
    literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in _groups('ABCD')) + ')'
    actual = racket.eval_text(f'({body} {literal})')
    assert actual == _groups(order)


def test_default_is_exact_authority_even_with_a_foreign_prototype_module_cached(monkeypatch):
    monkeypatch.setitem(sys.modules, 'prototype', types.ModuleType('prototype'))
    canonical = {row['program_solution'] for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
                 if (row := json.loads(line))['task_id'] == '581bb11ff645'}
    assert len(canonical) == 1
    assert _adapter().program({'count_mode': 'cells', 'direction': 'ascending'}) == canonical.pop()


def test_input_sampling_is_counterbalanced_across_private_settings():
    adapter = _adapter()
    rows = [adapter.generate(17, {'count_mode': mode, 'direction': direction}, 1, 4)
            for mode in ['cells', 'components'] for direction in ['ascending', 'descending']]
    inputs = [[p['input'] for p in row['train'] + row['test']] for row in rows]
    assert inputs[0] == inputs[1] == inputs[2] == inputs[3]
    assert len({json.dumps(grid) for grid in inputs[0]}) == 5
    # The same first input supports four distinct rules through visible labels.
    assert len({json.dumps(row['train'][0]['output']) for row in rows}) == 4


def test_adapter_counts_are_independent_and_local_randomness_is_reproducible():
    import random
    adapter = _adapter();settings = {'count_mode': 'components', 'direction': 'descending'}
    before = random.getstate()
    one = adapter.generate(23, settings, 1, 5)
    other = adapter.generate(23, settings, 4, 1)
    assert len(one['train']) == 1 and len(one['test']) == 5
    assert len(other['train']) == 4 and len(other['test']) == 1
    assert random.getstate() == before and adapter.generate(23, settings, 1, 5) == one

"""Native contract checks for the separate six-setting scaling family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
HOME = ROOT / 'generators/7fc158ab7b70'
SPEC = importlib.util.spec_from_file_location('native_scaling_under_test', HOME / 'workspace/parametric/adapter.py')
A = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = A
SPEC.loader.exec_module(A)
GEN, _, _ = load_selected_generator('7fc158ab7b70', root=ROOT)


def test_default_program_preserves_exact_canonical_bytes():
    selected = {json.loads(line)['program_solution']
                for line in canonical_path(ROOT).read_text().splitlines()
                if json.loads(line).get('task_id') == '7fc158ab7b70'}
    assert {A.program({'count_basis': 'cells', 'scale_axes': 'both'})} == selected
    assert len({A.program(s.as_dict()) for s in A.prototype.SETTINGS}) == 6


def test_every_program_satisfies_native_rule_source_contract():
    from puzzle_generators.rule_wrap import wrap_rule
    for setting in A.prototype.SETTINGS:
        assert wrap_rule(A.program(setting.as_dict())).lstrip().startswith('(lambda')


@pytest.mark.parametrize('demos', range(2, 7))
def test_supported_counts_keep_distinct_lawful_matched_inputs(demos):
    shared = None
    for setting in A.prototype.SETTINGS:
        result = A.generate(0, setting.as_dict(), demos, 4)
        assert len(result['train']) == demos and len(result['test']) == 4
        pairs = result['train'] + result['test']
        grids = [p['input'] for p in pairs]
        assert len({A.prototype.digest(g) for g in grids}) == demos + 4
        assert all(GEN.self_check(g) == [] for g in grids)
        assert shared is None or grids == shared
        shared = grids
        assert result['program_solution'] == A.program(setting.as_dict())
        assert all(p['output'] == A.prototype.predict(p['input'], setting) for p in pairs)
        assert all(1 <= len(p['output']) <= 30 and 1 <= len(p['output'][0]) <= 30 for p in pairs)
        assert A.prototype.counts(result['test'][0]['input']) == (6, 6)
        out = result['test'][0]['output']
        assert (len(out), len(out[0])) == {'both': (30, 30), 'rows': (30, 5), 'columns': (5, 30)}[setting.scale_axes]


def test_counts_are_independent_and_query_prefix_is_stable():
    settings = {'count_basis': 'colors', 'scale_axes': 'rows'}
    short = A.generate(17, settings, 2, 1)
    longer = A.generate(17, settings, 2, 4)
    more_demos = A.generate(17, settings, 6, 4)
    assert short['train'] == longer['train'] == more_demos['train'][:2]
    assert short['test'] == longer['test'][:1]
    assert longer['test'] == more_demos['test']
    assert A.generate(17, settings, 2, 4) == longer


@pytest.mark.parametrize('seed,demos,queries', [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, 1.0)])
def test_invalid_native_requests_fail_explicitly(seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        A.generate(seed, {'count_basis': 'cells', 'scale_axes': 'both'}, demos, queries)


@pytest.mark.parametrize('settings', [{}, {'count_basis': 'cells'}, {'count_basis': 'cells', 'scale_axes': 'both', 'extra': 0}, {'count_basis': False, 'scale_axes': 'both'}, {'count_basis': 'cells', 'scale_axes': 'diagonal'}])
def test_settings_are_exact_and_never_defaulted(settings):
    with pytest.raises((TypeError, ValueError)):
        A.program(settings)


def test_two_demo_prefix_separates_all_declared_settings():
    for seed in (0, 17):
        grids = A.prototype.generate_inputs(seed, train=2, test=4)[:2]
        signatures = {json.dumps([A.prototype.predict(g, s) for g in grids])
                      for s in A.prototype.SETTINGS}
        assert len(signatures) == 6


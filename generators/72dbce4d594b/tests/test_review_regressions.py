"""Review regressions, runnable in the source tree without legacy imports."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import random
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('reviewed_generator', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_rejects_retained_seed_zero_ambiguity():
    case = json.loads((HOME / 'workspace/baseline_ambiguous_lesson.json').read_text())
    assert gen.lesson_identifiable(case['demos'], case['query']), (
        'identity and 180-degree rotation agree on the first domino demo, '
        'but differ on the query; this lesson must not pass')


def test_all_four_curriculum_profiles_reachable_for_each_seed():
    for seed in range(8):
        visited = {gen.schedule_profile(seed, i) for i in range(20)}
        assert visited == set(gen.SCHEDULE_PROFILES), (seed, visited)


def test_every_window_has_query_identifying_command_examples():
    for band in ('easy', 'medium', 'hard'):
        for seed in range(8):
            grids = [gen.generate(seed, i, difficulty=band) for i in range(15)]
            for start in range(8):
                n = gen.EXAMPLES_NEEDED
                demos = [{'input':g, 'output':gen.rule_mirror(g)} for g in grids[start:start+n]]
                query = {'input':grids[start+n]}
                assert gen.lesson_identifiable(demos, query) == [], (band, seed, start)
                # Independent four-command subset, including the previously missing rival.
                code = sum(v == 3 for row in query['input'] for v in row)
                for wrong in range(1, 5):
                    if wrong == code:
                        continue
                    def rival(g):
                        c = sum(v == 3 for row in g for v in row)
                        return gen._solve_with(g, transform=wrong) if c == code else gen.rule_mirror(g)
                    survives = all(rival(d['input']) == d['output'] for d in demos)
                    assert not survives or rival(query['input']) == gen.rule_mirror(query['input']), (band, seed, start, code, wrong)


def test_canonical_pairs_are_preserved():
    row = next(json.loads(line) for line in (REPO / 'shared/data/canonical/puzzles.jsonl').open()
               if json.loads(line).get('task_id') == gen.TASK_ID)
    pairs = row['train'] + row['test']
    assert len(pairs) == 5
    for pair in pairs:
        assert not gen.self_check(pair['input'])
        assert not gen.strict_canonical_like(pair['input'])
        assert gen.rule_mirror(pair['input']) == pair['output']


def test_determinism_and_nonmutation():
    state = random.getstate()
    for index in range(10):
        g = gen.generate(23, index, difficulty='hard')
        untouched = copy.deepcopy(g)
        assert g == gen.generate(23, index, difficulty='hard')
        gen.observe_overrides(g)
        gen.rule_mirror(g)
        assert g == untouched
    assert random.getstate() == state


@pytest.mark.parametrize('profile', ['canonical_234', 'spread_246', 'wide_358'])
@pytest.mark.parametrize('rank', [1, 2, 3])
@pytest.mark.parametrize('transform', [1, 2, 3, 4])
def test_legacy_size_overrides_remain_exact(profile, rank, transform):
    g = gen.generate(42, 7, size_profile=profile, rank=rank, transform=transform)
    got = gen.observe_overrides(g)
    assert got['size_profile'] == profile
    assert got['rank'] == rank
    assert got['transform'] == transform
    assert gen.self_check(g) == []


def _probe():
    spec = importlib.util.spec_from_file_location('probe', HOME / 'workspace/instruction_table_probe.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_rejects_real_baseline_case():
    case = json.loads((HOME / 'workspace/baseline_ambiguous_lesson.json').read_text())
    report = _probe().analyze(case['demos'], [case['query']])
    assert not report['passed']
    assert report['queries'][0]['distinct_predictions'] > 1


def test_probe_accepts_rule_ambiguity_when_query_answers_agree():
    report = _probe().factorized_gate([{'input':0,'output':[[0]]}], [{'input':1}],
              key=lambda g:0, predictors={'a':lambda g:[[0]],'b':lambda g:[[0]]})
    assert report['passed']
    assert len(report['queries'][0]['survivors']) == 2


def test_probe_does_not_hide_empty_hypothesis_class_or_exceptions():
    probe = _probe()
    result = probe.factorized_gate([{'input':0,'output':[[9]]}], [{'input':1}],
              key=lambda g:0, predictors={'a':lambda g:[[0]]})
    assert not result['passed']
    def raises(g):
        raise ValueError('probe failure')
    result = probe.factorized_gate([], [{'input':1}], key=lambda g:0,
                                 predictors={'a':lambda g:[[0]],'b':raises})
    assert not result['passed'] and result['errors']


@pytest.mark.parametrize('size', [4,5,6,7,8])
def test_asymmetric_sampler_separates_all_eight_orientations(size):
    for seed in range(24):
        cells = gen._grow_polyomino(random.Random(seed), size, require_asymmetric=True)
        assert len(cells) == size
        assert len({tuple(gen._d4(cells,v)) for v in range(8)}) == 8


def test_exactly_one_canonical_and_four_teaching_slots_per_window():
    for seed in range(12):
        for start in range(10):
            grids = [gen.generate(seed,start+i) for i in range(5)]
            canonical = [g for g in grids if not gen.strict_canonical_like(g)]
            teaching = [g for g in grids if gen.strict_canonical_like(g)]
            assert len(canonical) == 1
            assert len(teaching) == 4
            assert {sum(v==3 for row in g for v in row) for g in teaching} == {1,2,3,4}
            for g in teaching:
                for shape in gen._components(g,1):
                    assert gen._asymmetric(shape)


def test_inconsistent_unqueried_instruction_still_rejects_lesson():
    report = _probe().factorized_gate([{'input':0,'output':[[9]]}], [{'input':1}],
              key=lambda g:g, predictors={'a':lambda g:[[0]]})
    assert not report['passed']
    assert report['inconsistent_controls'] == ['0']

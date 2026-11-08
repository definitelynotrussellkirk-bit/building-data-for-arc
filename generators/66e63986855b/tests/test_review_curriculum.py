"""Portable regression contract for the October 4 row-front curriculum repair.

Run via run_with_racket.py or the public task_tests stage. These tests do not
change the retained root fixtures and use no private scripts namespace.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = '66e63986855b'
ROOT = find_root(__file__)
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
if not SOURCE.exists():
    SOURCE = ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py'
SPEC = importlib.util.spec_from_file_location('reviewed_rowfront', SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
BANDS = ('easy', 'medium', 'hard')


def half_copy(grid, upper=True):
    """Independent rival: copy one output half across the occupied vertical span."""
    output = GEN.rule_mirror(grid)
    rows = [r for r, row in enumerate(grid) if any(row)]
    top, bottom = min(rows), max(rows)
    original = copy.deepcopy(output)
    for r in range(top, bottom + 1):
        source = min(r, top + bottom - r) if upper else max(r, top + bottom - r)
        output[r] = list(original[source])
    return output


@pytest.mark.parametrize('band', BANDS)
def test_every_band_emits_each_canonical_canvas_size(band):
    wanted = {(len(p['input']), len(p['input'][0]))
              for p in canonical_pairs(TASK, root=ROOT)}
    found = {(len(g), len(g[0])) for i in range(120)
             for g in [GEN.generate(101, i, difficulty=band)]}
    assert wanted <= found, f'{band}: missing canonical canvas sizes {wanted-found}'


@pytest.mark.parametrize('band', BANDS)
def test_width_six_is_a_real_exact_axis_in_every_morphology_and_placement(band):
    for profile in GEN.PROFILES:
        for placement in GEN.PLACEMENTS:
            kw = dict(grid_h=6, grid_w=6, color=4, profile=profile, placement=placement)
            g = GEN.generate(23, 11, difficulty=band, **kw)
            assert GEN.observe_overrides(g) == kw
            assert GEN.self_check(g) == []


@pytest.mark.parametrize('band', BANDS)
def test_all_six_cyclic_starts_and_rotations_refute_half_copy(band):
    # Each four-pair bundle may hold out any one pair. One witness is NOT enough:
    # it could itself be the query. Test all starts of the joint 2x3 schedule.
    for seed in range(12):
        grids = [GEN.generate(seed, i, difficulty=band) for i in range(9)]
        for start in range(6):
            pairs = [(g, GEN.rule_mirror(g)) for g in grids[start:start+4]]
            for holdout in range(4):
                for upper in (True, False):
                    demonstrations = [p for i, p in enumerate(pairs) if i != holdout]
                    assert any(half_copy(g, upper) != out for g, out in demonstrations), (
                        band, seed, start, holdout, 'upper' if upper else 'lower')


@pytest.mark.parametrize('overrides', [
    {'grid_h': True}, {'grid_h': 6.5}, {'grid_w': '8'}, {'color': False},
    {'color': 2.25}, {'grid_w': 5}, {'color': 0}, {'unknown': 1},
])
def test_bad_controls_fail_as_value_errors_without_silent_coercion(overrides):
    with pytest.raises(ValueError):
        GEN.generate(3, 7, **overrides)


def test_declared_contract_is_executable_and_canonical_shortcuts_really_fit():
    for name in ('strict_canonical_like', 'lesson_identifiable'):
        assert callable(getattr(GEN, name, None)), f'missing {name}'
    shortcuts = getattr(GEN, 'CANONICAL_SHORTCUTS', {})
    assert len(shortcuts) >= 2, 'Both plausible half-copy rules need explicit declarations'
    for pair in canonical_pairs(TASK, root=ROOT):
        assert GEN.strict_canonical_like(pair['input']) == []
        for name, rival in shortcuts.items():
            assert rival(pair['input']) == pair['output'], name
    assert set(shortcuts) <= set(GEN.LESSON_COMPETITORS)
    assert set(shortcuts) <= set(GEN.SEMANTIC_RIVALS)


def test_hooks_read_demo_labels_but_ignore_the_private_query_label():
    assert callable(getattr(GEN, 'lesson_identifiable', None)), 'missing lesson hook'
    demos = canonical_pairs(TASK, root=ROOT)
    query_input = GEN.generate(31, 3, profile='asymmetric_front')
    query = {'input': query_input, 'output': GEN.rule_mirror(query_input)}
    reasons = GEN.lesson_identifiable(demos, query)
    assert reasons, 'All canonical pairs leave the half-copy rule ambiguous on this query'
    poisoned = {'input': query_input, 'output': [[9]]}
    assert GEN.lesson_identifiable(demos, poisoned) == reasons
    witnessed = demos[:2] + [query]
    assert GEN.lesson_identifiable(witnessed, poisoned) == []
    assert GEN.lesson_identifiable(demos, {'input': demos[0]['input']}) == []


def test_witness_claims_are_real_and_rivals_are_input_pure():
    assert getattr(GEN, 'WITNESS_RIVALS', {}), 'missing rival-backed witnesses'
    counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for index in range(36):
        g = GEN.generate(607, index, difficulty=BANDS[index % 3])
        saved = copy.deepcopy(g)
        correct = GEN.rule_mirror(g)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(g):
                counts[name] += 1
                assert any(GEN.SEMANTIC_RIVALS[r](g) != correct
                           for r in GEN.WITNESS_RIVALS[name])
        for rival in GEN.LESSON_COMPETITORS.values():
            assert rival(g) == rival(g)
        assert g == saved
    assert all(counts.values()), counts


def test_selected_racket_text_is_exactly_canonical_not_just_normalized():
    row = next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
               if json.loads(line).get('task_id') == TASK)
    source = row['program_solution']
    base = ROOT / 'shared/data/base/solutions/training/bf32578f__66e63986855b.json'
    if not base.exists():
        base = ROOT / 'data/base/solutions/training/bf32578f__66e63986855b.json'
    target = json.loads(base.read_text())['racket_target']
    assert target['raw_code'] == source
    assert target['target_code'] == source
    assert GEN.RULE_HASH == hashlib.sha256(' '.join(source.split()).encode()).hexdigest()[:12]


@pytest.mark.parametrize('band,start', [('easy', 0), ('medium', 17), ('hard', 22)])
def test_replay_of_original_ambiguous_lesson_draws_is_now_distinguished(band, start):
    pairs = [{'input': GEN.generate(0, start+i, difficulty=band)} for i in range(4)]
    for p in pairs:
        p['output'] = GEN.rule_mirror(p['input'])
    for query in range(4):
        demos = [p for i, p in enumerate(pairs) if i != query]
        assert GEN.lesson_identifiable(demos, pairs[query]) == []


def test_keyed_draw_provenance_matches_the_returned_axes(monkeypatch):
    recorded = []
    real_factory = GEN.gen_ctx
    def record_context(**kwargs):
        context = real_factory(**kwargs)
        recorded.append(context)
        return context
    monkeypatch.setattr(GEN, 'gen_ctx', record_context)
    for band in BANDS:
        for index in range(12):
            grid = GEN.generate(17, index, difficulty=band)
            drawn = recorded[-1].drawn_store
            assert {name: drawn[name] for name in GEN.AXES} == GEN.observe_overrides(grid)

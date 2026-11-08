"""Regression tests for canonical-compatible instruction deduplication."""
import importlib

import pytest
from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module('puzzle_generators.per_puzzle.b6592c220670.generator')


def test_canonical_shortcut_declarations_fit_every_usable_pair():
    pairs = canonical_pairs(gen.TASK_ID)
    assert pairs
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input']) == p['output'] for p in pairs), name


def test_duplicate_removal_is_declared_and_bound_to_a_witness():
    name = 'deduplicate_script'
    assert name in gen.CANONICAL_SHORTCUTS
    assert name in gen.LESSON_COMPETITORS
    assert name in gen.SEMANTIC_RIVALS
    assert any(name in rivals for rivals in gen.WITNESS_RIVALS.values())


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_all_eight_cyclic_starts_include_a_repeat_in_four_demos(band):
    for seed in range(23000, 23013):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(12)]
        for start in range(8):
            demos = grids[start:start + 4]
            assert any(len(gen._script(g)) > len(set(gen._script(g))) for g in demos), (band, seed, start)


def test_general_script_repetitions_are_not_limited_to_one_code():
    repeated = set()
    for index in range(512):
        codes = gen._script(gen.generate(18731, index, difficulty='hard'))
        repeated.update(code for code in codes if codes.count(code) > 1)
    assert repeated == {1, 2, 3, 4}


def test_deduplication_changes_panel_count_not_only_pixels():
    assert 'deduplicate_script' in gen.CANONICAL_SHORTCUTS
    # Shape and colors are deliberately simple; the lost panel is decisive.
    grid = [[2, 0, 2, 0, 3, 0, 0, 0, 0], [0] * 9,
            [7, 0, 0, 0, 0, 0, 0, 0, 0],
            [7, 0, 0, 0, 0, 0, 0, 0, 0],
            [7, 8, 0, 0, 0, 0, 0, 0, 0], [0] * 9, [0] * 9]
    assert gen.self_check(grid) == []
    intended = gen.rule_mirror(grid)
    rival = gen.CANONICAL_SHORTCUTS['deduplicate_script'](grid)
    assert len(rival[0]) < len(intended[0])
    assert gen.SEMANTIC_WITNESSES['repeated_instruction_is_executed'](grid)


def test_every_witness_has_a_named_executable_rival():
    for witness in gen.SEMANTIC_WITNESSES:
        assert gen.WITNESS_RIVALS.get(witness), witness
        for rival in gen.WITNESS_RIVALS[witness]:
            assert callable(gen.SEMANTIC_RIVALS[rival]), (witness, rival)


def test_regression_order_ambiguity_easy_seed_23008_start_5():
    pairs = []
    for index in range(5, 10):
        grid = gen.generate(23008, index, difficulty='easy')
        pairs.append({'input': grid, 'output': gen.rule_mirror(grid)})
    assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
    assert any(gen.SEMANTIC_RIVALS['reverse_script'](d['input']) != d['output'] for d in pairs[:4])


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_every_cyclic_lesson_refutes_every_declared_competitor(band):
    for seed in range(23000, 23013):
        pairs = []
        for index in range(12):
            grid = gen.generate(seed, index, difficulty=band)
            pairs.append({'input': grid, 'output': gen.rule_mirror(grid)})
        for start in range(8):
            demos, query = pairs[start:start + 4], pairs[start + 4]
            assert gen.lesson_identifiable(demos, query) == [], (seed, start)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(d['input']) != d['output'] for d in demos), (band, seed, start, name)

"""Behavioral regressions for the header-count sampler, portable to review runtimes."""
from __future__ import annotations

import importlib.util
from itertools import product

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "cb439f1b5f4a"
ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("header_repeat_under_test", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def expected(grid):
    """Independent row-slice oracle; canonical labels check this test helper."""
    occupied = [(r, c) for r in range(1, len(grid))
                for c, value in enumerate(grid[r]) if value != 0]
    top, bottom = min(r for r, _ in occupied), max(r for r, _ in occupied)
    left, right = min(c for _, c in occupied), max(c for _, c in occupied)
    count = grid[0].count(1)
    result = []
    for row in grid[top:bottom + 1]:
        crop = row[left:right + 1]
        result.append((crop + [0]) * (count - 1) + crop)
    return result


def test_canonical_labels_and_domain():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert expected(pair["input"]) == pair["output"]


@pytest.mark.parametrize("grid,want", [
    ([[1, 0, 0], [0, 4, 0]], [[4]]),
    ([[1, 1, 0, 0], [0, 4, 1, 0], [0, 0, 3, 0]],
     [[4, 1, 0, 4, 1], [0, 3, 0, 0, 3]]),
    ([[1, 0, 1], [0, 1, 0], [0, 0, 0]], [[1, 0, 1]]),
    ([[1, 1, 0], [1, 1, 0], [0, 0, 0]], [[1, 1, 0, 1, 1]]),
])
def test_lawful_singletons_blue_and_multicolor_are_preserved(grid, want):
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert expected(grid) == want


@pytest.mark.parametrize("grid", [
    [], [[]], [[1, 1], [0]],
    [[True, 1, 0], [0, 4, 4]],
    [[1, 1, 0], [0, 4.0, 4]],
    [[1, 1, 0], [0, 10, 4]],
    [[1, 1, 4], [0, 4, 4]],
    [[0, 0, 0], [0, 4, 4]],
    [[1, 1, 0], [0, 0, 0]],
    [[1, 1, 0, 0], [4, 0, 0, 1]],
    [[1] * 31, [4] * 31],
])
def test_validator_rejects_malformed_or_out_of_domain_grids(grid):
    assert GEN.self_check(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("texture", ["solid", "notched", "multicolor", "blue_motif"])
def test_all_exact_controls_survive_each_curriculum_phase(band, texture):
    for phase, color, count in product(range(5), (2, 9), (1, 4)):
        controls = dict(grid_h=4, grid_w=6, K=count,
                        prototype_color=color, texture=texture)
        grid = GEN.generate(17, phase, difficulty=band, **controls)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == controls
        assert max(len(row) for row in expected(grid)) <= 30


@pytest.mark.parametrize("controls", [
    {"unknown_control": 2}, {"grid_h": 6.5}, {"grid_h": "6"},
    {"grid_h": True}, {"grid_w": 16}, {"K": 0}, {"K": 2.0},
    {"prototype_color": 1}, {"prototype_color": False},
    {"texture": "unrecognized"}, {"texture": "no_prototype"},
])
def test_invalid_overrides_fail_loudly(controls):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **controls)


def test_observer_reports_absent_primary_color_for_lawful_blue_only_body():
    grid = [[1, 0, 1], [0, 1, 0], [0, 0, 0]]
    assert GEN.observe_overrides(grid) == {
        "grid_h": 3, "grid_w": 3, "K": 2,
        "prototype_color": None, "texture": "blue_motif",
    }


def test_output_cap_is_checked_even_when_input_dimensions_are_legal():
    assert GEN.self_check([[1, 1, 1, 1, 0, 0, 0], [4, 4, 4, 4, 4, 4, 0]]) == []
    assert GEN.self_check([[1, 1, 1, 1, 0, 0, 0], [4, 4, 4, 4, 4, 4, 4]])
    controls = dict(grid_h=12, grid_w=15, K=4, prototype_color=9, texture="blue_motif")
    grid = GEN.generate(17, 4, difficulty="easy", **controls)
    assert GEN.observe_overrides(grid) == controls
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_profile_floor_and_diversity(band):
    draws = [GEN.generate(19, i, difficulty=band) for i in range(100)]
    profiles = [(len(g), len(g[0]), len({v for row in g for v in row})) for g in draws]
    for start in range(0, 100, 20):
        assert sum(p in {(4, 6, 3), (4, 7, 3)} for p in profiles[start:start + 20]) >= 8
    assert all(GEN.self_check(g) == [] for g in draws)
    assert len({str(g) for g in draws}) >= 90
    assert draws == [GEN.generate(19, i, difficulty=band) for i in range(100)]


def test_canonical_shortcuts_are_real_and_have_generated_counterexamples():
    canonical = canonical_pairs(TASK_ID, root=ROOT)
    assert GEN.CANONICAL_SHORTCUTS
    generated = [GEN.generate(seed, i, difficulty="medium")
                 for seed in range(4) for i in range(10)]
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(p["input"]) == p["output"] for p in canonical), name
        assert any(rival(g) != expected(g) for g in generated), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_start_and_query_rotation_teaches_declared_rivals(band):
    for seed in range(8):
        pairs = [{"input": GEN.generate(seed, i, difficulty=band)} for i in range(9)]
        for pair in pairs:
            pair["output"] = expected(pair["input"])
        for start in range(5):
            window = pairs[start:start + 5]
            for query_index in range(5):
                query = window[query_index]
                demos = window[:query_index] + window[query_index + 1:]
                assert GEN.lesson_identifiable(demos, query) == [], (seed, start, query_index)
                rivals = {**GEN.CANONICAL_SHORTCUTS, **GEN.LESSON_COMPETITORS}
                for name, rival in rivals.items():
                    assert (rival(query["input"]) == query["output"] or
                            any(rival(p["input"]) != p["output"] for p in demos)), (
                                seed, start, query_index, name)


def test_semantic_witnesses_refute_their_declared_rivals():
    fired = set()
    for seed, index in product(range(8), range(5)):
        grid = GEN.generate(seed, index)
        label = expected(grid)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                fired.add(name)
                assert any(GEN.SEMANTIC_RIVALS[rival](grid) != label
                           for rival in GEN.WITNESS_RIVALS[name]), name
    assert fired == set(GEN.SEMANTIC_WITNESSES)

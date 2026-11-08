"""Behavioral regressions; valid both in the library and staged task runtime."""
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "17f92e205b34"


@pytest.fixture(scope="module")
def generator():
    root = find_root(__file__)
    candidates = [root / "generators" / TASK_ID / "generator.py",
                  root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"]
    path = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("reflection_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def reference_formula(grid):
    # Test oracle only. Canonical and census labels are obtained from Racket.
    return [[grid[c][r] or grid[r][c] for c in range(len(grid))]
            for r in range(len(grid))]


def facts(grid):
    cells = [(r, c, v) for r, row in enumerate(grid)
             for c, v in enumerate(row) if v]
    return {"size": len(grid), "markers": len(cells),
            "palette_size": len({v for _, _, v in cells}),
            "diagonal_markers": sum(r == c for r, c, _ in cells)}


def test_validator_accepts_every_canonical_input(generator, canonical):
    for pair in canonical:
        assert generator.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])
        assert reference_formula(pair["input"]) == pair["output"]


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[0, 1], [0]], [None, [0, 1]],
    [[0] * 5 for _ in range(6)], [[0] * 6 for _ in range(5)],
    [[0, 10], [0, 0]], [[0, True], [0, 0]],
    [[0, 1.0], [0, 0]], [[0, "2"], [0, 0]],
    [[0, 0], [0, 0]], [[1, 0], [0, 2]], [[1, 1], [1, 1]],
    [[0, 2], [3, 0]],
])
def test_validator_rejects_malformed_or_unsupported_inputs_without_crashing(generator, grid):
    try:
        errors = generator.self_check(grid, meta={"texture": "full_grid"})
    except Exception as exc:
        pytest.fail(f"validator raised {type(exc).__name__}: {exc}")
    assert isinstance(errors, list) and errors


def test_matching_prefilled_pairs_are_lawful_with_an_unmatched_source(generator):
    grid = [[0] * 6 for _ in range(6)]
    grid[1][3] = grid[3][1] = 2
    grid[5][2] = 7
    grid[4][4] = 4
    assert generator.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("overrides", [
    {"size": 6, "markers": 3, "palette_size": 2, "diagonal_markers": 2},
    {"size": 16, "markers": 12, "palette_size": 3, "diagonal_markers": 0},
    {"size": 6, "markers": 12, "palette_size": 1, "diagonal_markers": 1},
    {"size": 7, "markers": 4, "palette_size": 3, "diagonal_markers": 2},
])
def test_exact_controls_are_recoverable_from_pixels(generator, band, overrides):
    for seed in range(3):
        grid = generator.generate(seed, seed + 4, difficulty=band, **overrides)
        assert generator.self_check(grid) == []
        assert facts(grid) == overrides
        assert generator.observe_overrides(grid) == overrides


@pytest.mark.parametrize("name,value", [
    ("unknown_axis", 1), ("grid_h", 6), ("grid_w", 6),
    ("palette_kind", "warm"), ("anchor_corner", True),
    ("asymmetry_force", True), ("texture", "empty_grid"),
])
def test_retired_or_unknown_controls_raise_instead_of_silently_changing_nothing(generator, name, value):
    with pytest.raises(ValueError, match="unknown|retired"):
        generator.generate(0, 0, **{name: value})


@pytest.mark.parametrize("overrides", [
    {"markers": 3.5}, {"markers": "3"}, {"markers": True},
    {"palette_size": 2.0}, {"diagonal_markers": False},
    {"size": 5}, {"size": 17}, {"markers": 2}, {"markers": 13},
    {"palette_size": 0}, {"palette_size": 4}, {"diagonal_markers": 3},
])
def test_invalid_controls_raise(generator, overrides):
    with pytest.raises((ValueError, TypeError)):
        generator.generate(0, 0, **overrides)


def test_invalid_difficulty_raises(generator):
    with pytest.raises(ValueError, match="difficulty"):
        generator.generate(0, 0, difficulty="typo")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_has_canonical_profiles_and_both_directions(generator, band):
    observed = set()
    profiles = 0
    for index in range(64):
        grid = generator.generate(17, index, difficulty=band)
        assert generator.self_check(grid) == []
        assert generator.strict_canonical_like(grid) == []
        off = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v and r != c]
        upper, lower = any(r < c for r, c in off), any(r > c for r, c in off)
        observed.add((upper, lower))
        obs = facts(grid)
        profiles += obs["size"] in (6, 7) and obs["palette_size"] == 2
        assert grid == generator.generate(17, index, difficulty=band)
    assert {(True, False), (False, True), (True, True)} <= observed
    assert profiles >= 16


def test_shortcuts_really_fit_canonical_examples(generator, canonical):
    shortcuts = getattr(generator, "CANONICAL_SHORTCUTS", {})
    assert len(shortcuts) >= 2
    for name, rival in shortcuts.items():
        for pair in canonical:
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_core_profile_mass_is_independent_of_teaching_role(generator, band):
    for index in (0, 2, 4, 6):
        grid = generator.generate(0, index, difficulty=band)
        observed = facts(grid)
        assert observed["size"] in (6, 7)
        assert observed["palette_size"] == 2


def test_teaching_anchor_distinguishes_the_anti_diagonal_rival(generator):
    # Actual failing draw from the intermediate implementation, not a mock.
    grid = generator.generate(435, 1, difficulty="medium", size=7,
                              markers=5, palette_size=1, diagonal_markers=1)
    assert generator.LESSON_COMPETITORS["anti_diagonal"](grid) != reference_formula(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_declared_witnesses_refute_their_rivals_on_the_same_grid(generator, band):
    witnesses = getattr(generator, "SEMANTIC_WITNESSES", {})
    assert witnesses
    hits = {name: 0 for name in witnesses}
    for index in range(32):
        grid = generator.generate(29, index, difficulty=band)
        label = reference_formula(grid)
        if index % 4 < 2:
            assert all(rival(grid) != label for rival in generator.LESSON_COMPETITORS.values())
        for name, predicate in witnesses.items():
            if predicate(grid):
                hits[name] += 1
                assert any(generator.SEMANTIC_RIVALS[rival](grid) != label
                           for rival in generator.WITNESS_RIVALS[name]), name
    assert all(hits.values()), hits


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_demonstrations_survive_every_query_rotation_of_schedule_windows(generator, band):
    competitors = getattr(generator, "LESSON_COMPETITORS", {})
    assert competitors
    for seed in range(3):
        for start in range(4):
            grids = [generator.generate(seed, start + i, difficulty=band) for i in range(4)]
            labels = [reference_formula(grid) for grid in grids]
            for query in range(4):
                for name, rival in competitors.items():
                    if all(rival(grids[i]) == labels[i] for i in range(4) if i != query):
                        assert rival(grids[query]) == labels[query], (seed, start, query, name)

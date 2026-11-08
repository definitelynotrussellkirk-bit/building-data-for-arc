from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_f65705efd235", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

TASK_ID = "f65705efd235"


def _canonical_record():
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise AssertionError(f"canonical record {TASK_ID} not found")


def _as_int_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def _canonical_pairs():
    record = _canonical_record()
    pairs = [*record["train"], record["test"]]
    return [
        {"input": _as_int_grid(pair["input"]), "output": _as_int_grid(pair["output"])}
        for pair in pairs
    ]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_metadata_rule_mirror_and_self_check_accept_all_canonical_pairs():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "635fcfe4fd6f"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_rects"}
    for pair in _canonical_pairs():
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [7, 24])
@pytest.mark.parametrize("grid_w", [7, 24])
@pytest.mark.parametrize("n_rects", [2, 6])
def test_boundary_override_cross_is_exact_and_lawful(
    difficulty, grid_h, grid_w, n_rects
):
    overrides = {"grid_h": grid_h, "grid_w": grid_w, "n_rects": n_rects}
    grid = GEN.generate(314159, 2718, difficulty=difficulty, **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid, meta={"overrides": overrides}) == []


def test_invalid_difficulty_types_ranges_and_unknown_overrides_fail_loudly():
    invalid = (
        {"difficulty": "expert"},
        {"grid_h": 6},
        {"grid_h": 25},
        {"grid_w": 6},
        {"grid_w": 25},
        {"n_rects": 1},
        {"n_rects": 7},
        {"n_rects": True},
        {"palette_kind": "warm"},
        {"__override_contract_unknown_axis__": 1},
    )
    for kwargs in invalid:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 1, **kwargs)


def test_four_sample_schedule_teaches_every_declared_semantic_distinction():
    profiles = []
    counts = []
    witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    rival_refutations = {name: 0 for name in GEN.SEMANTIC_RIVALS}
    for index in range(4):
        grid = GEN.generate(5000, index, difficulty="medium")
        assert GEN.self_check(grid) == []
        profiles.append(GEN.schedule_profile(5000, index, difficulty="medium"))
        counts.append(GEN.observe_overrides(grid)["n_rects"])
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            witness_hits[name] += int(bool(witness(grid)))
        expected = GEN.rule_mirror(grid)
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            rival_refutations[name] += int(rival(grid) != expected)
    assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
    assert 2 in counts
    assert any(count > 2 for count in counts)
    assert all(hits > 0 for hits in witness_hits.values()), witness_hits
    assert all(hits > 0 for hits in rival_refutations.values()), rival_refutations


def test_every_three_example_sliding_window_is_identifiable():
    pairs = []
    for index in range(9):
        grid = GEN.generate(8000, index, difficulty="hard")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    for start in range(6):
        demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
        query = pairs[start + GEN.EXAMPLES_NEEDED]
        assert GEN.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_structural_impostors():
    valid = GEN.generate(99, 3, difficulty="medium", grid_h=9, grid_w=10, n_rects=2)
    analysis = GEN._analysis(valid)
    assert analysis["errors"] == []
    first = analysis["rectangles"][0]

    partial = copy.deepcopy(valid)
    r, c = first["corners"][0]
    partial[r][c] = 0
    assert any("exactly 4" in error for error in GEN.self_check(partial))

    fifth = copy.deepcopy(valid)
    color = first["color"]
    candidate = next(
        (r, c)
        for r in range(len(fifth))
        for c in range(len(fifth[0]))
        if fifth[r][c] == 0 and (r, c) not in first["corners"]
    )
    fifth[candidate[0]][candidate[1]] = color
    assert any("exactly 4" in error for error in GEN.self_check(fifth))

    non_corner = copy.deepcopy(valid)
    old_r, old_c = first["corners"][0]
    non_corner[old_r][old_c] = 0
    replacement = next(
        (r, c)
        for r in range(len(non_corner))
        for c in range(len(non_corner[0]))
        if non_corner[r][c] == 0
        and r not in first["rows"]
        and c not in first["cols"]
    )
    non_corner[replacement[0]][replacement[1]] = color
    assert any(
        "two rows" in error or "four rectangle corners" in error
        for error in GEN.self_check(non_corner)
    )


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(77, 11, difficulty="hard")
    middle = random.getstate()
    second = GEN.generate(77, 11, difficulty="hard")
    after = random.getstate()
    assert _freeze(first) == _freeze(second)
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after


@pytest.mark.parametrize(
    ("seed", "sample_index"),
    [(17911100, 36963), (18101156, 37851)],
)
def test_every_scene_keeps_a_visible_hollow_interior_counterexample(seed, sample_index):
    """Regression: extra rectangles must not erase the outline-vs-fill lesson."""
    grid = GEN.generate(seed, sample_index, difficulty="easy")
    assert GEN.SEMANTIC_WITNESSES["strict_interior_stays_background"](grid)
    assert GEN.SEMANTIC_RIVALS["fill_each_rectangle_solid"](grid) != GEN.rule_mirror(grid)

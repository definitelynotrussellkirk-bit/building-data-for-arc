from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK = "b35816e8388b"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK}", ROOT / "generators" / TASK / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_row():
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError("canonical row missing")


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return row["train"] + (test if isinstance(test, list) else [test])


def endpoint_facts(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4]
    assert len(points) == 2
    (r1, c1), (r2, c2) = points
    dr, dc = r2 - r1, c2 - c1
    if dr == 0:
        orientation = "horizontal"
    elif dc == 0:
        orientation = "vertical"
    elif dr * dc > 0:
        orientation = "diag_down"
    else:
        orientation = "diag_up"
    return {
        "orientation": orientation,
        "span_steps": max(abs(dr), abs(dc)),
        "midpoint": ((r1 + r2) // 2, (c1 + c2) // 2),
    }


def test_rule_hash_and_canonical_pairs_are_exact():
    row = canonical_row()
    source = row["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == digest == "259314225434"
    for pair in canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_declared_axes_are_real_geometry_controls_and_unknown_keys_fail_closed():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "orientation", "span_steps"}
    assert GEN.AXES["orientation"]["type"] == "str"
    assert GEN.AXES["orientation"]["valid"] == "horizontal|vertical|diag_down|diag_up"
    assert GEN.AXES["span_steps"]["valid"] == "2|4|6|8|10|12"
    with pytest.raises(ValueError):
        GEN.generate(1, 0, typo_axis=7)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, difficulty="expert")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 5, "grid_w": 14, "orientation": "horizontal", "span_steps": 12},
        {"grid_h": 14, "grid_w": 5, "orientation": "vertical", "span_steps": 12},
        {"grid_h": 14, "grid_w": 14, "orientation": "diag_down", "span_steps": 12},
        {"grid_h": 14, "grid_w": 14, "orientation": "diag_up", "span_steps": 12},
        {"grid_h": 5, "grid_w": 5, "orientation": "horizontal", "span_steps": 4},
    ],
)
def test_exact_overrides_are_observable_and_rule_valid(kwargs):
    grid = GEN.generate(91, 13, **kwargs)
    assert len(grid) == kwargs["grid_h"]
    assert len(grid[0]) == kwargs["grid_w"]
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert observed == kwargs
    assert endpoint_facts(grid)["midpoint"] == next(
        (r, c)
        for r, row in enumerate(GEN.rule_mirror(grid))
        for c, value in enumerate(row)
        if value == 8
    )


def test_incompatible_exact_geometry_is_rejected_not_silently_clamped():
    with pytest.raises(ValueError):
        GEN.generate(
            1,
            0,
            grid_h=5,
            grid_w=5,
            orientation="diag_down",
            span_steps=12,
        )


def test_three_example_schedule_always_contains_strict_and_off_center_evidence():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(15):
            grids = [GEN.generate(700 + start, start + offset, difficulty=difficulty) for offset in range(3)]
            assert any(GEN.strict_canonical_like(grid) == [] for grid in grids)
            assert any(GEN.SEMANTIC_WITNESSES["off_grid_center"](grid) for grid in grids)
            demos = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
            query_grid = GEN.generate(900 + start, start + 3, difficulty=difficulty)
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_fixed_center_shortcut_fits_canonical_but_generated_witness_refutes_it():
    rival = GEN.CANONICAL_SHORTCUTS["fixed_grid_center"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    for difficulty in ("easy", "medium", "hard"):
        witnessed = [
            GEN.generate(12_000 + seed, seed, difficulty=difficulty)
            for seed in range(30)
        ]
        counterexamples = [
            grid
            for grid in witnessed
            if GEN.SEMANTIC_WITNESSES["off_grid_center"](grid)
        ]
        assert counterexamples
        assert all(rival(grid) != GEN.rule_mirror(grid) for grid in counterexamples)


def test_default_distribution_covers_all_orientations_and_even_spans():
    grids = [GEN.generate(30_000 + seed, seed, difficulty="hard") for seed in range(360)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert {item["orientation"] for item in observed} == set(GEN.ORIENTATIONS)
    assert {item["span_steps"] for item in observed} == set(GEN.SPAN_STEPS)
    assert all(GEN.self_check(grid) == [] for grid in grids)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(777)
    state = random.getstate()
    first = GEN.generate(123, 45, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123, 45, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(123, 45, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0] * 5 for _ in range(4)],
        [[False] * 5 for _ in range(5)],
        [[10] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(5)],
        [[0, 0, 4, 0, 0], [0, 0, 0], [0, 0, 4, 0, 0]],
    ],
)
def test_malformed_and_out_of_domain_grids_fail_closed(grid):
    assert GEN.self_check(grid)

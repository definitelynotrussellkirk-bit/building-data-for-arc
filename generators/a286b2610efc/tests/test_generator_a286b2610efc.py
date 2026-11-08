"""Focused contract tests for the complete-straight-segments generator."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "a286b2610efc"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_pairs() -> list[dict]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                test = row["test"]
                return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))
    raise AssertionError(f"canonical row not found for {TASK_ID}")


def _lesson(seed: int, start: int, difficulty: str):
    demos = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty)
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def _blank(height: int = 7, width: int = 8):
    return [[0 for _ in range(width)] for _ in range(height)]


def test_rule_pin_and_all_canonical_pairs_are_owned_exactly():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "2e117d692607"
    pairs = _canonical_pairs()
    assert len(pairs) == 3

    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.observe_overrides(pair["input"])["layout"] == "edge"
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_default_schedule_teaches_one_sided_and_two_sided_completion_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(6):
            demos, query = _lesson(8100 + start, start, difficulty)
            layouts = {GEN.observe_overrides(demo["input"])["layout"] for demo in demos}
            assert layouts == {"edge", "interior"}
            assert GEN.lesson_identifiable(demos, query) == []

        edge = GEN.generate(99, 0, difficulty=difficulty, layout="edge")
        interior = GEN.generate(99, 0, difficulty=difficulty, layout="interior")
        assert sum(value != 0 for row in edge for value in row) == 4
        assert sum(value != 0 for row in GEN.rule_mirror(edge) for value in row) == 6
        assert sum(value != 0 for row in interior for value in row) == 4
        assert sum(value != 0 for row in GEN.rule_mirror(interior) for value in row) == 8


def test_exact_override_boundaries_are_observable_in_every_band():
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (7, 8, 9):
            for grid_w in (8, 9, 10):
                for layout in ("edge", "interior"):
                    requested = {"grid_h": grid_h, "grid_w": grid_w, "layout": layout}
                    grid = GEN.generate(9200 + case, case, difficulty=difficulty, **requested)
                    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": requested}) == []
                    assert GEN.observe_overrides(grid) == requested
                    case += 1


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"unknown_axis": 1}, "unknown override"),
        ({"grid_h": 6}, "grid_h"),
        ({"grid_w": 11}, "grid_w"),
        ({"layout": "mixed"}, "layout"),
        ({"difficulty": "extreme"}, "difficulty"),
    ],
)
def test_invalid_generation_requests_fail_loudly(kwargs, match):
    with pytest.raises((TypeError, ValueError), match=match):
        GEN.generate(1, 0, **kwargs)


def test_declared_shortcut_fits_every_canonical_pair_but_generated_interior_refutes_it():
    name = "one_sided_triplet_completion"
    shortcut = GEN.CANONICAL_SHORTCUTS[name]
    assert GEN.SEMANTIC_RIVALS[name] is shortcut
    assert GEN.LESSON_COMPETITORS[name] is shortcut
    assert name in GEN.WITNESS_RIVALS["two_sided_completion"]

    for pair in _canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = GEN.generate(1200, sample_index, difficulty=difficulty, layout="interior")
            assert GEN.SEMANTIC_WITNESSES["two_sided_completion"](grid)
            assert shortcut(grid) != GEN.rule_mirror(grid)


def test_self_check_rejects_minimal_impostors_and_interacting_motifs():
    singleton = _blank()
    singleton[2][2] = 3

    solid_2x2 = _blank()
    solid_2x2[2][2] = solid_2x2[2][3] = 3
    solid_2x2[3][2] = solid_2x2[3][3] = 4

    same_orientation = _blank()
    same_orientation[1][0] = same_orientation[1][1] = 3
    same_orientation[5][6] = same_orientation[5][7] = 4

    mixed_layout = _blank()
    mixed_layout[1][0] = mixed_layout[1][1] = 3
    mixed_layout[2][5] = mixed_layout[3][5] = 4

    overlap_footprints = _blank()
    overlap_footprints[3][2] = overlap_footprints[3][3] = 3
    overlap_footprints[1][4] = overlap_footprints[2][4] = 4

    for name, grid in {
        "empty": [],
        "blank": _blank(),
        "singleton": singleton,
        "solid_2x2": solid_2x2,
        "same_orientation": same_orientation,
        "mixed_layout": mixed_layout,
        "overlap_footprints": overlap_footprints,
        "ragged": [[0, 0], [0]],
        "out_of_range": [[10]],
    }.items():
        assert GEN.self_check(grid), name


def test_generation_is_deterministic_fresh_and_global_random_pure():
    random.seed(314159)
    state = random.getstate()
    first = GEN.generate(12345, 7, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(12345, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_difficulty_bands_are_behaviorally_live_without_changing_the_grammar():
    for sample_index in range(8):
        grids = [
            GEN.generate(7319, sample_index, difficulty=difficulty)
            for difficulty in ("easy", "medium", "hard")
        ]
        normalized = {tuple(tuple(row) for row in grid) for grid in grids}
        assert len(normalized) == 3
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert len({GEN.observe_overrides(grid)["layout"] for grid in grids}) == 1

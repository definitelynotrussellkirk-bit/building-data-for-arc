from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GEN_PATH = ROOT / "generators" / "c0f52d961a7c" / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_generator_c0f52d961a7c", GEN_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

TASK_ID = "c0f52d961a7c"
CANONICAL_DIMS = {(6, 7), (7, 8), (8, 9)}


def _canonical_row() -> dict:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _normalized_rule_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def _pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _lesson(seed: int, start: int, difficulty: str) -> tuple[list[dict], dict]:
    demos = []
    for offset in range(GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, start + offset, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty)
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def test_rule_pin_and_all_canonical_pairs():
    row = _canonical_row()
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == _normalized_rule_hash(row["program_solution"])
    assert GEN.RULE_HASH == "0f51670bbbc2"

    for pair in _pairs():
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_four_example_schedule_covers_all_directions_at_canonical_scale():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(12):
            grids = [GEN.generate(seed, index, difficulty=difficulty) for index in range(4)]
            observed = [GEN.observe_overrides(grid) for grid in grids]
            assert {item["marker_color"] for item in observed} == {1, 2, 3, 4}
            assert {(item["grid_h"], item["grid_w"]) for item in observed} <= CANONICAL_DIMS
            assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)

            demos, query = _lesson(seed, 0, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []


def test_declared_overrides_are_exact_composable_observable_and_band_safe():
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (6, 9, 20):
            for grid_w in (7, 12, 22):
                for payload_size in (3, 5, 8):
                    for marker_color in (1, 2, 3, 4):
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "payload_size": payload_size,
                            "marker_color": marker_color,
                        }
                        grid = GEN.generate(
                            10_000 + case,
                            case % 17,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert GEN.self_check(grid) == []
                        assert GEN.observe_overrides(grid) == requested
                        case += 1

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(0, 0, bogus_axis=1)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="nightmare")


def test_semantic_witnesses_refute_every_claimed_rival():
    grids = [
        GEN.generate(seed, index, difficulty="medium")
        for seed in range(12)
        for index in range(8)
    ]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        candidates = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert candidates, witness_name
        for rival_name in rival_names:
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
                for grid in candidates
            ), (witness_name, rival_name)


def test_replay_is_deterministic_fresh_and_global_rng_neutral():
    random.seed(20260928)
    state = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_default_schedule_combines_canonical_anchors_with_broad_axis_support():
    anchors = [GEN.generate(7, index, difficulty="medium") for index in range(4)]
    assert {(len(grid), len(grid[0])) for grid in anchors} <= CANONICAL_DIMS

    exploration = [
        GEN.generate(20_260_000 + index, index, difficulty="medium")
        for index in range(4, 36)
    ]
    dimensions = {(len(grid), len(grid[0])) for grid in exploration}
    assert all(GEN.strict_canonical_like(grid) == [] for grid in exploration)
    assert any(dim not in CANONICAL_DIMS for dim in dimensions)
    assert max(h for h, _ in dimensions) >= 15
    assert max(w for _, w in dimensions) >= 17

"""Regression tests for the 9db8deba5903 four-rotation tiling curriculum."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

TASK_ID = "9db8deba5903"
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
                return list(row["train"]) + list(row["test"])
    raise AssertionError(f"canonical row not found for {TASK_ID}")


def _lesson(seed: int, start: int, difficulty: str):
    demos = []
    for index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty)
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def test_rule_pin_and_every_canonical_pair_are_owned_exactly():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "847ceb038813"
    pairs = _canonical_pairs()
    assert len(pairs) == 6

    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original



def test_selected_racket_authority_is_exact_canonical_with_raw_source_preserved():
    canonical_path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical = None
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical = row
                break
    assert canonical is not None

    base_path = (
        ROOT
        / "shared"
        / "data"
        / "base"
        / "solutions"
        / "training"
        / "ed98d772__9db8deba5903.json"
    )
    base = json.loads(base_path.read_text(encoding="utf-8"))
    target = base["racket_target"]
    assert target["target_code"] == canonical["program_solution"]
    assert target["raw_code"] != target["target_code"]
    assert target["canonicalization_status"] == "selected_canonical_with_preserved_archival_raw"
    assert target["target_status"] == "selected_exact_canonical; archival_raw_execution_parity_required"

def test_schedule_has_four_profiles_per_band_and_canonical_support_everywhere():
    assert len(GEN.SCHEDULE_PROFILES) == 12
    assert set(GEN.AXES) == {"scene_profile"}
    for difficulty in ("easy", "medium", "hard"):
        scheduled = [GEN.schedule_profile(123, i, difficulty) for i in range(8)]
        assert len(set(scheduled[:4])) == 4
        assert scheduled[:4] == scheduled[4:]

        signatures = []
        for i in range(4):
            grid = GEN.generate(123, i, difficulty=difficulty)
            counts = sorted(Counter(value for row in grid for value in row).values())
            signatures.append((len(grid), len(grid[0]), len(counts)))
        assert (3, 3, 2) in signatures


def test_every_scene_profile_override_is_exactly_observable_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for index, profile in enumerate(GEN.SCHEDULE_PROFILES):
            requested = {"scene_profile": profile}
            grid = GEN.generate(
                9000 + index,
                index,
                difficulty=difficulty,
                **requested,
            )
            assert GEN.self_check(
                grid, difficulty=difficulty, meta={"overrides": requested}
            ) == []
            assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"unknown_axis": 1}, "unknown override"),
        ({"scene_profile": "not-a-profile"}, "scene_profile"),
        ({"difficulty": "extreme"}, "difficulty"),
    ],
)
def test_invalid_generation_requests_fail_loudly(kwargs, match):
    with pytest.raises((TypeError, ValueError), match=match):
        GEN.generate(1, 0, **kwargs)


def test_default_draws_are_valid_semantic_and_refute_declared_rivals():
    for difficulty in ("easy", "medium", "hard"):
        seen = set()
        for sample_index in range(24):
            grid = GEN.generate(711, sample_index, difficulty=difficulty)
            seen.add(repr(grid))
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.strict_canonical_like(grid) == []
            assert 3 <= len(grid) <= 7
            assert len(grid) == len(grid[0])
            assert 2 <= len({value for row in grid for value in row}) <= 4
            intended = GEN.rule_mirror(grid)
            assert GEN.SEMANTIC_WITNESSES["rotation_changes_grid"](grid)
            assert GEN.SEMANTIC_RIVALS["repeat_identity"](grid) != intended
            if GEN.SEMANTIC_WITNESSES["quarter_turn_direction_visible"](grid):
                assert GEN.SEMANTIC_RIVALS["swap_quarter_turns"](grid) != intended
        assert len(seen) >= 20


def test_each_band_contains_half_turn_and_full_orbit_examples():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(77, i, difficulty=difficulty) for i in range(4)]
        assert any(GEN.SEMANTIC_WITNESSES["half_turn_symmetric_case"](g) for g in grids)
        assert any(GEN.SEMANTIC_WITNESSES["full_rotation_orbit"](g) for g in grids)
        assert any(GEN.SEMANTIC_WITNESSES["multicolor_case"](g) for g in grids)


def test_generation_is_deterministic_fresh_and_global_random_pure():
    random.seed(314159)
    state = random.getstate()
    first = GEN.generate(12345, 7, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(12345, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_every_sliding_four_demo_lesson_refutes_named_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            demos, query = _lesson(404, start, difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_self_check_rejects_structural_impostors_without_rejecting_orbit_two():
    lawful_orbit_two = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]
    assert GEN.self_check(lawful_orbit_two) == []

    bad_cases = {
        "empty": [],
        "ragged": [[0, 1], [1]],
        "rectangle": [[0, 1, 0], [1, 0, 1]],
        "out_of_range": [[0, 0, 1], [0, 1, 0], [1, 0, 10]],
        "monochrome": [[0] * 3 for _ in range(3)],
        "single_cell": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        "short_line": [[0, 0, 0], [1, 1, 1], [0, 0, 0]],
        "solid_2x2": [[1, 1, 0], [1, 1, 0], [0, 0, 0]],
        "four_fold": [[1, 0, 1], [0, 1, 0], [1, 0, 1]],
    }
    for name, grid in bad_cases.items():
        assert GEN.self_check(grid), name

"""Focused regressions for generator ``f505996a2fdc``."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import random
import sys
from pathlib import Path

import pytest

# Portable bootstrap: works both in the review packet and the staged runtime.
for ancestor in Path(__file__).resolve().parents:
    packet_runtime = ancestor / "shared" / "runtime"
    if (packet_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(packet_runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import (  # noqa: E402
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
)

TASK_ID = "f505996a2fdc"
ROOT = find_root(__file__)
DEFAULT_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_SOURCE.is_file():
    DEFAULT_SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_SOURCE))
SPEC = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_row() -> dict:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _grid(value):
    if isinstance(value, list) and value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return copy.deepcopy(value)


def _canonical_pairs() -> list[dict]:
    return [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in load_canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    ]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN._authority_output(grid)}


def test_metadata_rule_pin_and_authority_binding_are_exact():
    row = _canonical_row()
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == _normalized_hash(row["program_solution"]) == "9bbe263d873a"
    assert GEN.EXAMPLES_NEEDED == 5
    assert GEN.MIN_STRICT_FRAC == 1.0


def test_all_canonical_pairs_are_accepted_and_solved_exactly():
    for pair in _canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._authority_output(pair["input"]) == pair["output"]


def test_six_slot_curriculum_survives_every_leave_one_out_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [_pair(GEN.generate(4700 + start, start + offset, difficulty=band))
                     for offset in range(6)]
            commands = [GEN._analysis(pair["input"])["cmd"] for pair in pairs]
            assert set(commands) == {1, 2, 3, 4, 5, 6}
            assert all(GEN.self_check(pair["input"]) == [] for pair in pairs)
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, competitor in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(demo["input"]) != demo["output"]
                        for demo in demos
                    ), (band, start, query_index, name)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 8, "cmd": 1, "blob_h": 2, "blob_w": 2, "n_colors": 1},
        {"grid_h": 10, "grid_w": 10, "cmd": 6, "blob_h": 4, "blob_w": 4, "n_colors": 3},
        {"grid_h": 9, "grid_w": 10, "cmd": 4, "blob_h": 3, "blob_w": 2, "n_colors": 2},
    ],
)
def test_representative_boundary_overrides_are_exact(band, overrides):
    grid = GEN.generate(991, 37, difficulty=band, **overrides)
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert GEN.observe_overrides(grid) == overrides


def test_unknown_invalid_and_coerced_overrides_are_rejected():
    bad_calls = (
        {"unknown": 1},
        {"grid_h": 7},
        {"grid_w": 11},
        {"cmd": 0},
        {"cmd": 7},
        {"blob_h": 1},
        {"blob_w": 5},
        {"n_colors": 0},
        {"n_colors": 4},
        {"grid_h": True},
        {"cmd": "2"},
        {"blob_w": 3.0},
    )
    for overrides in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 2, **overrides)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty="expert")


def test_declared_canonical_shortcuts_are_real_and_generated_flip_cases_refute_them():
    pairs = _canonical_pairs()
    assert set(GEN.CANONICAL_SHORTCUTS) == {"swap_unseen_flips", "unseen_as_identity"}
    for shortcut in GEN.CANONICAL_SHORTCUTS.values():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)

    generated = [GEN.generate(20261005, index, difficulty="medium") for index in range(6)]
    flip_cases = [grid for grid in generated if GEN._analysis(grid)["cmd"] in (5, 6)]
    assert len(flip_cases) == 2
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert any(shortcut(grid) != GEN._authority_output(grid) for grid in flip_cases), name
    assert any(GEN.SEMANTIC_WITNESSES["swap_unseen_flips_visible"](grid) for grid in flip_cases)
    assert any(GEN.SEMANTIC_WITNESSES["unseen_as_identity_visible"](grid) for grid in flip_cases)


def test_self_check_rejects_targeted_near_misses():
    base = GEN.generate(123, 0, difficulty="hard")

    dirty_command_row = copy.deepcopy(base)
    dirty_command_row[0][2] = 9

    dirty_separator = copy.deepcopy(base)
    dirty_separator[1][0] = 9

    no_body = copy.deepcopy(base)
    for row in range(2, len(no_body)):
        for col in range(len(no_body[0])):
            no_body[row][col] = 0

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    bad_color = copy.deepcopy(base)
    body = [(r, c) for r in range(2, len(base)) for c, value in enumerate(base[r]) if value]
    bad_color[body[0][0]][body[0][1]] = base[0][0]

    for mutation in (dirty_command_row, dirty_separator, no_body, ragged, bad_color):
        assert GEN.self_check(mutation), mutation


def test_authority_transform_codebook_on_one_asymmetric_crop():
    motif = [[1, 2, 0], [3, 4, 5]]
    expected = {
        1: [[1, 2, 0], [3, 4, 5]],
        2: [[3, 1], [4, 2], [5, 0]],
        3: [[5, 4, 3], [0, 2, 1]],
        4: [[1, 3], [2, 4], [0, 5]],
        5: [[0, 2, 1], [5, 4, 3]],
        6: [[3, 4, 5], [1, 2, 0]],
    }
    for cmd, output in expected.items():
        grid = [[0] * 8 for _ in range(8)]
        grid[0][0] = cmd
        for r, row in enumerate(motif, start=3):
            grid[r][2:5] = row
        assert GEN._authority_output(grid) == output


def test_default_schedule_anchors_every_canonical_exact_profile():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({value for row in pair["input"] for value in row}))
        for pair in _canonical_pairs()
    }
    for band in ("easy", "medium", "hard"):
        profiles = []
        for index in range(6):
            grid = GEN.generate(77, index, difficulty=band)
            profiles.append((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert canonical_profiles <= set(profiles)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20261005)
    state = random.getstate()
    first = GEN.generate(2026, 1005, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(2026, 1005, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

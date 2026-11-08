from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import sys
import json
import random
from pathlib import Path

import pytest


TASK_ID = "c2b9484357c1"
HERE = Path(__file__).resolve()
LIBRARY = next((p for p in HERE.parents if (p / "shared/runtime").is_dir()), None)
if LIBRARY is not None:
    # The selected task's tests can run without first staging the entire library.
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
    ROOT = LIBRARY / "shared"
    spec = importlib.util.spec_from_file_location(
        "c2b9484357c1_subject", LIBRARY / "generators" / TASK_ID / "generator.py"
    )
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
else:
    ROOT = HERE.parents[1]
    gen = importlib.import_module("puzzle_generators.per_puzzle.c2b9484357c1.generator")
EXPECTED_RULE_HASH = "4d65cf4d4b83"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _frame(grid: list[list[int]], rect: tuple[int, int, int, int], color: int) -> None:
    r0, c0, r1, c1 = rect
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                grid[r][c] = color


def test_rule_hash_and_all_canonical_pairs_are_exact() -> None:
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == EXPECTED_RULE_HASH
    assert gen.RULE_HASH == EXPECTED_RULE_HASH

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen._true_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_scheduled_lesson_exposes_selection_and_rebuts_shortcuts() -> None:
    grids = [gen.generate(4901, index, difficulty="medium") for index in range(5)]
    assert [gen.observe_overrides(grid)["scene_profile"] for grid in grids[:4]] == list(
        gen.SCENE_PROFILES
    )
    assert [gen.observe_overrides(grid)["solid_decoy"] for grid in grids[:4]] == [
        False,
        True,
        True,
        False,
    ]
    for grid in grids:
        assert gen.self_check(grid) == []
        assert gen._true_output(grid) != grid

    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name

    demos = [{"input": grid, "output": gen._true_output(grid)} for grid in grids[:4]]
    query = {"input": grids[4], "output": gen._true_output(grids[4])}
    assert gen.lesson_identifiable(demos, query) == []


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    cases = {
        "grid_h": (8, 12),
        "grid_w": (9, 14),
        "scene_profile": gen.SCENE_PROFILES,
        "solid_decoy": (False, True),
        "palette_kind": gen.PALETTE_KINDS,
    }
    for band in ("easy", "medium", "hard"):
        for axis, values in cases.items():
            for value in values:
                for seed in (0, 17, 29):
                    grid = gen.generate(
                        seed,
                        seed + 5,
                        difficulty=band,
                        **{axis: value},
                    )
                    assert gen.self_check(grid) == []
                    if axis in {"grid_h", "grid_w"}:
                        observed = len(grid) if axis == "grid_h" else len(grid[0])
                    else:
                        observed = gen.observe_overrides(grid)[axis]
                    assert observed == value

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis="accepted")


def test_replay_returns_fresh_grids_and_preserves_global_rng() -> None:
    random.seed(20260725)
    global_state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == global_state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_self_check_rejects_four_structural_impostors() -> None:
    valid = gen.generate(
        71,
        9,
        difficulty="medium",
        scene_profile="aligned_last",
        solid_decoy=True,
        palette_kind="canonical",
    )
    assert gen.self_check(valid) == []
    scene = gen._scene(valid)
    target = gen._largest_hollow(scene)
    assert target is not None
    solid = next(obj for obj in scene if not obj["hollow"])

    opened_hole = copy.deepcopy(valid)
    tr0, tc0, _, _ = target["bbox"]
    opened_hole[tr0][tc0 + 1] = 0

    foreign_inside_bbox = copy.deepcopy(valid)
    hr, hc = next(iter(target["hole_cells"]))
    replacement = next(color for color in range(1, 10) if color not in {o["color"] for o in scene})
    foreign_inside_bbox[hr][hc] = replacement

    broken_solid = copy.deepcopy(valid)
    sr, sc = next(iter(solid["cells"]))
    broken_solid[sr][sc] = 0

    tied = [[0 for _ in range(9)] for _ in range(8)]
    _frame(tied, (0, 0, 2, 2), 2)
    _frame(tied, (5, 6, 7, 8), 3)

    fixtures = {
        "opened_target_perimeter": opened_hole,
        "foreign_component_inside_target_bbox": foreign_inside_bbox,
        "non_rectangular_solid_decoy": broken_solid,
        "tied_largest_hollows": tied,
    }
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name


def test_negative_recombination_with_novel_replacement_color_is_rejected() -> None:
    grid = gen.generate(
        601,
        3,
        difficulty="easy",
        scene_profile="bbox_area_conflict",
        solid_decoy=False,
        palette_kind="canonical",
    )
    scene = gen._scene(grid)
    target = gen._largest_hollow(scene)
    assert target is not None
    used = {obj["color"] for obj in scene}
    novel = next(color for color in range(1, 10) if color not in used)
    mutation = copy.deepcopy(grid)
    r0, c0, _, _ = target["bbox"]
    mutation[r0][c0 + 1] = novel
    assert all(obj["color"] != novel for obj in scene)
    assert gen.self_check(mutation)

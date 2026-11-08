"""Focused semantic regressions for generator 4f640d81f260."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "4f640d81f260"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]
BANDS = ("easy", "medium", "hard")
BASE_PATHS = (
    ROOT / "data/base/solutions/augmented/9f27f097__4f255e58511a.json",
    ROOT / "data/base/solutions/training/9f27f097__4f640d81f260.json",
)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_rows() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def _first_background_cell(grid: list[list[int]]) -> tuple[int, int]:
    scene = GEN._scene(grid)
    occupied = GEN._rect_cells(scene["target_box"]) | GEN._rect_cells(scene["template_box"])
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if (row, col) not in occupied:
                return row, col
    raise AssertionError("generated scene has no background cell")


def test_all_canonical_pairs_are_accepted_and_solved_without_mutation():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 8  # two authority rows, four unique pairs
    assert len({json.dumps(pair, sort_keys=True) for pair in pairs}) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_rule_hash_and_selected_authorities_are_atomically_synchronized():
    rows = _canonical_rows()
    assert len(rows) == 2
    selected = {row["program_solution"] for row in rows}
    assert len(selected) == 1
    canonical = selected.pop()
    assert GEN.RULE_HASH == "bddf313b5517"
    assert GEN.RULE_HASH == _normalized_hash(canonical)

    for path in BASE_PATHS:
        target = json.loads(path.read_text())["racket_target"]
        assert target["target_code"] == canonical
        assert target["target_code_role"] == "selected_task_rule"
        assert target["raw_code_role"] == "archival_executable_source"
        assert target["raw_code"] != canonical


def test_exact_boundary_overrides_round_trip_in_every_band():
    cases = (
        {
            "grid_h": 12,
            "grid_w": 12,
            "template_size": "5x5",
            "background_color": 1,
            "template_palette_size": 2,
            "target_relation": "above",
            "template_column": "left",
            "target_column": "right",
        },
        {
            "grid_h": 16,
            "grid_w": 16,
            "template_size": "3x4",
            "background_color": 9,
            "template_palette_size": 3,
            "target_relation": "below",
            "template_column": "right",
            "target_column": "left",
        },
        {
            "grid_h": 12,
            "grid_w": 16,
            "template_size": "4x6",
            "background_color": 8,
            "template_palette_size": 2,
            "target_relation": "below",
            "template_column": "center",
            "target_column": "right",
        },
        {
            "grid_h": 16,
            "grid_w": 12,
            "template_size": "4x4",
            "background_color": 2,
            "template_palette_size": 3,
            "target_relation": "above",
            "template_column": "right",
            "target_column": "center",
        },
    )
    for band in BANDS:
        for index, requested in enumerate(cases):
            grid = GEN.generate(
                1000 + index,
                7919 + index,
                difficulty=band,
                **requested,
            )
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, difficulty="easy", typo_target_relation="above")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty="easy", grid_h=11)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, difficulty="easy", target_relation="sideways")


def test_self_check_rejects_five_semantic_mutations():
    grid = GEN.generate(4242, 7, difficulty="medium")
    scene = GEN._scene(grid)
    background = scene["background"]
    target = scene["target_box"]
    template = scene["template_box"]

    target_hole = copy.deepcopy(grid)
    target_hole[target[0]][target[1]] = background

    stray_zero = copy.deepcopy(grid)
    row, col = _first_background_cell(stray_zero)
    stray_zero[row][col] = 0

    template_hole = copy.deepcopy(grid)
    template_hole[template[0]][template[1]] = background

    stray_template = copy.deepcopy(grid)
    row, col = _first_background_cell(stray_template)
    stray_template[row][col] = scene["template"][0][0]

    wrong_target_height = copy.deepcopy(grid)
    for col in range(target[1], target[3] + 1):
        wrong_target_height[target[0]][col] = background

    fixtures = {
        "target_hole": target_hole,
        "stray_zero": stray_zero,
        "template_hole": template_hole,
        "stray_template": stray_template,
        "wrong_target_height": wrong_target_height,
    }
    for name, malformed in fixtures.items():
        assert GEN.self_check(malformed), name


def test_four_slot_schedule_is_identifiable_in_every_sliding_window():
    for band in BANDS:
        for start in range(16):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                index = start + offset
                grid = GEN.generate(20_000 + index, index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            demos, query = pairs[: GEN.EXAMPLES_NEEDED], pairs[-1]
            assert GEN.lesson_identifiable(demos, query) == [], (band, start)
            assert {GEN.observe_overrides(p["input"])["template_size"] for p in demos} == set(GEN.TEMPLATE_SIZES)
            assert {GEN.observe_overrides(p["input"])["target_relation"] for p in demos} == set(GEN.TARGET_RELATIONS)


def test_every_generated_scene_refutes_all_declared_rivals():
    for band in BANDS:
        for index in range(40):
            grid = GEN.generate(30_000 + index, index * 17 + 3, difficulty=band)
            official = GEN.rule_mirror(grid)
            assert GEN.self_check(grid) == []
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                assert official != rival(grid), (band, index, name)


def test_determinism_fresh_returns_global_rng_and_input_purity():
    random.seed(20260726)
    global_state = random.getstate()
    first = GEN.generate(99123, 4567, difficulty="hard")
    assert random.getstate() == global_state
    second = GEN.generate(99123, 4567, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    snapshot = copy.deepcopy(first)
    GEN.self_check(first)
    GEN.observe_overrides(first)
    GEN.rule_mirror(first)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(first)
    assert first == snapshot

    first[0][0] = 0
    third = GEN.generate(99123, 4567, difficulty="hard")
    assert third == second

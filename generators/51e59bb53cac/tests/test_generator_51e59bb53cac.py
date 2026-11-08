from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter

import pytest

from reviewer_support import find_root

TASK_ID = "51e59bb53cac"
ROOT = find_root(__file__)
MOD = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
BASE_PATHS = (
    ROOT / "data/base/solutions/training/7ee1c6ea__51e59bb53cac.json",
    ROOT / "data/base/solutions/augmented/7ee1c6ea__aa9a7f0218d2.json",
)


def _canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def _bbox(grid):
    gray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    return (
        min(row for row, _ in gray),
        min(col for _, col in gray),
        max(row for row, _ in gray),
        max(col for _, col in gray),
    )


def test_rule_hash_and_task_local_authorities_are_synced():
    rows = _canonical_rows()
    assert rows
    source = rows[0]["program_solution"]
    assert all(row["program_solution"] == source for row in rows)
    normalized = " ".join(source.split())
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert digest == MOD.RULE_HASH == "6efb83adf2b2"
    for path in BASE_PATHS:
        record = json.loads(path.read_text())
        assert " ".join(record["racket_target"]["raw_code"].split()) == normalized
        assert " ".join(record["racket_target"]["target_code"].split()) == normalized


def test_every_canonical_train_and_test_input_passes_structural_check():
    rows = _canonical_rows()
    assert sum(len(row.get(split, [])) for row in rows for split in ("train", "test")) >= 4
    for row in rows:
        for split in ("train", "test"):
            for index, pair in enumerate(row.get(split, [])):
                assert MOD.self_check(pair["input"]) == [], (row["source"], split, index)
                assert MOD.rule_mirror(pair["input"]) == pair["output"]


def test_default_draws_have_all_scoping_and_branch_witnesses():
    anchors = set()
    palette_kinds = set()
    shapes = set()
    inputs = set()
    outputs = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(120):
            grid = MOD.generate(1000 + seed, band_index * 10000 + seed, difficulty=band)
            analysis = MOD._analysis(grid)
            assert analysis["errors"] == [], (band, seed, analysis["errors"])
            color_a, color_b = analysis["colors"]
            assert analysis["interior_counter"][color_a] >= 2
            assert analysis["interior_counter"][color_b] >= 2
            assert analysis["interior_counter"][color_a] != analysis["interior_counter"][color_b]
            assert analysis["interior_counter"][0] >= 1
            assert analysis["outside_counter"][color_a] >= 2
            assert analysis["outside_counter"][color_b] >= 2
            assert all(value >= 1 for value in analysis["zone_witnesses"].values())
            assert set(analysis["palette"]) == {0, 5, color_a, color_b}
            output = MOD.rule_mirror(grid)
            top, left, bottom, right = analysis["bbox"]
            assert any(
                grid[row][col] == color_a and output[row][col] == color_b
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
            )
            assert any(
                grid[row][col] == color_b and output[row][col] == color_a
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
            )
            assert any(
                grid[row][col] == output[row][col] == 0
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
            )
            assert any(
                grid[row][col] in {color_a, color_b}
                and output[row][col] == grid[row][col]
                for row in range(len(grid))
                for col in range(len(grid[0]))
                if not (top <= row <= bottom and left <= col <= right)
            )
            global_swap = [
                [color_b if value == color_a else color_a if value == color_b else value for value in row]
                for row in grid
            ]
            assert global_swap != output
            observed = MOD.observe_overrides(grid)
            anchors.add(observed["frame_anchor"])
            palette_kinds.add(observed["palette_kind"])
            shapes.add((len(grid), len(grid[0])))
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, output)))
    assert anchors == set(MOD.FRAME_ANCHORS)
    assert palette_kinds == set(MOD.PALETTE_KINDS)
    assert len(shapes) > 80
    assert len(inputs) == 360
    assert len(outputs) == 360


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8},
        {"grid_h": 22},
        {"grid_w": 8},
        {"grid_w": 22},
        {"frame_h": 5},
        {"frame_h": 10},
        {"frame_w": 5},
        {"frame_w": 10},
        {"frame_anchor": "corner"},
        {"frame_anchor": "edge"},
        {"frame_anchor": "interior"},
        {"palette_kind": "canonical"},
        {"palette_kind": "broad"},
        {"fill_ratio": 0.35},
        {"fill_ratio": 0.90},
        {"outside_fill_ratio": 0.30},
        {"outside_fill_ratio": 0.85},
    ],
)
def test_declared_boundary_overrides_are_exact_or_observably_effective(band, overrides):
    low = MOD.generate(17, 23, difficulty=band, **overrides)
    assert MOD.self_check(low) == []
    observed = MOD.observe_overrides(low)
    for name in ("frame_h", "frame_w", "frame_anchor", "palette_kind"):
        if name in overrides:
            assert observed[name] == overrides[name]
    if "grid_h" in overrides:
        assert len(low) == overrides["grid_h"]
    if "grid_w" in overrides:
        assert len(low[0]) == overrides["grid_w"]


def test_incompatible_and_unknown_overrides_reject_loudly():
    with pytest.raises(ValueError):
        MOD.generate(1, 2, difficulty="easy", grid_h=8, frame_h=10)
    with pytest.raises(ValueError):
        MOD.generate(1, 2, difficulty="easy", grid_h=8, frame_anchor="interior")
    with pytest.raises(ValueError):
        MOD.generate(1, 2, frame_anchor="center")
    with pytest.raises(ValueError):
        MOD.generate(1, 2, fill_ratio=0.1)
    with pytest.raises(ValueError):
        MOD.generate(1, 2, texture="legacy")
    with pytest.raises(ValueError):
        MOD.generate(1, 2, difficulty="extreme")


def test_self_check_rejects_targeted_structural_impostors():
    original = MOD.generate(321, 654, difficulty="medium", palette_kind="canonical")
    analysis = MOD._analysis(original)
    top, left, bottom, right = analysis["bbox"]
    color_a, color_b = analysis["colors"]

    broken_frame = copy.deepcopy(original)
    broken_frame[top][left + 1] = 0

    third_interior_color = copy.deepcopy(original)
    absent = next(color for color in MOD.LEGAL_COLORS if color not in set(analysis["palette"]))
    zero_cell = next(
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if third_interior_color[row][col] == 0
    )
    third_interior_color[zero_cell[0]][zero_cell[1]] = absent

    missing_outside_role = copy.deepcopy(original)
    for row in range(len(original)):
        for col in range(len(original[0])):
            if not (top <= row <= bottom and left <= col <= right):
                if missing_outside_role[row][col] == color_a:
                    missing_outside_role[row][col] = color_b

    equal_interior_counts = copy.deepcopy(original)
    counts = Counter(
        original[row][col]
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
    )
    majority = color_a if counts[color_a] > counts[color_b] else color_b
    minority = color_b if majority == color_a else color_a
    delta = counts[majority] - counts[minority]
    majority_cells = [
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if equal_interior_counts[row][col] == majority
    ]
    if delta % 2 == 0:
        for row, col in majority_cells[: delta // 2]:
            equal_interior_counts[row][col] = minority
    else:
        equal_interior_counts[majority_cells[0][0]][majority_cells[0][1]] = 0
        remaining = (delta - 1) // 2
        for row, col in majority_cells[1 : 1 + remaining]:
            equal_interior_counts[row][col] = minority

    sparse_exterior = copy.deepcopy(original)
    kept = {"top": False, "bottom": False, "left": False, "right": False}
    for row in range(len(original)):
        for col in range(len(original[0])):
            if top <= row <= bottom and left <= col <= right:
                continue
            zone = (
                "top" if row < top else
                "bottom" if row > bottom else
                "left" if col < left else
                "right"
            )
            value = sparse_exterior[row][col]
            if value in {color_a, color_b} and not kept[zone]:
                kept[zone] = True
            elif value in {color_a, color_b}:
                sparse_exterior[row][col] = 0

    impostors = {
        "broken_frame": broken_frame,
        "third_interior_color": third_interior_color,
        "missing_outside_role": missing_outside_role,
        "equal_interior_counts": equal_interior_counts,
        "sparse_exterior": sparse_exterior,
    }
    for name, grid in impostors.items():
        assert MOD.self_check(grid), name


def test_replay_freshness_input_purity_and_process_rng_state():
    random.seed(8881)
    state = random.getstate()
    first = MOD.generate(
        19,
        29,
        difficulty="hard",
        frame_anchor="edge",
        palette_kind="canonical",
    )
    assert random.getstate() == state
    replay = MOD.generate(
        19,
        29,
        difficulty="hard",
        frame_anchor="edge",
        palette_kind="canonical",
    )
    assert first == replay
    assert first is not replay
    assert first[0] is not replay[0]
    before = copy.deepcopy(first)
    output = MOD.rule_mirror(first)
    assert first == before
    assert output is not first
    assert output[0] is not first[0]

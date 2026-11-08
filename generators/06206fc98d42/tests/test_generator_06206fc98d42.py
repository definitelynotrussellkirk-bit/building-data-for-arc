"""Focused semantic and override regressions for generator 06206fc98d42."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer


TASK_ID = "06206fc98d42"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE_FILE = (
    ROOT
    / "data/base/solutions/banks/7d2e04a04712/"
    "E133__06206fc98d42.json"
)


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"]
    return row["train"] + (test if isinstance(test, list) else [test])


def _rule_hash(source):
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _features(grid):
    objects, errors = MODULE._scene_analysis(grid)
    assert not errors
    return {
        "objects": objects,
        "count": len(objects),
        "colors": [obj["color"] for obj in objects],
        "center_empty": [
            grid[obj["center"][0]][obj["center"][1]] == 0
            for obj in objects
        ],
        "even_bbox": [
            (obj["bbox"][2] - obj["bbox"][0] + 1) % 2 == 0
            or (obj["bbox"][3] - obj["bbox"][1] + 1) % 2 == 0
            for obj in objects
        ],
    }


def _blank(height=9, width=10):
    return [[0] * width for _ in range(height)]


def test_all_canonical_pairs_rule_mirror_hash_and_source_sync():
    row = _canonical_row()
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert MODULE.self_check(source) == []
        assert MODULE.rule_mirror(source) == pair["output"]
        assert source == snapshot

    base = json.loads(BASE_FILE.read_text())
    canonical_rule = row["program_solution"]
    assert base["racket_target"]["target_code"] == canonical_rule
    assert MODULE.RULE_HASH == _rule_hash(canonical_rule)
    assert MODULE.RULE_HASH == "9f601f00a9b1"


def test_default_linked_semantic_census_is_exact_and_varied():
    for band in ("easy", "medium", "hard"):
        textures = Counter()
        object_counts = Counter()
        hollow_witnesses = 0
        repeat_witnesses = 0
        even_bbox_draws = 0
        inputs = set()
        outputs = set()
        for seed in range(120):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = MODULE.generate(seed, seed, difficulty=band)
            finally:
                set_ctx_observer(None)
            context = captured[-1]
            facts = _features(grid)
            texture = context._drawn["texture"]
            drawn_objects = context._drawn["objects"]
            textures[texture] += 1
            object_counts[facts["count"]] += 1
            assert drawn_objects == facts["count"]
            assert MODULE.observe_overrides(grid) == {
                "objects": drawn_objects
            }
            assert MODULE.self_check(grid) == []
            output = MODULE.rule_mirror(grid)
            assert output != grid
            assert sum(value != 0 for row in output for value in row) == facts["count"]
            hollow_witnesses += int(
                texture == "hollow_center" and any(facts["center_empty"])
            )
            repeat_witnesses += int(
                texture == "repeat_color"
                and len(set(facts["colors"])) == 1
            )
            even_bbox_draws += int(any(facts["even_bbox"]))
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, output)))

        assert set(textures) == set(MODULE.HELPFUL_TEXTURES)
        assert hollow_witnesses == textures["hollow_center"]
        assert repeat_witnesses == textures["repeat_color"]
        assert even_bbox_draws >= 80
        assert len(inputs) == 120
        assert len(outputs) >= 115
        if band == "easy":
            assert object_counts == {2: 120}
        elif band == "hard":
            assert set(object_counts) == {3, 4}
        else:
            assert set(object_counts) == {2, 3, 4}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_boundary_overrides_are_exact_or_reject_incompatibility_loudly(band):
    cases = (
        {"grid_h": 5},
        {"grid_h": 16},
        {"grid_w": 5},
        {"grid_w": 16},
        {"objects": 2},
        {"objects": 4},
        {"texture": "plain"},
        {"texture": "hollow_center"},
        {"texture": "repeat_color"},
        {"texture": "single_cell_objects", "objects": 4},
        {"texture": "even_size_objects", "objects": 4},
        {"texture": "no_objects"},
    )
    for seed in range(8):
        for overrides in cases:
            grid = MODULE.generate(
                seed + 500,
                seed * 17 + 3,
                difficulty=band,
                **overrides,
            )
            if "grid_h" in overrides:
                assert len(grid) == overrides["grid_h"]
            if "grid_w" in overrides:
                assert len(grid[0]) == overrides["grid_w"]
            observed = MODULE.observe_overrides(grid)
            if "objects" in overrides:
                assert observed["objects"] == overrides["objects"]
            meta = {"overrides": dict(overrides)}
            assert MODULE.self_check(grid, difficulty=band, meta=meta) == []

    with pytest.raises(ValueError, match="incompatible"):
        MODULE.generate(1, 2, difficulty=band, grid_h=5, grid_w=5)
    with pytest.raises(ValueError, match="incompatible with an objects"):
        MODULE.generate(
            1,
            2,
            difficulty=band,
            texture="no_objects",
            objects=2,
        )


def test_self_check_rejects_targeted_structural_impostors():
    all_background = _blank()
    singleton = _blank()
    singleton[4][4] = 2
    short_line = _blank()
    for col in range(3, 7):
        short_line[4][col] = 6

    oversized_bbox = _blank()
    for col in range(1, 6):
        oversized_bbox[1][col] = 2
    for row, col in ((6, 6), (6, 7), (7, 6)):
        oversized_bbox[row][col] = 3

    duplicate_centers = _blank()
    for row, col in (
        (1, 1),
        (1, 2),
        (1, 3),
        (2, 1),
        (2, 3),
        (3, 1),
        (3, 2),
        (3, 3),
    ):
        duplicate_centers[row][col] = 4
    duplicate_centers[2][2] = 5

    for mutation in (
        all_background,
        singleton,
        short_line,
        oversized_bbox,
        duplicate_centers,
        [[0, 0], [0]],
        [[True, 0], [0, 0]],
        [[10, 0], [0, 0]],
    ):
        assert MODULE.self_check(mutation), mutation


def test_explicit_degenerate_modes_are_narrow_and_meta_checked():
    for texture, expected_size in (
        ("single_cell_objects", 1),
        ("even_size_objects", 4),
    ):
        grid = MODULE.generate(
            100,
            200,
            difficulty="medium",
            texture=texture,
            objects=4,
        )
        facts = _features(grid)
        assert facts["count"] == 4
        assert [len(obj["cells"]) for obj in facts["objects"]] == [
            expected_size
        ] * 4
        assert MODULE.self_check(
            grid,
            meta={"overrides": {"texture": texture, "objects": 4}},
        ) == []
        if texture == "single_cell_objects":
            assert MODULE.self_check(grid)
        else:
            # Solid 2x2 objects are edge-valid under the canonical rule.
            assert MODULE.self_check(grid) == []

    blank = MODULE.generate(
        100,
        200,
        difficulty="medium",
        texture="no_objects",
    )
    assert MODULE.observe_overrides(blank) == {"objects": 0}
    assert MODULE.self_check(
        blank,
        meta={"overrides": {"texture": "no_objects"}},
    ) == []
    assert MODULE.self_check(blank)


def test_negative_recombinations_refute_shortcuts():
    grid = _blank(9, 13)
    # Same-color objects: one output per object, not one per color.
    for row, col in ((1, 1), (1, 2), (2, 1)):
        grid[row][col] = 7
    for row, col in ((1, 7), (1, 8), (2, 8), (2, 9)):
        grid[row][col] = 7
    # Hollow center: output paints a cell that was background.
    for row, col in (
        (5, 1),
        (5, 2),
        (5, 3),
        (6, 1),
        (6, 3),
        (7, 1),
        (7, 2),
        (7, 3),
    ):
        grid[row][col] = 4
    # Even 2x2 bbox: floor chooses the top-left cell.
    for row in (5, 6):
        for col in (8, 9):
            grid[row][col] = 2

    assert MODULE.self_check(grid) == []
    output = MODULE.rule_mirror(grid)
    expected = _blank(9, 13)
    expected[1][1] = 7
    expected[1][8] = 7
    expected[6][2] = 4
    expected[5][8] = 2
    assert output == expected
    assert grid[6][2] == 0
    assert sum(value == 7 for row in output for value in row) == 2


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(20260723)
    state = random.getstate()
    first = MODULE.generate(917, 311, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(917, 311, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    frozen = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(917, 311, difficulty="hard") == frozen


def test_unknown_axis_texture_and_difficulty_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 2, bogus=3)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, texture="unknown")
    with pytest.raises(ValueError, match="unknown difficulty"):
        MODULE.generate(1, 2, difficulty="extreme")

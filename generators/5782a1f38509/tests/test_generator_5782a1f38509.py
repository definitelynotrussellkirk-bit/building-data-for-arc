"""Task-local semantic regressions for generator 5782a1f38509.

The unchanged canonical Racket program remains label authority.  The Python
mirror below is intentionally independent of the generator's diagnostic mirror
so tests do not merely compare the module with itself.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
TASK_ID = "5782a1f38509"


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_record():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise AssertionError("canonical task not found")


def _components(grid):
    cardinals = ((1, 0), (-1, 0), (0, 1), (0, -1))
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in cardinals:
                    point = rr + dr, cc + dc
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        pending.append(point)
            objects.append((color, cells))
    return objects


def independent_rule(grid):
    pieces = []
    for color, cells in sorted(_components(grid), key=lambda item: len(item[1])):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        top, left = min(rows), min(cols)
        bottom, right = max(rows), max(cols)
        piece = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
        for row, col in cells:
            piece[row - top][col - left] = color
        pieces.append(piece)
    if not pieces:
        return [[0]]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = [[0] * width for _ in range(height)]
    left = 0
    for piece in pieces:
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value:
                    output[row][left + col] = value
        left += len(piece[0]) + 1
    return output


gen = _load_generator()
CANONICAL = _canonical_record()
CANONICAL_PAIRS = CANONICAL["train"] + [CANONICAL["test"]]


def test_authority_pin_and_all_canonical_pairs():
    assert gen.RULE_HASH == "a6b584fba994"
    for pair in CANONICAL_PAIRS:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert independent_rule(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_default_five_example_cycle_is_valid_and_refutes_every_competitor():
    assert gen.EXAMPLES_NEEDED == 5
    assert len(gen.SCHEDULE_PROFILES) == 5
    for band in (None, "easy", "medium", "hard"):
        for start in range(5):
            demos = []
            profiles = []
            for offset in range(gen.EXAMPLES_NEEDED):
                index = start + offset
                grid = gen.generate(10_003, index, difficulty=band)
                assert gen.self_check(grid) == []
                assert grid == gen.generate(10_003, index, difficulty=band)
                assert gen.rule_mirror(grid) == independent_rule(grid)
                profiles.append(gen.schedule_profile(10_003, index, band))
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert set(profiles) == set(gen.SCHEDULE_PROFILES)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_every_texture_honors_exact_dimensions_and_is_lawful():
    for texture in gen.HELPFUL_TEXTURES:
        for height, width in ((5, 6), (9, 12), (18, 20)):
            grid = gen.generate(
                17,
                4,
                difficulty="hard",
                texture=texture,
                grid_h=height,
                grid_w=width,
            )
            assert (len(grid), len(grid[0])) == (height, width)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {
                "grid_h": height,
                "grid_w": width,
            }
            assert gen.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"grid_h": 4},
        {"grid_h": 19},
        {"grid_w": 5},
        {"grid_w": 21},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"texture": "not-a-profile"},
        {"texture": 3},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


def test_every_band_gets_canonical_anchor_support_in_each_cycle():
    canonical_profiles = {(5, 6, 4), (5, 7, 4)}
    for band in ("easy", "medium", "hard"):
        observed = []
        strict = 0
        for index in range(15):
            grid = gen.generate(91, index, difficulty=band)
            observed.append(
                (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
            )
            strict += bool(gen.strict_canonical_like(grid))
        assert sum(profile in canonical_profiles for profile in observed) >= 6
        assert strict >= 6


def test_only_real_canonical_shortcuts_are_declared_and_counterexampled():
    assert set(gen.CANONICAL_SHORTCUTS) == {"group_by_color", "sort_by_height"}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL_PAIRS), name
        assert any(
            rival(gen.generate(301, index)) != gen.rule_mirror(gen.generate(301, index))
            for index in range(gen.EXAMPLES_NEEDED)
        ), name


def test_named_profiles_supply_the_intended_semantic_witnesses():
    expected = {
        "order_conflict": {"ordering"},
        "bbox_metric": {"area_metric"},
        "alignment_gap_shape": {"vertical_alignment", "separator", "shape_preservation"},
        "shared_color": {"component_identity"},
    }
    for texture, witness_names in expected.items():
        grid = gen.generate(401, 7, texture=texture, grid_h=5, grid_w=6)
        for name in witness_names:
            assert gen.SEMANTIC_WITNESSES[name](grid), (texture, name)


def test_self_check_rejects_malformed_ambiguous_and_touching_scenes():
    invalid = [None, [], [[]], [[0], [0, 1]], [[True] * 6 for _ in range(5)]]
    for grid in invalid:
        assert gen.self_check(grid)

    tied = [
        [1, 0, 2, 0, 0, 0],
        [1, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [3, 3, 3, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert any("distinct" in reason for reason in gen.self_check(tied))

    touching = [
        [1, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [3, 3, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    assert any("touch" in reason for reason in gen.self_check(touching))


def test_distribution_is_deterministic_fresh_and_nontrivial():
    inputs = set()
    outputs = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(60):
            grid = gen.generate(700 + band_index, index, difficulty=band)
            replay = gen.generate(700 + band_index, index, difficulty=band)
            assert grid == replay
            assert grid is not replay
            assert all(row is not replay_row for row, replay_row in zip(grid, replay))
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, gen.rule_mirror(grid))))
    assert len(inputs) >= 160
    assert len(outputs) >= 145


def test_source_bound_lesson_probe_has_no_surviving_declared_competitor():
    probe_path = HOME / "workspace/lesson_probe.py"
    spec = importlib.util.spec_from_file_location("lesson_probe_under_test", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.run_probe(lessons_per_band=3)
    assert report["status"] == "PASS"
    assert report["generator_sha256"]
    assert report["canonical_shortcuts_fit"] == {
        "group_by_color": True,
        "sort_by_height": True,
    }
    for band in ("easy", "medium", "hard"):
        assert report["bands"][band]["identifiable_lessons"] == 3
        assert report["bands"][band]["unidentifiable_lessons"] == 0
        assert not report["bands"][band]["query_changing_survivors"]

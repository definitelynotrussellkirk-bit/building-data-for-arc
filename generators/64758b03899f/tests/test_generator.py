"""Task-local regressions for the 64758b03899f mask-stamping sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

TASK_ID = "64758b03899f"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _mask_facts(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    assert cells
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    normalized = tuple(sorted((r - r0, c - c0) for r, c in cells))
    return (r0, c0), normalized


def _anchors(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value not in (0, 5)]


def _reference(grid, *, first_cell_origin=False, keep_source=False, bbox=False,
               first_anchor_only=False, mask_color=False):
    h, w = len(grid), len(grid[0])
    mask = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    if first_cell_origin:
        r0, c0 = min(mask)
    else:
        r0 = min(r for r, _ in mask)
        c0 = min(c for _, c in mask)
    offsets = {(r - r0, c - c0) for r, c in mask}
    if bbox:
        min_dr = min(r for r, _ in offsets)
        max_dr = max(r for r, _ in offsets)
        min_dc = min(c for _, c in offsets)
        max_dc = max(c for _, c in offsets)
        offsets = {(r, c) for r in range(min_dr, max_dr + 1)
                   for c in range(min_dc, max_dc + 1)}
    out = [[0] * w for _ in range(h)]
    if keep_source:
        for r, c in mask:
            out[r][c] = 5
    anchors = _anchors(grid)
    if first_anchor_only:
        anchors = anchors[:1]
    for ar, ac, color in anchors:
        for dr, dc in offsets:
            r, c = ar + dr, ac + dc
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = 5 if mask_color else color
    return out


def test_rule_hash_pins_selected_authority():
    assert getattr(gen, "RULE_HASH", None) == "daa4a7279074"


def test_canonical_pairs_match_independent_reference_and_are_accepted():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert _reference(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_and_observable_in_every_band(band):
    requested = {
        "grid_h": 10,
        "grid_w": 14,
        "mask_family": "hollow_corner3",
        "n_anchors": 3,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert grid == gen.generate(17, 9, difficulty=band, **requested)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 8},
        {"grid_h": 14},
        {"grid_w": 11},
        {"grid_w": 19},
        {"grid_w": True},
        {"grid_h": 10.5},
        {"mask_family": "not-a-mask"},
        {"mask_family": 7},
        {"n_anchors": 1},
        {"n_anchors": 4},
        {"n_anchors": "3"},
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_default_distribution_covers_canonical_profiles_and_hollow_origin():
    canonical_profiles = {(10, 14, 4), (11, 15, 4), (9, 13, 5), (10, 16, 4), (11, 15, 5)}
    for band in ("easy", "medium", "hard"):
        profiles = set()
        families = set()
        counts = set()
        origins = set()
        palettes = set()
        for index in range(96):
            grid = gen.generate(3100, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(3100, index, difficulty=band)
            observed = gen.observe_overrides(grid)
            families.add(observed["mask_family"])
            counts.add(observed["n_anchors"])
            origins.add(_mask_facts(grid)[0])
            palette_size = len({value for row in grid for value in row})
            profiles.add((len(grid), len(grid[0]), palette_size))
            palettes.update(value for row in grid for value in row if value not in (0, 5))
        assert profiles & canonical_profiles
        assert {2, 3} <= counts
        assert "hollow_corner3" in families
        assert len(families) >= 6
        assert len(origins) >= 8
        assert {1, 9} <= palettes


def test_every_four_slot_schedule_contains_hollow_origin_and_nonrectangle():
    for band in ("easy", "medium", "hard"):
        for start in range(0, 24):
            grids = [gen.generate(9001, start + offset, difficulty=band) for offset in range(4)]
            normalized = [_mask_facts(grid)[1] for grid in grids]
            assert any((0, 0) not in shape for shape in normalized)
            assert any(len(shape) < (max(r for r, _ in shape) + 1) *
                       (max(c for _, c in shape) + 1) for shape in normalized)


def test_first_mask_cell_shortcut_fits_canonical_but_generated_witness_refutes_it():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert all(_reference(pair["input"], first_cell_origin=True) == pair["output"]
               for pair in pairs)

    witness = gen.generate(
        91,
        4,
        grid_h=10,
        grid_w=14,
        mask_family="hollow_corner3",
        n_anchors=2,
    )
    intended = _reference(witness)
    shortcut = _reference(witness, first_cell_origin=True)
    assert intended != shortcut
    assert gen.rule_mirror(witness) == intended
    assert gen.SEMANTIC_WITNESSES["bbox_origin_without_mask_cell"](witness)
    assert gen.SEMANTIC_RIVALS["use_first_mask_cell_as_origin"](witness) == shortcut
    assert gen.CANONICAL_SHORTCUTS["use_first_mask_cell_as_origin"](witness) == shortcut
    assert gen.LESSON_COMPETITORS["use_first_mask_cell_as_origin"](witness) == shortcut


def test_declared_rivals_are_real_counterrules_on_generated_inputs():
    grid = gen.generate(421, 1, mask_family="hollow_stair4", n_anchors=3)
    intended = _reference(grid)
    expected = {
        "leave_only_anchor_markers": [[0 if value == 5 else value for value in row] for row in grid],
        "fill_mask_bounding_box": _reference(grid, bbox=True),
        "stamp_only_first_anchor": _reference(grid, first_anchor_only=True),
        "keep_source_mask": _reference(grid, keep_source=True),
        "use_first_mask_cell_as_origin": _reference(grid, first_cell_origin=True),
        "stamp_in_mask_color": _reference(grid, mask_color=True),
    }
    for name, rival_output in expected.items():
        assert gen.SEMANTIC_RIVALS[name](grid) == rival_output
        assert rival_output != intended


def test_self_check_rejects_malformed_and_destructive_mutations():
    for malformed in (None, [], [[]], [[0, 0], [0]], [[11]], [[True, 0], [0, 0]]):
        assert gen.self_check(malformed)

    grid = gen.generate(77, 3, mask_family="hollow_corner3", n_anchors=3)
    assert gen.self_check(grid) == []

    no_mask = deepcopy(grid)
    for r, row in enumerate(no_mask):
        for c, value in enumerate(row):
            if value == 5:
                no_mask[r][c] = 0
    assert gen.self_check(no_mask)

    duplicate_color = deepcopy(grid)
    anchors = _anchors(duplicate_color)
    duplicate_color[anchors[1][0]][anchors[1][1]] = anchors[0][2]
    assert gen.self_check(duplicate_color)

    unknown = deepcopy(grid)
    for r, row in enumerate(unknown):
        for c, value in enumerate(row):
            if value == 0:
                unknown[r][c] = 10
                break
        else:
            continue
        break
    assert gen.self_check(unknown)


def test_retained_first_mask_cell_counterexample_is_exact_and_replayable():
    import json

    path = HOME / "counterexamples" / "first-mask-cell-origin.json"
    record = json.loads(path.read_text())
    assert record["task_id"] == TASK_ID
    assert record["seed"] == 91
    assert record["sample_index"] == 4
    assert record["overrides"] == {
        "grid_h": 10,
        "grid_w": 14,
        "mask_family": "hollow_corner3",
        "n_anchors": 2,
    }
    grid = gen.generate(record["seed"], record["sample_index"], **record["overrides"])
    assert grid == record["input"]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == record["intended_output"]
    assert gen.CANONICAL_SHORTCUTS[record["rival_name"]](grid) == record["rival_output"]
    assert record["intended_output"] != record["rival_output"]
    actual_differences = [
        [r, c, record["intended_output"][r][c], record["rival_output"][r][c]]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if record["intended_output"][r][c] != record["rival_output"][r][c]
    ]
    assert actual_differences == record["differing_cells"]


def test_every_five_pair_lesson_keeps_hollow_origin_after_any_query_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            grids = [gen.generate(8128, start + offset, difficulty=band) for offset in range(5)]
            for query_index in range(5):
                demos = [grid for index, grid in enumerate(grids) if index != query_index]
                assert any((0, 0) not in _mask_facts(grid)[1] for grid in demos), (
                    band,
                    start,
                    query_index,
                    [gen.observe_overrides(grid)["mask_family"] for grid in grids],
                )

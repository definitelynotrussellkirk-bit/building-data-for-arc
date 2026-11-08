"""Focused regressions for the 5d3738a6b89c generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    clipping_surfaces,
    load_generator,
    observed,
    outer_border_ignored_output,
    painted_footprints,
    parse,
    reference_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    assert gen.RULE_HASH == "f9d79bf79624"
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_advertised_override_is_exact_in_every_band(band):
    options = {"grid_h": 11, "n_boxes": 4, "mask_size": 6, "edge_mode": "mixed"}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 10), ("grid_h", 16), ("grid_h", True), ("grid_h", "11"),
        ("n_boxes", 1), ("n_boxes", 5), ("n_boxes", 2.5),
        ("mask_size", 1), ("mask_size", 7),
        ("edge_mode", "edge"), ("edge_mode", 1),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_covers_all_declared_branches_and_canonical_profile(band):
    shapes, box_counts, mask_sizes, edge_modes = set(), set(), set(), set()
    canonical_profile_hits = 0
    for index in range(256):
        grid = gen.generate(2100 + index, index * 11, difficulty=band)
        assert grid == gen.generate(2100 + index, index * 11, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        shapes.add((len(grid), len(grid[0])))
        box_counts.add(stats["n_boxes"])
        mask_sizes.add(stats["mask_size"])
        edge_modes.add(stats["edge_mode"])
        if (len(grid), len(grid[0]), len({v for row in grid for v in row})) == (11, 11, 5):
            canonical_profile_hits += 1
    assert canonical_profile_hits > 0
    assert box_counts == {2, 3, 4}
    assert mask_sizes == {2, 3, 4, 5, 6}
    assert edge_modes == {"interior", "mixed"}
    assert len(shapes) >= 8


def test_generated_instances_have_two_nonoverlapping_anchors_per_key():
    for index in range(256):
        grid = gen.generate(700 + index, index * 5, difficulty="hard")
        info = parse(grid)
        assert {len(anchors) for anchors in info["anchors"].values()} == {2}
        footprints = painted_footprints(grid)
        for i, left in enumerate(footprints):
            for right in footprints[i + 1:]:
                assert not (left[2] & right[2]), (left, right, grid)


def test_first_anchor_shortcut_fits_canonical_but_is_refuted_by_every_generated_grid():
    rival = gen.CANONICAL_SHORTCUTS["first_anchor_per_key_only"]
    assert rival is gen.SEMANTIC_RIVALS["first_anchor_per_key_only"]
    assert rival is gen.LESSON_COMPETITORS["first_anchor_per_key_only"]
    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]
    for index in range(128):
        grid = gen.generate(900 + index, index, difficulty="medium")
        assert gen.SEMANTIC_WITNESSES["repeated_key_anchors"](grid)
        assert rival(grid) == reference_output(grid, first_anchor_only=True)
        assert rival(grid) != reference_output(grid)


@pytest.mark.parametrize(
    "mutation",
    ["unknown_color", "separator_hole", "prototype_center", "unequal_anchor_counts", "overlap"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(44, 3, grid_h=11, n_boxes=3, mask_size=5, edge_mode="interior")
    info = parse(grid)
    changed = deepcopy(grid)
    if mutation == "unknown_color":
        changed[-1][-1] = 5 if 5 not in info["anchors"] else 1
    elif mutation == "separator_hole":
        changed[info["sep"]][0] = 0
    elif mutation == "prototype_center":
        left, _ = info["boxes"][0]
        changed[1][left + 1] = 0
    elif mutation == "unequal_anchor_counts":
        key = info["prototypes"][0]["key"]
        r, c = info["anchors"][key][0]
        changed[r][c] = 0
    elif mutation == "overlap":
        first, second = info["prototypes"][:2]
        r, c = info["anchors"][first["key"]][0]
        old_r, old_c = info["anchors"][second["key"]][0]
        changed[old_r][old_c] = 0
        changed[r][c + 1] = second["key"]
    assert gen.self_check(changed)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(11)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_keyed_generation_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


@pytest.mark.parametrize("mask_size", [2, 3, 4, 5, 6])
@pytest.mark.parametrize("n_boxes", [2, 4])
def test_mixed_mode_constructs_separator_and_outer_grid_clipping(mask_size, n_boxes):
    grid = gen.generate(81 + mask_size, n_boxes, grid_h=11, n_boxes=n_boxes, mask_size=mask_size, edge_mode="mixed")
    surfaces = clipping_surfaces(grid)
    assert "separator" in surfaces
    assert surfaces & {"left", "right", "bottom"}
    assert gen.observe_overrides(grid)["edge_mode"] == "mixed"
    rival = gen.SEMANTIC_RIVALS["outer_border_anchor_ignored"]
    assert rival(grid) == outer_border_ignored_output(grid)
    if mask_size >= 3:
        assert rival(grid) != reference_output(grid)


def test_outer_border_shortcut_fits_canonical_but_is_scheduled_out():
    rival = gen.CANONICAL_SHORTCUTS["outer_border_anchor_ignored"]
    assert rival is gen.SEMANTIC_RIVALS["outer_border_anchor_ignored"]
    assert rival is gen.LESSON_COMPETITORS["outer_border_anchor_ignored"]
    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            grids = [gen.generate(9100 + start, start + offset, difficulty=band) for offset in range(gen.EXAMPLES_NEEDED)]
            modes = {observed(grid)["edge_mode"] for grid in grids}
            assert "mixed" in modes
            assert any(gen.SEMANTIC_WITNESSES["outer_grid_clipping"](grid) for grid in grids)
            assert any(rival(grid) != reference_output(grid) for grid in grids)


def test_every_query_rotation_retains_an_outer_clipping_demonstration():
    rival = gen.CANONICAL_SHORTCUTS["outer_border_anchor_ignored"]
    assert set(gen.SCHEDULE_EDGE_MODES) == {"interior", "mixed"}
    for band in (None, "easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            episode = [
                gen.generate(13_000, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_index, query_grid in enumerate(episode):
                demo_grids = [grid for index, grid in enumerate(episode) if index != query_index]
                demos = [{"input": grid, "output": reference_output(grid)} for grid in demo_grids]
                query = {"input": query_grid, "output": reference_output(query_grid)}
                assert any(rival(grid) != reference_output(grid) for grid in demo_grids)
                assert gen.lesson_identifiable(demos, query) == []


def test_rule_mirror_and_both_declared_rivals_match_independent_probe():
    assert gen.EXAMPLES_NEEDED == 2
    assert set(gen.SEMANTIC_RIVALS) == {"first_anchor_per_key_only", "outer_border_anchor_ignored"}
    for index in range(64):
        grid = gen.generate(12_000 + index, index, difficulty="hard")
        assert gen.rule_mirror(grid) == reference_output(grid)
        assert gen.SEMANTIC_RIVALS["outer_border_anchor_ignored"](grid) == outer_border_ignored_output(grid)

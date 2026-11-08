"""Focused regressions for the b6452f922704 overlap-gallery sampler."""
from __future__ import annotations

import copy
import json
import os
import random
import sys
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "b6452f922704"
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    gallery_output,
    is_vertical_centering_witness,
    load_generator,
    observed_axes,
    overlap_parts,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
ROOT = find_root(__file__)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def test_rule_pin_and_canonical_repeated_keys_are_lawful() -> None:
    assert GEN.RULE_HASH == "abfc4a89f098"
    assert len(PAIRS) >= 4
    saw_repeat = False
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        keys = [part["key"] for part in overlap_parts(pair["input"])]
        saw_repeat |= len(set(keys)) < len(keys)
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert gallery_output(pair["input"]) == pair["output"]
        assert pair["input"] == original
    assert saw_repeat


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
@pytest.mark.parametrize(
    "requested",
    (
        {"frame_h": 6, "frame_w": 8, "key_variety": 1},
        {"frame_h": 7, "frame_w": 7, "key_variety": 2},
        {"frame_h": 8, "frame_w": 6, "key_variety": 3},
    ),
)
def test_every_exact_override_is_honored_in_every_band(
    band: str | None, requested: dict[str, int]
) -> None:
    grid = GEN.generate(734, 19, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert observed_axes(grid) == requested
    assert GEN.observe_overrides(grid) == requested
    assert gallery_output(grid) != GEN.SEMANTIC_RIVALS["top_align"](grid)


@pytest.mark.parametrize(
    "kwargs",
    (
        {"typo_axis": 1},
        {"frame_h": 5},
        {"frame_h": 9},
        {"frame_w": 5},
        {"frame_w": 9},
        {"key_variety": 0},
        {"key_variety": 4},
        {"frame_h": True},
        {"frame_w": 7.0},
        {"key_variety": "2"},
    ),
)
def test_unknown_and_invalid_overrides_fail_loudly(kwargs: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


def test_canonical_top_alignment_shortcut_and_generated_counterexamples() -> None:
    rival = GEN.CANONICAL_SHORTCUTS["top_align"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)
    for band in (None, "easy", "medium", "hard"):
        lesson = []
        for index in range(GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(911, index, difficulty=band)
            output = gallery_output(grid)
            assert is_vertical_centering_witness(grid)
            assert GEN.SEMANTIC_WITNESSES["vertical_centering"](grid)
            assert rival(grid) != output
            lesson.append({"input": grid, "output": output})
        assert GEN.lesson_identifiable(lesson[:-1], lesson[-1]) == []


def test_saved_top_align_counterexample_is_exact_and_racket_checked() -> None:
    path = HOME / "counterexamples" / "top_align_vertical_centering.json"
    record = json.loads(path.read_text())
    assert record["task_id"] == TASK_ID
    assert record["generator_sha256"] == "507c68b8d9eb31fcc3a86d999854acfada8bc269438724a91b5fc4b22c7e9b4c"
    assert GEN.self_check(record["input"]) == []
    assert gallery_output(record["input"]) == record["intended_output"]
    assert GEN.CANONICAL_SHORTCUTS["top_align"](record["input"]) == record["rival_output"]
    assert record["intended_output"] != record["rival_output"]
    assert record["racket_output_matches_independent_oracle"] is True


def test_default_distribution_is_deterministic_diverse_and_representative() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        realized = set()
        shapes = set()
        signatures = set()
        repeated_keys = 0
        canonical_profiles = 0
        for index in range(128):
            seed = 18000 + band_index * 1000 + index
            grid = GEN.generate(seed, index * 11 + 3, difficulty=band)
            assert grid == GEN.generate(seed, index * 11 + 3, difficulty=band)
            assert GEN.self_check(grid) == []
            axes = GEN.observe_overrides(grid)
            assert axes == observed_axes(grid)
            realized.add(tuple(sorted(axes.items())))
            shapes.add((len(grid), len(grid[0])))
            signatures.add(tuple(map(tuple, grid)))
            keys = [part["key"] for part in overlap_parts(grid)]
            repeated_keys += len(set(keys)) < len(keys)
            canonical_profiles += (
                (len(grid), len(grid[0])) == (11, 25)
                and len({cell for row in grid for cell in row}) in (5, 6)
            )
        assert {dict(values)["frame_h"] for values in realized} == {6, 7, 8}
        assert {dict(values)["frame_w"] for values in realized} == {6, 7, 8}
        assert {dict(values)["key_variety"] for values in realized} == {1, 2, 3}
        assert len(shapes) == 9
        assert len(signatures) >= 120
        assert repeated_keys >= 40
        assert canonical_profiles >= 32


def test_self_check_rejects_malformed_and_structural_impostors_without_raising() -> None:
    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 25 for _ in range(11)]):
        errors = GEN.self_check(malformed)
        assert isinstance(errors, list) and errors

    grid = GEN.generate(44, 7, frame_h=7, frame_w=7, key_variety=2)
    no_key = copy.deepcopy(grid)
    first = overlap_parts(no_key)[0]
    r0, c0 = first["origin"]
    for col in range(c0, c0 + first["frame_w"]):
        if no_key[r0 - 1][col] not in (0, 9):
            no_key[r0 - 1][col] = 0
    assert any("key" in reason for reason in GEN.self_check(no_key))

    broken_frame = copy.deepcopy(grid)
    broken_frame[r0][c0] = 0
    assert GEN.self_check(broken_frame)

    bad_color = copy.deepcopy(grid)
    bad_color[0][0] = 10
    assert GEN.self_check(bad_color)


def test_global_rng_purity_and_fresh_return_values() -> None:
    random.seed(120901)
    before = random.getstate()
    first = GEN.generate(444, 9, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(444, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 8
    assert first != second

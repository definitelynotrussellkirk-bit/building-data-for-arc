"""Focused regression tests for the zero-mask self-tile generator repair."""
from __future__ import annotations

import copy
import json
import random
from itertools import product
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base
from arcpuzzles import Catalog
from reviewer_support import (
    canonical_pairs as read_canonical_pairs,
    find_root,
    load_selected_generator,
)

ROOT = find_root(__file__)
TASK_ID = "4ecf2a93671f"
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def canonical_pairs(task_id):
    return read_canonical_pairs(task_id, root=ROOT, labeled_only=True)


def _authority_path():
    target = "data/base/solutions/training/8e2edd66__4ecf2a93671f.json"
    mapping = json.loads((ROOT / "catalog/runtime_files.json").read_text())
    relative = next(item["path"] for item in mapping if item["target"] == target)
    source = ROOT / relative
    return source if source.is_file() else ROOT / target


def _canonical_row() -> dict:
    return Catalog(ROOT).get(TASK_ID)["variants"][0]


def test_rule_hash_selected_authority_and_all_canonical_pairs() -> None:
    row = _canonical_row()
    assert GEN.RULE_HASH == Catalog(ROOT).describe(TASK_ID)["rule_hash"]

    target = json.loads(_authority_path().read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != target["target_code"]

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_fixed_side3_is_a_real_canonical_shortcut() -> None:
    rival = GEN.CANONICAL_SHORTCUTS["fixed_side3_output"]
    pairs = canonical_pairs(TASK_ID)
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_boundary_overrides_are_exact_observable_and_valid(difficulty: str) -> None:
    for index, (side, fg_color, bg_count) in enumerate(
        product((3, 5), (1, 9), (3, 7))
    ):
        requested = {"side": side, "fg_color": fg_color, "bg_count": bg_count}
        grid = GEN.generate(
            73_000 + index,
            index * 31 + 7,
            difficulty=difficulty,
            **requested,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == requested


def test_default_draw_provenance_matches_realized_exact_axes() -> None:
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            for index in range(24):
                grid = GEN.generate(91_000 + index, index * 19 + 11, difficulty=band)
                draws = captured[-1].recorded_draws()
                assert GEN.observe_overrides(grid) == {
                    axis: draws[axis] for axis in GEN.AXES
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_default_draws_refute_all_single_scene_rivals() -> None:
    for band in ("easy", "medium", "hard"):
        for index in range(48):
            grid = GEN.generate(110_000 + index, index * 37 + 5, difficulty=band)
            expected = GEN.rule_mirror(grid)
            assert GEN.self_check(grid) == []
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                if name == "fixed_side3_output" and len(grid) == 3:
                    continue
                assert rival(grid) != expected, (band, index, name)


def test_every_three_demo_sliding_window_identifies_rule() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = []
            for offset in range(4):
                grid = GEN.generate(220_000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
            assert any(len(pair["input"]) != 3 for pair in pairs[:3])


def test_targeted_rule_hiding_impostors_are_rejected() -> None:
    impostors = {
        "short_foreground_line": [[1, 1, 1], [0, 0, 0], [0, 0, 0]],
        "solid_foreground_rectangle": [[1, 1, 0], [1, 1, 0], [0, 0, 0]],
        "single_zero": [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
        "missing_zero": [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
        "extra_palette_color": [[1, 1, 0], [0, 2, 1], [0, 1, 0]],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_with_absent_replacement_color_is_rejected() -> None:
    grid = GEN.generate(12_345, 67, difficulty="hard")
    mutation = copy.deepcopy(grid)
    used = {value for row in mutation for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    zero_r, zero_c = next(
        (r, c)
        for r, row in enumerate(mutation)
        for c, value in enumerate(row)
        if value == 0
    )
    mutation[zero_r][zero_c] = replacement
    remaining = [
        value
        for r, row in enumerate(mutation)
        for c, value in enumerate(row)
        if (r, c) != (zero_r, zero_c)
    ]
    assert replacement not in remaining
    assert GEN.self_check(mutation)


def test_replay_fresh_returns_and_global_rng_state() -> None:
    random.seed(20260815)
    before = random.getstate()
    first = GEN.generate(512, 23, difficulty="hard")
    middle = GEN.generate(513, 24, difficulty="easy")
    second = GEN.generate(512, 23, difficulty="hard")
    after = random.getstate()

    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert first != middle

    snapshot = copy.deepcopy(first)
    second[0][0] = 9 if second[0][0] != 9 else 8
    assert first == snapshot
    assert GEN.generate(512, 23, difficulty="hard") == snapshot


def test_unknown_and_out_of_range_overrides_fail_closed() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=4)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, side=2)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, fg_color=0)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, bg_count=8)

from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application
from puzzle_generators import base as gen_base
from puzzle_generators.per_puzzle.d65971416c2d import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


BANDS = ("easy", "medium", "hard")


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/f6c2fd26c5e5/M71__d65971416c2d.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _find_clear_cell(grid: list[list[int]], *, margin: int = 1) -> tuple[int, int]:
    height = len(grid)
    width = len(grid[0])
    occupied = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    for row in range(1, height):
        for col in range(width):
            if all(
                (row + dr, col + dc) not in occupied
                for dr in range(-margin, margin + 1)
                for dc in range(-margin, margin + 1)
                if 0 <= row + dr < height and 0 <= col + dc < width
            ):
                return row, col
    raise AssertionError("test fixture has no clear background cell")


def _absent_nonzero_color(grid: list[list[int]]) -> int:
    palette = {value for row in grid for value in row}
    return next(color for color in range(1, 10) if color not in palette)


def test_canonical_pairs_are_accepted_and_rule_mirror_is_exact() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_selected_rule_sources_are_synchronized_exact_and_reentrant() -> None:
    row = _canonical_row()
    source = row["program_solution"]
    target = json.loads(BASE.read_text(encoding="utf-8"))["racket_target"]
    assert _normalized_rule_hash(source) == gen.RULE_HASH == "93b94c98bc36"
    assert target["target_code"] == source
    assert target["raw_code"] == source
    assert target["target_code_role"] == "selected_task_rule_commented_true_source"
    assert target["raw_code_role"] == "archival_executable_source_exact_selected"

    pairs = canonical_pairs(gen.TASK_ID)
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for pair in pairs:
            original = copy.deepcopy(pair["input"])
            assert bridge.eval_text(rule_application(source, pair["input"])) == pair["output"]
            assert pair["input"] == original
        probe = bridge.eval_text(purity_body(source, pairs[0]["input"], pairs[1]["input"]))
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


def test_replay_is_fresh_deterministic_band_distinct_and_rng_neutral() -> None:
    random.seed(20260728)
    state = random.getstate()
    first = gen.generate(81, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(81, 7, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert first != second

    band_draws = [gen.generate(917, 3, difficulty=band) for band in BANDS]
    assert len({repr(grid) for grid in band_draws}) >= 2


def test_all_declared_axes_are_exact_observable_and_unknowns_reject() -> None:
    domains = {
        "size_profile": gen.SIZE_PROFILES,
        "control_code": (1, 2, 3, 4),
        "template_profile": gen.TEMPLATE_PROFILES,
        "anchor_zone": gen.ANCHOR_ZONES,
        "extra_red": (False, True),
        "decoy_count": (1, 2),
    }
    for axis, values in domains.items():
        for value in values:
            grid = gen.generate(7100, 0, difficulty="medium", **{axis: value})
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid)[axis] == value

    for band in BANDS:
        requested = {
            "size_profile": "h13_w13",
            "control_code": 4,
            "template_profile": "tetra_t",
            "anchor_zone": "lower_right",
            "extra_red": True,
            "decoy_count": 2,
        }
        grid = gen.generate(7110, 11, difficulty=band, **requested)
        assert gen.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, obsolete_axis="legacy")
    with pytest.raises(ValueError):
        gen.generate(0, 0, control_code=5)
    with pytest.raises(ValueError):
        gen.generate(0, 0, decoy_count=3)


def test_ordinary_draw_provenance_matches_observed_axes() -> None:
    captured = []
    gen_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(BANDS):
            for sample_index in range(8):
                grid = gen.generate(7200 + band_index, sample_index, difficulty=band)
                ctx = captured[-1]
                recorded = ctx.recorded_draws()
                observed = gen.observe_overrides(grid)
                assert {name: recorded[name] for name in gen.AXES} == observed
                assert ctx.overrides_used() == {
                    name: recorded[name]
                    for name in ("control_code", "anchor_zone", "extra_red", "decoy_count")
                }
    finally:
        gen_base.set_ctx_observer(None)


def test_self_check_rejects_targeted_impostors_and_negative_recombination() -> None:
    valid = gen.generate(
        7300,
        0,
        difficulty="medium",
        size_profile="h13_w13",
        control_code=1,
        template_profile="tri_l",
        extra_red=False,
        decoy_count=1,
    )
    info = gen._analyze(valid)
    assert info["errors"] == []

    duplicate_control = copy.deepcopy(valid)
    empty_top = next(col for col, value in enumerate(duplicate_control[0]) if value == 0)
    duplicate_control[0][empty_top] = 4

    duplicate_anchor = copy.deepcopy(valid)
    row, col = _find_clear_cell(duplicate_anchor)
    duplicate_anchor[row][col] = 8

    connected_control = copy.deepcopy(valid)
    connected_control[1][info["control_col"]] = 1

    no_visible_template = copy.deepcopy(valid)
    replacement = _absent_nonzero_color(no_visible_template)
    for row, col in info["visible_template"]["cells"]:
        no_visible_template[row][col] = replacement

    malformed_template = copy.deepcopy(valid)
    row, col = next(iter(info["visible_template"]["cells"]))
    malformed_template[row][col] = 0

    anchor_overflow = copy.deepcopy(valid)
    anchor_row, anchor_col = info["anchor"]
    anchor_overflow[anchor_row][anchor_col] = 0
    anchor_overflow[-1][-1] = 8

    crowded = gen.generate(
        7301,
        3,
        difficulty="hard",
        size_profile="h13_w13",
        control_code=4,
        template_profile="tri_l",
        extra_red=True,
        decoy_count=1,
    )
    third_red = copy.deepcopy(crowded)
    row, col = _find_clear_cell(third_red)
    third_red[row][col] = 2

    for name, impostor in {
        "duplicate_control": duplicate_control,
        "duplicate_anchor": duplicate_anchor,
        "connected_control": connected_control,
        "missing_visible_template": no_visible_template,
        "malformed_template": malformed_template,
        "anchor_overflow": anchor_overflow,
        "third_red_component": third_red,
    }.items():
        assert gen.self_check(impostor), name

    # True negative recombination: replace the non-control red template by a
    # color absent from every remaining scene part.  The teaching grammar must
    # reject it, while the oracle still executes because red control 2 remains
    # the first red component and therefore still determines a one-cell answer.
    code_two = gen.generate(
        7302,
        1,
        difficulty="medium",
        control_code=2,
        extra_red=False,
        decoy_count=1,
    )
    code_two_info = gen._analyze(code_two)
    absent = _absent_nonzero_color(code_two)
    recombined = copy.deepcopy(code_two)
    for row, col in code_two_info["visible_template"]["cells"]:
        recombined[row][col] = absent
    remaining_palette = {
        value
        for row in code_two
        for value in row
        if value != 0 and value != absent
    }
    assert absent not in remaining_palette
    assert gen.self_check(recombined)
    assert gen.rule_mirror(recombined) == gen.rule_mirror(code_two)


def test_every_semantic_branch_has_a_rival_killing_witness() -> None:
    witnesses = {
        "control_1_identity": gen.generate(7400, 0, difficulty="easy"),
        "control_2_selects_red_control": gen.generate(7401, 1, difficulty="medium"),
        "control_3_half_turn": gen.generate(7402, 2, difficulty="hard"),
        "control_4_counterclockwise": gen.generate(7403, 3, difficulty="easy"),
        "first_red_is_not_largest": gen.generate(7404, 1, difficulty="hard"),
        "control_is_not_fixed_to_col0": gen.generate(7405, 3, difficulty="medium"),
    }
    for witness_name, grid in witnesses.items():
        expected = gen.rule_mirror(grid)
        assert gen.SEMANTIC_WITNESSES[witness_name](grid), witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected


def test_every_four_example_sliding_window_identifies_the_query() -> None:
    assert gen.EXAMPLES_NEEDED == 4
    for band_index, band in enumerate(BANDS):
        for start in range(12):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = gen.generate(
                    7500 + band_index * 100 + start,
                    sample_index,
                    difficulty=band,
                )
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []
            assert {
                gen.schedule_profile(0, start + offset, band)
                for offset in range(gen.EXAMPLES_NEEDED)
            } == set(gen.SCHEDULE_PROFILES)

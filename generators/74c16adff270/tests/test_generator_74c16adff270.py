from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators import base as gen_base
gen = importlib.import_module("puzzle_generators.per_puzzle.74c16adff270.generator")
from scripts.canonical_profile_gate import canonical_pairs
from scripts.rule_smoke import purity_body, rule_application


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/ce088a50599a/M159__74c16adff270.json"
BANDS = ("easy", "medium", "hard")


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _clear_cell(grid: list[list[int]], *, avoid_edge: bool = False) -> tuple[int, int]:
    height = len(grid)
    width = len(grid[0])
    occupied = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    row_range = range(1, height - 1) if avoid_edge else range(height)
    col_range = range(1, width - 1) if avoid_edge else range(width)
    for row in row_range:
        for col in col_range:
            if (row, col) in occupied:
                continue
            if all(
                (row + dr, col + dc) not in occupied
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if 0 <= row + dr < height and 0 <= col + dc < width
            ):
                return row, col
    raise AssertionError("fixture has no isolated background cell")


def test_all_canonical_pairs_are_accepted_and_rule_mirror_is_exact() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    signatures = set()
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        signatures.add(gen.canonical_profile_signature(pair["input"]))
    assert signatures == set(gen._CANONICAL_SIGNATURES)


def test_selected_rule_sources_are_comment_preserving_exact_and_reentrant() -> None:
    row = _canonical_row()
    source = row["program_solution"]
    target = json.loads(BASE.read_text(encoding="utf-8"))["racket_target"]
    assert _normalized_hash(source) == gen.RULE_HASH == "69c529d368d9"
    assert target["target_code"] == source
    assert target["raw_code"] == source
    assert target["target_code_role"] == "selected_task_rule_comment_preserving_authority"
    assert target["raw_code_role"] == "archival_executable_source_exact_selected"
    assert ";; Position of the first color 7 cell" in source

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


def test_replay_is_fresh_deterministic_and_global_rng_neutral() -> None:
    random.seed(20260729)
    state = random.getstate()
    first = gen.generate(81, 7, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(81, 7, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 5
    assert first != second


def test_all_declared_axes_are_exact_observable_and_unknowns_reject() -> None:
    domains = {
        "canonical_profile": gen.CANONICAL_PROFILES,
        "layout_profile": gen.LAYOUT_PROFILES,
        "row_profile": gen.ROW_PROFILES,
        "template_col_zone": gen.COLUMN_ZONES,
        "anchor_col_zone": gen.COLUMN_ZONES,
        "control_col_zone": gen.COLUMN_ZONES,
    }
    for axis, values in domains.items():
        for value in values:
            grid = gen.generate(7100, 0, difficulty="medium", **{axis: value})
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid)[axis] == value

    requested = {
        "canonical_profile": "ctrl6_zig5_w12",
        "layout_profile": "control_anchor_template",
        "row_profile": "rows_1_5_9",
        "template_col_zone": "right",
        "anchor_col_zone": "center",
        "control_col_zone": "left",
    }
    for band in BANDS:
        grid = gen.generate(7110, 11, difficulty=band, **requested)
        assert gen.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, obsolete_axis="legacy")
    with pytest.raises(ValueError):
        gen.generate(0, 0, canonical_profile="not_a_profile")
    with pytest.raises(ValueError):
        gen.generate(0, 0, anchor_col_zone="diagonal")


def test_ordinary_draw_provenance_matches_observed_axes() -> None:
    captured = []
    gen_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(BANDS):
            for sample_index in range(12):
                grid = gen.generate(7200 + band_index, sample_index, difficulty=band)
                ctx = captured[-1]
                recorded = ctx.recorded_draws()
                observed = gen.observe_overrides(grid)
                assert {name: recorded[name] for name in gen.AXES} == observed
                assert ctx.overrides_used() == {
                    "canonical_profile": recorded["canonical_profile"],
                    "layout_profile": recorded["layout_profile"],
                }
    finally:
        gen_base.set_ctx_observer(None)


def test_self_check_rejects_targeted_impostors_and_strict_rejects_recombination() -> None:
    valid = gen.generate(
        7300,
        0,
        difficulty="medium",
        canonical_profile="ctrl2_stair6_w14",
        layout_profile="template_anchor_control",
        row_profile="rows_0_4_8",
        template_col_zone="left",
        anchor_col_zone="center",
        control_col_zone="right",
    )
    analysis = gen._analyze(valid)
    assert analysis["errors"] == []

    duplicate_anchor = copy.deepcopy(valid)
    row, col = _clear_cell(duplicate_anchor)
    duplicate_anchor[row][col] = 7

    duplicate_control = copy.deepcopy(valid)
    row, col = _clear_cell(duplicate_control)
    duplicate_control[row][col] = 6

    disconnected_template = copy.deepcopy(valid)
    row, col = _clear_cell(disconnected_template)
    disconnected_template[row][col] = 1

    overflow = copy.deepcopy(valid)
    anchor_row, anchor_col = analysis["anchor"]
    overflow[anchor_row][anchor_col] = 0
    overflow[-1][-1] = 7

    illegal_color = copy.deepcopy(valid)
    row, col = _clear_cell(illegal_color)
    illegal_color[row][col] = 9

    touching_roles = copy.deepcopy(valid)
    control_row, control_col = analysis["control_cell"]
    touching_roles[control_row][control_col] = 0
    template_row, template_col = next(iter(analysis["template_cells"]))
    touching_roles[template_row][template_col - 1 if template_col else template_col + 1] = 2

    for name, impostor in {
        "duplicate_anchor": duplicate_anchor,
        "duplicate_control": duplicate_control,
        "disconnected_template": disconnected_template,
        "anchor_overflow": overflow,
        "illegal_color": illegal_color,
        "touching_roles": touching_roles,
    }.items():
        assert gen.self_check(impostor), name

    # Linked-profile recombination: ctrl=3 is absent from every remaining
    # scene part, and replacing the ctrl=2 cell leaves an oracle-valid scene.
    recombined = copy.deepcopy(valid)
    recombined[control_row][control_col] = 3
    remaining_palette = {
        value
        for row_values in valid
        for value in row_values
        if value not in (0, 2)
    }
    assert 3 not in remaining_palette
    assert gen.self_check(recombined) == []
    assert gen.strict_canonical_like(recombined)
    assert gen.rule_mirror(recombined) != gen.rule_mirror(valid)


def test_every_control_branch_has_rival_killing_witnesses() -> None:
    profiles = {
        "control_2_identity": "ctrl2_stair6_w14",
        "control_3_clockwise": "ctrl3_t4_w15",
        "control_4_half_turn": "ctrl4_cap5_w13",
        "control_6_counterclockwise": "ctrl6_zig5_w12",
    }
    for index, (witness_name, profile) in enumerate(profiles.items()):
        grid = gen.generate(
            7400 + index,
            index,
            difficulty=BANDS[index % len(BANDS)],
            canonical_profile=profile,
        )
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
            controls = {
                gen._analyze(pair["input"])["control"]
                for pair in pairs[:4]
            }
            assert controls == {2, 3, 4, 6}


def test_strict_linked_profile_census_is_complete_and_varied() -> None:
    for band_index, band in enumerate(BANDS):
        profile_counts = {name: 0 for name in gen.CANONICAL_PROFILES}
        rendered = set()
        for sample_index in range(200):
            grid = gen.generate(7600 + band_index, sample_index, difficulty=band)
            assert gen.strict_canonical_like(grid) == []
            profile_counts[gen.observe_overrides(grid)["canonical_profile"]] += 1
            rendered.add(repr(grid))
        assert all(count > 0 for count in profile_counts.values())
        assert len(rendered) >= 150

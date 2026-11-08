"""Focused semantic regressions for generator 8a8682f21e71."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.check_task_authority_sync import strip_racket_comments
from scripts.generator_module_loader import load_module_from_path
from scripts.rule_smoke import rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "8a8682f21e71"
GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
MODULE = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)
AUTHORITY_PATHS = (
    ROOT / "data/base/solutions/training/ba1aa698__8a8682f21e71.json",
    ROOT / "data/base/solutions/augmented/ba1aa698__d2216cd70de0.json",
)


def _canonical_rows() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 2
    return rows


def _pairs(row: dict) -> list[dict]:
    test = row.get("test", [])
    tests = [test] if isinstance(test, dict) else list(test)
    return [*row.get("train", []), *tests]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _selected_source() -> str:
    return json.loads(AUTHORITY_PATHS[0].read_text())["racket_target"]["target_code"]


def test_rule_hash_and_comment_preserving_source_roles() -> None:
    canonical = _canonical_rows()[0]["program_solution"]
    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "62f8e51d2975"
    assert MODULE.RULE_HASH == _normalized_hash(canonical)
    for path in AUTHORITY_PATHS:
        target = json.loads(path.read_text())["racket_target"]
        assert target["canonicalization_status"] == "selected_exact_canonical_comments_preserved_in_raw"
        assert target["target_code"] == canonical
        assert ";;" in target["raw_code"]
        assert " ".join(strip_racket_comments(target["target_code"]).split()) == " ".join(canonical.split())
        assert target["raw_code"] != target["target_code"]


def test_all_canonical_occurrences_pass_and_match_official_outputs() -> None:
    occurrences = 0
    unique_pairs = set()
    for row in _canonical_rows():
        for pair in _pairs(row):
            occurrences += 1
            unique_pairs.add(json.dumps(pair, sort_keys=True))
            assert MODULE.self_check(pair["input"], meta={"canonical": True}) == []
            assert MODULE.rule_mirror(pair["input"]) == pair["output"]
    assert occurrences == 8
    assert len(unique_pairs) == 4


def test_all_exact_axis_combinations_are_observable_in_every_band() -> None:
    sample = 0
    for difficulty in ("easy", "medium", "hard"):
        for box_w in (4, 5):
            for n_boxes in (3, 4):
                for step in MODULE.STEP_VALUES:
                    for marker_shape in MODULE.MARKER_SHAPES:
                        for palette_size in (2, 3):
                            overrides = {
                                "box_w": box_w,
                                "n_boxes": n_boxes,
                                "step": step,
                                "marker_shape": marker_shape,
                                "palette_size": palette_size,
                            }
                            grid = MODULE.generate(
                                7000 + sample,
                                sample,
                                difficulty=difficulty,
                                **overrides,
                            )
                            assert MODULE.observe_overrides(grid) == overrides
                            assert MODULE.self_check(
                                grid,
                                difficulty=difficulty,
                                meta={"overrides": overrides},
                            ) == []
                            sample += 1


def test_ordinary_draw_provenance_matches_observed_axes() -> None:
    original = MODULE.gen_ctx
    captured = []

    def recording_ctx(*args, **kwargs):
        ctx = original(*args, **kwargs)
        captured.append(ctx)
        return ctx

    MODULE.gen_ctx = recording_ctx
    try:
        for band_index, difficulty in enumerate(("easy", "medium", "hard")):
            for index in range(60):
                grid = MODULE.generate(
                    110_000 + band_index * 10_000 + index,
                    900 + index,
                    difficulty=difficulty,
                )
                ctx = captured[-1]
                keyed = {
                    axis: ctx.axis_value(axis)
                    for axis in MODULE.AXES
                }
                assert MODULE.observe_overrides(grid) == keyed
    finally:
        MODULE.gen_ctx = original


def test_every_sliding_five_example_lesson_is_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(25):
            pairs = []
            for offset in range(MODULE.EXAMPLES_NEEDED + 1):
                grid = MODULE.generate(
                    210_000 + start,
                    start + offset,
                    difficulty=difficulty,
                )
                pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
            assert MODULE.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_named_witnesses_refute_their_linked_rivals() -> None:
    witnesses = {}
    for sample_index in range(10):
        grid = MODULE.generate(333, sample_index, difficulty="hard")
        for name, predicate in MODULE.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                witnesses.setdefault(name, grid)
    assert set(witnesses) == set(MODULE.SEMANTIC_WITNESSES)
    for witness_name, grid in witnesses.items():
        true = MODULE.rule_mirror(grid)
        for rival_name in MODULE.WITNESS_RIVALS[witness_name]:
            assert MODULE.SEMANTIC_RIVALS[rival_name](grid) != true


def test_canonical_shortcuts_fit_public_pairs_but_generated_witnesses_refute() -> None:
    for row in _canonical_rows():
        for pair in _pairs(row):
            for rival in MODULE.CANONICAL_SHORTCUTS.values():
                assert rival(pair["input"]) == pair["output"]
    offset_witness = MODULE.generate(400, 1, difficulty="medium", box_w=5)
    height_witness = MODULE.generate(401, 3, difficulty="hard")
    assert MODULE._rival_fixed_column_one(offset_witness) != MODULE.rule_mirror(offset_witness)
    assert MODULE._rival_fixed_height_16(height_witness) != MODULE.rule_mirror(height_witness)


def test_self_check_rejects_all_targeted_mutations() -> None:
    fixtures = MODULE.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert MODULE.self_check(grid), name


def test_negative_recombination_rejected_while_racket_executes() -> None:
    grid = MODULE.generate(
        500,
        0,
        difficulty="medium",
        box_w=5,
        n_boxes=4,
        step="down1",
        marker_shape="line2",
        palette_size=3,
    )
    facts = MODULE._facts(grid)
    changed = copy.deepcopy(grid)
    second = facts["markers"][1]
    box_left = facts["border_columns"][1] + 1
    top = second["top"]
    left = second["left"]
    marker_color = facts["marker_color"]
    box_color = facts["box_color"]
    # Replace the second horizontal domino with a vertical domino.  The
    # replacement shape occurs nowhere else, so this is a real recombination,
    # not an extra copy of an existing feature.
    changed[top][box_left + left + 1] = box_color
    changed[top + 1][box_left + left] = marker_color
    errors = MODULE.self_check(changed)
    assert errors
    assert any("same marker shape" in error or "unsupported marker shape" in error for error in errors)

    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        output = bridge.eval_text(rule_application(_selected_source(), changed))
    finally:
        bridge.shutdown()
    assert isinstance(output, list)
    assert len(output) == len(changed)
    assert len(output[0]) == facts["box_w"] + 2


def test_determinism_fresh_returns_unknown_overrides_and_rng_isolation() -> None:
    random.seed(20260726)
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(901, 17, difficulty="hard") == second
    with pytest.raises(TypeError):
        MODULE.generate(1, 2, unknown_axis=3)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, step="sideways")

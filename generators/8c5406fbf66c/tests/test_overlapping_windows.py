"""Regression tests for canonical overlapping 2x2-window semantics."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "8c5406fbf66c"
ROOT = find_root(__file__)


@pytest.fixture(scope="module")
def generator():
    module, _path, _digest = load_selected_generator(TASK_ID, root=ROOT)
    return module


@pytest.fixture(scope="module")
def racket_bridge():
    with RacketBridge() as bridge:
        yield bridge


def _canonical_source() -> str:
    sources = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.add(row["program_solution"])
    assert len(sources) == 1
    return sources.pop()


def _overlap_witness(color: int = 4):
    return [[color, color, color], [color, color, color]]


def test_two_by_three_overlap_is_a_lawful_two_anchor_input(generator):
    witness = _overlap_witness()
    assert generator.self_check(witness) == []
    assert generator._active_anchors(witness) == [(0, 0), (0, 1)]


def test_real_canonical_racket_marks_both_overlapping_anchors(racket_bridge):
    witness = _overlap_witness()
    racket_bridge.define_grid("g", witness)
    actual = racket_bridge.eval_text(f"({wrap_rule(_canonical_source())} g)")
    assert actual == [[8, 8, 4], [4, 4, 4]]


def test_normal_schedule_emits_overlap_and_exact_requested_window_counts(generator):
    state = random.getstate()
    for difficulty, expected in (("easy", {2}), (None, {2, 3, 4}), ("hard", {3, 4})):
        observed = set()
        overlap_seen = False
        canonical_profile_seen = False
        for sample_index in range(18):
            grid = generator.generate(2718, sample_index, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            anchors = generator._active_anchors(grid)
            observed.add(len(anchors))
            overlap_seen |= any(
                abs(r1 - r2) + abs(c1 - c2) == 1
                for i, (r1, c1) in enumerate(anchors)
                for r2, c2 in anchors[i + 1 :]
            )
            canonical_profile_seen |= generator.strict_canonical_like(grid) == []
        assert observed <= expected and observed
        assert overlap_seen, "the default schedule must retain an overlap-teaching branch"
        assert canonical_profile_seen, "the default schedule must anchor a canonical profile"
    assert random.getstate() == state


def test_blocks_override_counts_active_windows_exactly(generator):
    for target in (2, 3, 4):
        grid = generator.generate(99, target, blocks=target)
        assert generator.self_check(grid) == []
        assert len(generator._active_anchors(grid)) == target


def test_self_check_accepts_legacy_isolated_blocks_but_rejects_uncovered_fragments(generator):
    legacy = [
        [2, 2, 0, 0, 3, 3],
        [2, 2, 0, 0, 3, 3],
        [0, 0, 0, 0, 0, 0],
        [4, 4, 0, 0, 0, 0],
        [4, 4, 0, 0, 0, 0],
    ]
    assert generator.self_check(legacy) == []

    fragmented = [
        [2, 2, 0, 0],
        [2, 2, 0, 0],
        [0, 0, 7, 0],
    ]
    errors = generator.self_check(fragmented)
    assert any("covered by an active 2x2 window" in error for error in errors)


def test_source_bound_contract_and_declared_controls(generator):
    assert generator.RULE_HASH == "29d77c7080ca"
    assert generator.AXES == {
        "grid_h": {"type": "int", "default": "canonical schedule or rng 4..16", "valid": "4..16"},
        "grid_w": {"type": "int", "default": "canonical schedule or rng 4..16", "valid": "4..16"},
        "blocks": {"type": "int", "default": "difficulty schedule in 2..4", "valid": "2..4"},
    }
    assert generator.EXAMPLES_NEEDED == 3
    assert generator.LESSON_SCHEDULE_PERIOD == 3
    assert set(generator.SCHEDULE_PROFILES) == {"canonical", "overlap"}


def test_canonical_inputs_are_strict_and_schedule_profiles_cover_every_three(generator):
    profiles = []
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []

    for start in range(9):
        window = [generator.schedule_profile(5, start + offset) for offset in range(3)]
        assert "canonical" in window
        assert "overlap" in window
        profiles.extend(window)
    assert set(profiles) == {"canonical", "overlap"}


def test_full_range_overrides_are_exact_and_strict(generator):
    cases = [
        (4, 4, 4),
        (16, 16, 2),
        (4, 16, 3),
        (16, 4, 4),
    ]
    for index, (height, width, blocks) in enumerate(cases):
        grid = generator.generate(121, index, grid_h=height, grid_w=width, blocks=blocks)
        assert (len(grid), len(grid[0])) == (height, width)
        assert len(generator._active_anchors(grid)) == blocks
        assert generator.self_check(grid) == []
        assert generator.observe_overrides(grid) == {
            "grid_h": height,
            "grid_w": width,
            "blocks": blocks,
        }

    for bad in (True, 2.0, "2"):
        with pytest.raises(TypeError):
            generator.generate(121, 0, blocks=bad)
    with pytest.raises(TypeError):
        generator.generate(True, 0)
    with pytest.raises(ValueError):
        generator.generate(121, -1)
    with pytest.raises(ValueError):
        generator.generate(121, 0, difficulty="impossible")
    with pytest.raises(TypeError):
        generator.generate(121, 0, difficulty=1.0)
    with pytest.raises(TypeError):
        generator.generate(121, 0, unknown_control=1)


def test_every_default_branch_records_all_exact_axis_provenance(generator, monkeypatch):
    contexts = []
    original = generator.gen_ctx

    def recording_ctx(*args, **kwargs):
        context = original(*args, **kwargs)
        contexts.append(context)
        return context

    monkeypatch.setattr(generator, "gen_ctx", recording_ctx)
    for sample_index in range(6):
        grid = generator.generate(404, sample_index, difficulty="hard")
        context = contexts[-1]
        observed = generator.observe_overrides(grid)
        assert set(context.recorded_draws()) >= set(generator.AXES)
        assert {name: context.axis_value(name) for name in generator.AXES} == observed


def test_semantic_witness_refutes_the_old_isolated_component_shortcut(generator):
    witness = _overlap_witness()
    canonical = generator.rule_mirror(witness)
    rival = generator.SEMANTIC_RIVALS["isolated_components_only"](witness)
    assert generator.SEMANTIC_WITNESSES["overlapping_windows"](witness)
    assert canonical == [[8, 8, 4], [4, 4, 4]]
    assert rival != canonical
    assert generator.WITNESS_RIVALS == {
        "overlapping_windows": ["isolated_components_only"]
    }


def test_every_default_three_demo_lesson_is_identifiable(generator):
    for difficulty in ("easy", "medium", "hard"):
        for start in range(6):
            pairs = []
            for sample_index in range(start, start + 4):
                grid = generator.generate(913, sample_index, difficulty=difficulty)
                pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
            for held_out in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                assert generator.lesson_identifiable(demos, pairs[held_out]) == []

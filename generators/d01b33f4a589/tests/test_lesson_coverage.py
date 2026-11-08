"""Regressions for command-identifying lessons; run directly from the repository."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest

TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
SOURCE = Path(os.environ.get("ARCPUZZLES_GENERATOR_SOURCE", TASK / "generator.py"))
spec = importlib.util.spec_from_file_location("reviewed_corner_generator", SOURCE)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def alias_four_as_three(grid):
    """An independently constructed rival, not the new declared contract."""
    rival_input = [row[:] for row in grid]
    for r, c in ((0, 0), (0, -1), (-1, 0), (-1, -1)):
        if rival_input[r][c] == 4:
            rival_input[r][c] = 3
    return g.rule_mirror(rival_input)


def test_reported_seed_661_demonstrates_command_four():
    demos = [g.generate(661, i, difficulty="easy") for i in range(4)]
    assert any(alias_four_as_three(x) != g.rule_mirror(x) for x in demos), (
        "seed=661/easy/samples=0..3 leaves command 4 -> 3 unrefuted"
    )


def test_four_demo_windows_have_a_jointly_informative_example():
    # A rectangular L4 has four distinct command outputs; the other legal
    # families can have equal transforms, so mere code presence is not enough.
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 17, 661, 20261002):
            draws = [g.generate(seed, i, difficulty=band) for i in range(11)]
            for start in range(8):
                assert any(
                    g.observe_overrides(x) == {
                        "scene_profile": "l4_9x9", "command_profile": "permutation"
                    }
                    for x in draws[start:start + 4]
                ), (band, seed, start)


def test_semantic_contract_is_declared():
    assert callable(getattr(g, "lesson_identifiable", None))
    assert callable(getattr(g, "schedule_profile", None))
    assert getattr(g, "LESSON_COMPETITORS", {})
    assert getattr(g, "CANONICAL_SHORTCUTS", {})


def _pairs(draws):
    return [{"input": x, "output": g.rule_mirror(x)} for x in draws]


def test_all_declared_rivals_refuted_at_every_cyclic_start():
    rivals = getattr(g, "LESSON_COMPETITORS", {})
    assert rivals, "the lesson gate must enumerate its actual tested rivals"
    for band in (None, "easy", "medium", "hard"):
        for seed in range(32):
            pairs = _pairs([g.generate(seed, i, difficulty=band) for i in range(12)])
            for start in range(8):
                demos, query = pairs[start:start + 4], pairs[start + 4]
                assert g.lesson_identifiable(demos, query) == [], (band, seed, start)
                for name, rival in rivals.items():
                    assert any(rival(p["input"]) != p["output"] for p in demos), (
                        band, seed, start, name
                    )


def test_shortcuts_really_fit_every_canonical_pair():
    row = next(json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()
               if json.loads(line).get("task_id") == g.TASK_ID)
    test = row["test"]
    pairs = row["train"] + (test if isinstance(test, list) else [test])
    shortcuts = getattr(g, "CANONICAL_SHORTCUTS", {})
    assert shortcuts
    for pair in pairs:
        inp = [[int(c) for c in row] for row in pair["input"]]
        out = [[int(c) for c in row] for row in pair["output"]]
        for name, shortcut in shortcuts.items():
            assert shortcut(inp) == out, name


def test_hook_detects_a_real_query_discriminating_rival_without_query_labels():
    assert callable(getattr(g, "lesson_identifiable", None))
    demos = _pairs([g.generate(90, i, scene_profile="l4_9x9", command_profile="repeat_two")
                    for i in range(4)])
    query = g.generate(91, 4, scene_profile="l4_9x9", command_profile="permutation")
    reasons = g.lesson_identifiable(demos, {"input": query})
    assert any("command_4_as_3" in reason for reason in reasons)
    assert g.lesson_identifiable(demos, {"input": query, "output": [[9]]}) == reasons


def test_valid_query_equivalence_does_not_require_all_four_commands():
    assert callable(getattr(g, "lesson_identifiable", None))
    # Reusing a demonstration as query is legitimate for this hook test,
    # though production lesson assembly correctly deduplicates it.
    inp = g.generate(22, 0, scene_profile="l3_9x9", command_profile="repeat_two")
    assert g.lesson_identifiable(_pairs([inp]), {"input": inp}) == []


def test_pinned_axes_are_respected_even_at_anchor_residues():
    for band in (None, "easy", "medium", "hard"):
        for profile in g.SCENE_PROFILES:
            for commands in g.COMMAND_PROFILES:
                for i in range(4):
                    overrides = {"scene_profile": profile, "command_profile": commands}
                    inp = g.generate(661, i, difficulty=band, **overrides)
                    assert g.observe_overrides(inp) == overrides
                    assert g.self_check(inp, difficulty=band, meta={"overrides": overrides}) == []


def test_schedule_determinism_and_input_purity():
    random.seed(20261002)
    state = random.getstate()
    first = g.generate(12, 5, difficulty="hard")
    assert random.getstate() == state
    assert first == g.generate(12, 5, difficulty="hard")
    frozen = json.dumps(first)
    for rival in getattr(g, "LESSON_COMPETITORS", {}).values():
        rival(first)
        assert json.dumps(first) == frozen
    first[0][0] = 9
    assert g.generate(12, 5, difficulty="hard")[0][0] != 9


def test_default_axis_provenance_is_on_the_last_created_context():
    # Shared override checkers inspect the last observed GenCtx. A phase-only
    # context created after the layout context used to hide both exact axes.
    from puzzle_generators.base import set_ctx_observer
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        grid = g.generate(0, 0, difficulty="easy")
    finally:
        set_ctx_observer(None)
    observed = g.observe_overrides(grid)
    assert contexts
    recorded = contexts[-1].recorded_draws()
    for axis, value in observed.items():
        assert recorded.get(axis) == value, (axis, recorded)

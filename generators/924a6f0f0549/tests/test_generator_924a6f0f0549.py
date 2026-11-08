from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (canonical_pairs, canonical_path, find_root,
                              load_selected_generator)

TASK_ID = "924a6f0f0549"
ROOT = find_root(__file__)
GEN, _GEN_PATH, _GEN_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _selected_source() -> str:
    sources: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    sources.add(source)
    assert len(sources) == 1
    return next(iter(sources))


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _marker_count(grid: list[list[int]]) -> int:
    return sum(value == 1 for value in grid[0])


def test_target_size_override_controls_marker_count_in_every_band() -> None:
    for difficulty in (None, "easy", "medium", "hard"):
        small = GEN.generate(703, 2, difficulty=difficulty, target_size=3)
        large = GEN.generate(703, 2, difficulty=difficulty, target_size=8)
        assert _marker_count(small) == 3
        assert _marker_count(large) == 8
        assert small != large
        assert GEN.self_check(small, difficulty=difficulty) == []
        assert GEN.self_check(large, difficulty=difficulty) == []


def test_public_axes_are_honest_observable_and_cross_band_legal() -> None:
    assert set(GEN.AXES) == {"grid_h", "grid_w", "target_size", "n_objects"}
    grid = GEN.generate(
        901,
        4,
        difficulty="easy",
        grid_h=30,
        grid_w=30,
        target_size=12,
        n_objects=5,
    )
    assert len(grid) == 30 and len(grid[0]) == 30
    assert GEN.observe_overrides(grid) == {
        "grid_h": 30,
        "grid_w": 30,
        "target_size": 12,
        "n_objects": 5,
    }
    assert GEN.self_check(grid, difficulty="easy") == []

    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, made_up_axis="x")
    with pytest.raises(TypeError, match="target_size"):
        GEN.generate(1, 0, target_size=True)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_exact_rule_hash_python_mirror_and_protected_racket_match_originals() -> None:
    source = _selected_source()
    assert GEN.RULE_HASH == _normalized_hash(source) == "23fd1d61a026"
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 3
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for pair in pairs:
            original = copy.deepcopy(pair["input"])
            assert GEN.rule_mirror(pair["input"], render_mode="outline") == pair["output"]
            bridge.define_grid("canonical_input", pair["input"])
            assert bridge.eval_text(f"({wrap_rule(source)} canonical_input)") == pair["output"]
            assert pair["input"] == original
    finally:
        bridge.shutdown()


def test_generated_shapes_have_one_unique_selected_component_and_fresh_results() -> None:
    first = GEN.generate(112, 9, grid_h=24, grid_w=27, target_size=10, n_objects=5)
    second = GEN.generate(112, 9, grid_h=24, grid_w=27, target_size=10, n_objects=5)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert GEN.self_check(first) == []
    observed = GEN.observe_overrides(first)
    assert observed["target_size"] == 10
    assert observed["n_objects"] == 5

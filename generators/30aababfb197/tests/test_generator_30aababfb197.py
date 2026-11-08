from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from scripts.generator_module_loader import load_module_from_path


ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = ROOT / "puzzle_generators/per_puzzle/30aababfb197/generator.py"
CANON = ROOT / "data/canonical/puzzles.jsonl"


def _module():
    return load_module_from_path("test_generator_30aababfb197_subject", GEN_PATH)


def _canonical_inputs():
    with CANON.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "30aababfb197":
                return [pair["input"] for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task not found")


def _fresh_zero_outside_target(module, grid):
    analysis = module._analysis_or_raise(grid)
    target_cells = set(analysis["target"]["cells"])
    h, w = len(grid) - 1, len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            if any((r + dr, c + dc) in target_cells for dr, dc in module._DIRS4):
                continue
            return r, c
    raise AssertionError("no isolated zero cell available")


def test_all_declared_overrides_are_observable_at_boundaries():
    module = _module()
    cases = [
        dict(grid_h=9, grid_w=10, palette_kind="default", n_blobs=3, key_column=0, target_size=5),
        dict(grid_h=15, grid_w=16, palette_kind="warm", n_blobs=4, key_column=9, target_size=7),
        dict(grid_h=12, grid_w=13, palette_kind="cool", n_blobs=3, key_column=4, target_size=6),
        dict(grid_h=10, grid_w=14, palette_kind="varied", n_blobs=4, key_column=8, target_size=5),
    ]
    for index, overrides in enumerate(cases):
        grid = module.generate(100 + index, index, difficulty="medium", **overrides)
        assert module.self_check(grid) == []
        assert module.observe_overrides(grid) == overrides


def test_unknown_override_is_rejected_loudly():
    module = _module()
    with pytest.raises(ValueError, match="unknown override"):
        module.generate(1, 0, __override_contract_unknown_axis__=1)
    with pytest.raises(ValueError, match="unknown override"):
        module.generate(1, 0, texture="multiple_keys")


def test_determinism_fresh_returns_and_global_rng_purity():
    module = _module()
    state = random.getstate()
    first = module.generate(77, 9, difficulty="hard")
    assert random.getstate() == state
    second = module.generate(77, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert module.generate(77, 9, difficulty="hard") == second


def test_self_check_accepts_all_canonical_inputs():
    module = _module()
    inputs = _canonical_inputs()
    assert len(inputs) == 5
    assert [module.self_check(grid) for grid in inputs] == [[] for _ in inputs]


def test_self_check_rejects_targeted_impostors():
    module = _module()
    base = module.generate(31, 5, difficulty="medium", n_blobs=4)

    no_key = copy.deepcopy(base)
    no_key[-1] = [0] * len(no_key[-1])
    assert any("exactly one bottom-row key" in message for message in module.self_check(no_key))

    two_keys = copy.deepcopy(base)
    empty_column = next(c for c, value in enumerate(two_keys[-1]) if value == 0)
    two_keys[-1][empty_column] = next(value for value in range(1, 10) if value != module._analysis_or_raise(base)["key_color"])
    assert any("exactly one bottom-row key" in message for message in module.self_check(two_keys))

    absent_key = copy.deepcopy(base)
    absent = next(value for value in range(1, 10) if value not in {v for row in base for v in row})
    key_col = module._analysis_or_raise(base)["key_column"]
    absent_key[-1][key_col] = absent
    assert any("body blob in key colour" in message for message in module.self_check(absent_key))

    duplicate_target = copy.deepcopy(base)
    r, c = _fresh_zero_outside_target(module, duplicate_target)
    duplicate_target[r][c] = module._analysis_or_raise(base)["key_color"]
    assert any("exactly one blob" in message or "3..4 body blobs" in message for message in module.self_check(duplicate_target))

    solid_bbox = copy.deepcopy(base)
    analysis = module._analysis_or_raise(base)
    r1, c1, r2, c2 = analysis["target"]["bbox"]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            solid_bbox[r][c] = analysis["key_color"]
    assert any("leave at least one zero" in message for message in module.self_check(solid_bbox))


def test_named_rivals_are_refuted_by_declared_witnesses():
    module = _module()
    for sample_index in range(12):
        grid = module.generate(200 + sample_index, sample_index, difficulty="medium")
        official = module.rule_mirror(grid)
        for witness_name, predicate in module.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            assert any(
                module.SEMANTIC_RIVALS[rival_name](grid) != official
                for rival_name in module.WITNESS_RIVALS[witness_name]
            ), witness_name


def test_every_consecutive_three_demo_window_is_identifiable():
    module = _module()
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(module.EXAMPLES_NEEDED + 1):
                grid = module.generate(9000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": module.rule_mirror(grid)})
            assert module.lesson_identifiable(pairs[:-1], pairs[-1]) == []

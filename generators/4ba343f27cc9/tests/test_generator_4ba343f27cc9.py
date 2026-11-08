"""Regression tests for the 4ba343f27cc9 generator repair."""
from __future__ import annotations

import importlib.util
import random
from pathlib import Path

from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT / "puzzle_generators" / "per_puzzle" / "4ba343f27cc9" / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_4ba343f27cc9", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def test_canonical_inputs_are_accepted_and_strict():
    pairs = canonical_pairs("4ba343f27cc9")
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_work_in_every_band():
    for band in ("easy", "medium", "hard"):
        for grid_h, grid_w, palette_size in ((4, 8, 7), (8, 4, 10)):
            grid = GEN.generate(
                17,
                29,
                difficulty=band,
                grid_h=grid_h,
                grid_w=grid_w,
                palette_size=palette_size,
            )
            assert GEN.observe_overrides(grid) == {
                "grid_h": grid_h,
                "grid_w": grid_w,
                "palette_size": palette_size,
            }
            assert GEN.self_check(grid) == []


def test_every_default_draw_refutes_all_named_rivals():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(36):
            grid = GEN.generate(1000 + sample_index, sample_index, difficulty=band)
            expected = GEN.rule_mirror(grid)
            assert GEN.self_check(grid) == []
            for rival in GEN.SEMANTIC_RIVALS.values():
                assert rival(grid) != expected


def test_every_two_draw_sliding_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(24):
            grid = GEN.generate(2000, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for start in range(len(pairs) - GEN.EXAMPLES_NEEDED):
            demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
            query = pairs[start + GEN.EXAMPLES_NEEDED]
            assert GEN.lesson_identifiable(demos, query) == []


def test_targeted_impostors_are_rejected():
    impostors = {
        "too_few_colors": [[0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        "rot180_symmetric": [
            [0, 1, 2, 3],
            [4, 5, 6, 0],
            [0, 6, 5, 4],
            [3, 2, 1, 0],
        ],
        "single_line_support": [
            [1, 2, 3, 4, 5, 6, 7],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ],
    }
    for grid in impostors.values():
        assert GEN.self_check(grid)


def test_replay_is_fresh_and_global_rng_is_unchanged():
    random.seed(12345)
    before = random.getstate()
    first = GEN.generate(7, 11, difficulty="hard")
    middle = GEN.generate(8, 12, difficulty="easy")
    second = GEN.generate(7, 11, difficulty="hard")
    after = random.getstate()
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert first != middle


def test_unknown_override_is_rejected():
    try:
        GEN.generate(1, 1, typo_axis=4)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was accepted")

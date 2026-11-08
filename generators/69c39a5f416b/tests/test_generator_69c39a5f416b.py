from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "runtime"))

from puzzle_generators import base  # noqa: E402


def _load_generator():
    path = ROOT / "generators" / "69c39a5f416b" / "generator.py"
    spec = importlib.util.spec_from_file_location("review_generator_69c39a5f416b", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs() -> list[dict]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                test = row["test"]
                return [*row["train"], *(test if isinstance(test, list) else [test])]
    raise AssertionError(f"missing canonical task {gen.TASK_ID}")


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _signature(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_hash_and_canonical_pairs_are_exact_and_input_pure() -> None:
    assert gen.RULE_HASH == "d3105e4a99fb"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_default_draws_are_lawful_and_axes_are_observable() -> None:
    for band in ("easy", "medium", "hard"):
        for sample_index in range(18):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(4100 + sample_index, sample_index, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert gen.self_check(grid) == []
            recorded_axes = {
                key: value
                for key, value in captured[-1].recorded_draws().items()
                if key in gen.AXES
            }
            assert recorded_axes == gen.observe_overrides(grid)


def test_six_slot_schedule_hits_all_linked_canonical_profiles() -> None:
    assert gen.SCHEDULE_PROFILES == tuple(range(6))
    for start in range(6):
        assert {
            gen.schedule_profile(0, start + offset)
            for offset in range(6)
        } == set(gen.SCHEDULE_PROFILES)

    expected = {(8, 8, 7), (8, 9, 5), (9, 9, 6)}
    for band in ("easy", "medium", "hard"):
        observed = {
            _signature(gen.generate(900 + profile, profile, difficulty=band))
            for profile in (0, 2, 4)
        }
        assert observed == expected


def test_every_three_demo_window_refutes_each_named_competitor() -> None:
    assert gen.EXAMPLES_NEEDED == 3
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            demos, query = pairs[: gen.EXAMPLES_NEEDED], pairs[gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                if rival(query["input"]) != query["output"]:
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_first_three_columns_shortcut_fits_canonical_but_generated_data_refutes_it() -> None:
    rival = gen.CANONICAL_SHORTCUTS["first_three_columns_only"]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        grid = gen.generate(123, 1, difficulty=band)
        assert gen.SEMANTIC_WITNESSES["legend_after_column_two"](grid)
        assert rival(grid) != gen.rule_mirror(grid)


def test_exact_override_cross_product_round_trips() -> None:
    for band in ("easy", "medium", "hard"):
        for grid_h in (7, 11):
            for grid_w in (7, 12):
                for n_pairs in (2, 4):
                    for legend_layout in gen.LEGEND_LAYOUTS:
                        for mapping_kind in gen.MAPPING_KINDS:
                            requested = {
                                "grid_h": grid_h,
                                "grid_w": grid_w,
                                "n_pairs": n_pairs,
                                "legend_layout": legend_layout,
                                "mapping_kind": mapping_kind,
                            }
                            grid = gen.generate(99, 17, difficulty=band, **requested)
                            assert gen.self_check(grid) == []
                            assert gen.observe_overrides(grid) == requested


def test_unknown_override_fails_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_palette="warm")


def test_self_check_rejects_structural_impostors() -> None:
    valid = gen.generate(1234, 1, difficulty="medium")
    columns, sources, destinations = gen._legend(valid)

    no_legend = copy.deepcopy(valid)
    no_legend[0] = [0] * len(no_legend[0])
    no_legend[1] = [0] * len(no_legend[1])

    half_pair = copy.deepcopy(valid)
    half_pair[1][columns[0]] = 0

    duplicate_source = copy.deepcopy(valid)
    duplicate_source[0][columns[1]] = duplicate_source[0][columns[0]]

    identity_pair = copy.deepcopy(valid)
    identity_pair[1][columns[0]] = identity_pair[0][columns[0]]

    unknown_body = copy.deepcopy(valid)
    foreign = next(color for color in range(1, 10) if color not in set(sources))
    unknown_body[2][0] = foreign

    missing_source = copy.deepcopy(valid)
    missing = sources[0]
    for row in missing_source[2:]:
        for column, value in enumerate(row):
            if value == missing:
                row[column] = 0

    for fixture in (no_legend, half_pair, duplicate_source, identity_pair, unknown_body, missing_source):
        assert gen.self_check(fixture), fixture


def test_determinism_fresh_returns_global_rng_and_reentrant_aba() -> None:
    random.seed(20261002)
    state = random.getstate()
    a = gen.generate(44, 9, difficulty="hard")
    b = gen.generate(45, 10, difficulty="easy")
    assert random.getstate() == state

    a_again = gen.generate(44, 9, difficulty="hard")
    assert a == a_again
    assert a is not a_again
    assert all(row is not other for row, other in zip(a, a_again))

    a_before = copy.deepcopy(a)
    b_before = copy.deepcopy(b)
    assert gen.rule_mirror(a) == gen.rule_mirror(a_again)
    gen.rule_mirror(b)
    assert a == a_before
    assert b == b_before

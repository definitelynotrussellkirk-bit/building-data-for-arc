from __future__ import annotations

import copy
import json
import random
from itertools import product
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.f5d85347c2fe import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    row = None
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            candidate = json.loads(line)
            if candidate.get("task_id") == gen.TASK_ID:
                row = candidate
                break
    assert row is not None

    def grid(value):
        return [[int(ch) for ch in r] if isinstance(r, str) else list(r) for r in value]

    pairs = [(grid(item["input"]), grid(item["output"])) for item in row["train"]]
    test = row["test"]
    pairs.append((grid(test["input"]), grid(test["output"])))
    return pairs


def test_rule_hash_and_all_canonical_pairs():
    assert gen.RULE_HASH == "8389730df0cc"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for inp, expected in pairs:
        assert gen.self_check(inp) == []
        assert gen.strict_canonical_like(inp) == []
        before = copy.deepcopy(inp)
        assert gen.rule_mirror(inp) == expected
        assert inp == before


def test_every_declared_override_cross_product_is_exact_and_observable():
    for band in ("easy", "medium", "hard"):
        for index, (profile, relation, layout) in enumerate(
            product(gen.PROFILES, gen.COLOR_RELATIONS, gen.DOT_LAYOUTS)
        ):
            expected = {
                "profile": profile,
                "color_relation": relation,
                "dot_layout": layout,
            }
            grid = gen.generate(
                seed=10_000 + index,
                sample_index=index,
                difficulty=band,
                **expected,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == expected
            assert gen.rule_mirror(grid) != grid


def test_unknown_and_invalid_overrides_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="canonical_11")
    with pytest.raises((ValueError, KeyError)):
        gen.generate(1, 0, profile="not_a_profile")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_self_check_rejects_rule_hiding_mutations():
    base = gen.generate(42, 3, profile="broad_three", color_relation="distinct", dot_layout="different_relative")
    errors, analysis = gen._analyze(base)
    assert errors == [] and analysis is not None
    first = analysis["frames"][0]

    broken_border = copy.deepcopy(base)
    r1, c1, _, _ = first["box"]
    broken_border[r1][c1] = 0
    assert gen.self_check(broken_border)

    no_dot = copy.deepcopy(base)
    dr, dc, _ = first["dot"]
    no_dot[dr][dc] = 0
    assert any("inner dots" in item for item in gen.self_check(no_dot))

    extra_dot = copy.deepcopy(base)
    for r, c in first["interior"]:
        if (r, c) != (dr, dc):
            extra_dot[r][c] = 9 if first["dot"][2] != 9 else 8
            break
    assert any("inner dots" in item for item in gen.self_check(extra_dot))

    stray = copy.deepcopy(base)
    stray[0][0] = 4
    assert any("stray" in item for item in gen.self_check(stray))


def test_four_consecutive_demos_identify_rule_against_named_rivals():
    for band in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(4):
            inp = gen.generate(700 + sample_index, sample_index, difficulty=band)
            demos.append({"input": inp, "output": gen.rule_mirror(inp)})
        query_input = gen.generate(999, 4, difficulty=band)
        query = {"input": query_input, "output": gen.rule_mirror(query_input)}
        assert gen.lesson_identifiable(demos, query) == []
        assert {gen.schedule_profile(0, i, band) for i in range(4)} == set(gen.PROFILES)


def test_named_canonical_shortcuts_fit_canonical_but_are_refuted_generated():
    pairs = _canonical_pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(inp) == expected for inp, expected in pairs), name

    broad = gen.generate(51, 3, profile="broad_three", color_relation="repeated", dot_layout="different_relative")
    true = gen.rule_mirror(broad)
    assert gen.CANONICAL_SHORTCUTS["only_first_two_frames"](broad) != true
    assert gen.CANONICAL_SHORTCUTS["reject_repeated_colors"](broad) != true
    assert gen.CANONICAL_SHORTCUTS["only_canonical_frame_sizes"](broad) != true


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(123456)
    state_before = random.getstate()
    first = gen.generate(9876, 11, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(9876, 11, difficulty="hard")
    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9

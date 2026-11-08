"""Focused semantic and regression tests for generator 038464cb9db1."""
from __future__ import annotations

import copy
import hashlib
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "038464cb9db1"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def test_rule_hash_and_all_six_canonical_pairs():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 6
    canonical_rule = (
        "(rule! (lambda (g) (let* ((h (rows g)) (w (cols g))) "
        "(let* ((nw (+ w (- h 1)))) (build-grid h nw (r c) "
        "(let ((oc (- c (- h 1 r)))) (if (and (>= oc 0) (< oc w)) "
        "(at g r oc) 0)))))))"
    )
    digest = hashlib.sha256(
        " ".join(canonical_rule.split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == digest == "608d74db8ac9"
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        frozen = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == frozen


def test_exact_overrides_are_observable_and_unknown_keys_reject():
    for band in ("easy", "medium", "hard"):
        for overrides in (
            {"grid_h": 2},
            {"grid_h": 15},
            {"grid_w": 1},
            {"grid_w": 15},
            {"palette_size": 4},
            {"palette_size": 9},
            {"grid_h": 2, "grid_w": 15, "palette_size": 9},
            {"grid_h": 15, "grid_w": 1, "palette_size": 9},
        ):
            grid = gen.generate(9102, 17, difficulty=band, **overrides)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            for name, value in overrides.items():
                assert observed[name] == value
    with pytest.raises(TypeError):
        gen.generate(1, 1, typo_axis=3)
    with pytest.raises(ValueError) as excinfo:
        gen.generate(1, 1, grid_h=2, grid_w=1)
    assert set(excinfo.value.incompatible_axes) >= {"grid_h", "grid_w"}


def test_every_sliding_four_sample_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(
                    800_000 + start,
                    start + offset,
                    difficulty=band,
                )
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_named_witnesses_refute_named_rivals():
    grids = [gen.generate(73, index, difficulty="medium") for index in range(48)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        hits = [grid for grid in grids if witness(grid)]
        assert hits, witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert all(rival(grid) != gen.rule_mirror(grid) for grid in hits)


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(4242, 3, difficulty="medium")
    h, w = len(valid), len(valid[0])
    modal = valid[0][0]
    other = next(value for value in range(1, 10) if value != modal)

    all_one_color = [[modal] * w for _ in range(h)]
    singleton = [[modal] * w for _ in range(h)]
    singleton[h // 2][w // 2] = other
    zero_contaminated = copy.deepcopy(valid)
    zero_contaminated[0][0] = 0
    ragged = copy.deepcopy(valid)
    ragged[-1] = ragged[-1][:-1]
    too_tall = [valid[0][:] for _ in range(16)]

    for name, impostor in {
        "all_one_color": all_one_color,
        "singleton": singleton,
        "zero_contaminated": zero_contaminated,
        "ragged": ragged,
        "too_tall": too_tall,
    }.items():
        assert gen.self_check(impostor), name


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(52711)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="hard")
    second = gen.generate(17, 9, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 0
    assert first != second
    assert second == gen.generate(17, 9, difficulty="hard")
    assert second != gen.generate(17, 10, difficulty="hard")

"""Focused regressions for generator a89702404b3c."""
from __future__ import annotations

import copy
import hashlib
import random

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

import pytest

ROOT = find_root(__file__)
gen, _, _ = load_selected_generator("a89702404b3c", root=ROOT)


def _canonical_row():
    import json
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        return next(
            row for line in handle if line.strip()
            if (row := json.loads(line)).get("task_id") == gen.TASK_ID
        )


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    actual_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual_hash
    for pair in [*row["train"], *row["test"]]:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]


def test_exact_override_boundaries_and_incompatibilities():
    for band in ("easy", "medium", "hard"):
        for case in (
            {"side": 3},
            {"side": 12},
            {"parity": "odd"},
            {"parity": "even"},
            {"palette_size": 3},
            {"palette_size": 10},
            {"side": 3, "parity": "odd", "palette_size": 9},
            {"side": 12, "parity": "even", "palette_size": 10},
        ):
            grid = gen.generate(971, 41, difficulty=band, **case)
            observed = gen.observe_overrides(grid)
            for axis, expected in case.items():
                assert observed[axis] == expected
            assert gen.self_check(
                grid, difficulty=band, meta={"overrides": case}
            ) == []

    with pytest.raises(ValueError, match="incompatible"):
        gen.generate(1, 1, side=3, parity="even")
    with pytest.raises(ValueError, match="cannot fit"):
        gen.generate(1, 1, side=3, palette_size=10)


def test_lesson_schedule_exposes_both_parity_branches():
    for seed in range(30):
        parities = {
            gen.observe_overrides(gen.generate(seed, sample, difficulty="medium"))[
                "parity"
            ]
            for sample in range(6)
        }
        assert parities == {"odd", "even"}


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(897024)
    before = random.getstate()
    first = gen.generate(17, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(17, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert gen.generate(17, 9, difficulty="hard") == second
    assert gen.generate(18, 9, difficulty="hard") != second
    assert gen.generate(17, 10, difficulty="hard") != second


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(
        991337,
        42,
        difficulty="hard",
        side=8,
        parity="even",
        palette_size=8,
    )
    impostors = {}

    nonsquare = copy.deepcopy(base)
    nonsquare.pop()
    impostors["nonsquare"] = nonsquare

    monochrome = [[base[0][0] for _ in row] for row in base]
    impostors["monochrome"] = monochrome

    collapsed_answer = copy.deepcopy(base)
    answer_color = collapsed_answer[0][-2]
    for row in range(2):
        for col in range(len(collapsed_answer[0]) - 2, len(collapsed_answer[0])):
            collapsed_answer[row][col] = answer_color
    impostors["collapsed_answer"] = collapsed_answer

    equal_corners = copy.deepcopy(base)
    for row in range(2):
        equal_corners[row][-2:] = equal_corners[row][:2]
    impostors["equal_corners"] = equal_corners

    dominant = copy.deepcopy(base)
    dominant_color = dominant[2][2]
    for row in range(2, len(dominant)):
        dominant[row] = [dominant_color] * len(dominant[row])
    impostors["dominant_color"] = dominant

    absent_replacement = copy.deepcopy(base)
    present = {value for row in absent_replacement for value in row}
    replacement = next(value for value in range(10) if value not in present)
    for row in range(2):
        for col in range(len(absent_replacement[0]) - 2, len(absent_replacement[0])):
            absent_replacement[row][col] = replacement
    impostors["absent_feature_recombination"] = absent_replacement

    for label, grid in impostors.items():
        assert gen.self_check(grid), label


def test_unknown_and_invalid_calls_reject_loudly():
    with pytest.raises(ValueError, match="unsupported override"):
        gen.generate(1, 1, texture="noise")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        gen.generate(1, 1, difficulty="extreme")
    for axis in ("side", "palette_size"):
        for bad in (True, 6.0, "6"):
            with pytest.raises(ValueError, match="integer"):
                gen.generate(1, 1, **{axis: bad})

def test_declares_strict_canonical_like_semantic_contract():
    for pair in canonical_pairs("a89702404b3c", root=ROOT, labeled_only=True):
        assert gen.strict_canonical_like(pair["input"]) == []
    generated = gen.generate(83, 4, difficulty="hard")
    assert gen.strict_canonical_like(generated) == []
    assert gen.strict_canonical_like([[1, 2], [3]])


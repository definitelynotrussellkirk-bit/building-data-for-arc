from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.3c01bf0d6576.generator")
TASK_ID = "3c01bf0d6576"


def test_rule_hash_and_all_canonical_pairs_match_full_crop_rule() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "3722dcd853de"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    saw_satellite = False
    saw_shape_ambiguity = False
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        info, errors = gen._analyze(pair["input"])
        assert errors == []
        assert gen.self_check(pair["input"]) == []
        assert gen._solve_python(pair["input"]) == pair["output"]
        assert pair["input"] == original
        saw_satellite |= info["satellite_count"] == 1
        saw_shape_ambiguity |= len(info["shape_matches"]) > 1
    assert saw_satellite, "canonical corpus must cover bbox-crop satellite semantics"
    assert saw_shape_ambiguity, "canonical corpus must require colour-aware transform inference"


def test_satellite_texture_includes_disconnected_cell_in_b_crop() -> None:
    grid = gen.generate(
        20260815,
        1,
        difficulty="medium",
        transform=4,
        texture="query_satellite",
        palette_size=5,
    )
    info, errors = gen._analyze(grid)
    assert errors == []
    assert info["satellite_count"] == 1
    truth = gen._solve_python(grid)
    connected_only = gen.SEMANTIC_RIVALS["connected_query_only"](grid)
    assert truth != connected_only
    assert gen.SEMANTIC_WITNESSES["query_satellite_in_crop"](grid)


def test_colour_disambiguation_kills_shape_only_rival() -> None:
    grid = gen.generate(
        20260815,
        2,
        difficulty="hard",
        transform=5,
        texture="color_disambiguation",
    )
    info, errors = gen._analyze(grid)
    assert errors == []
    assert len(info["shape_matches"]) > 1
    assert gen._solve_python(grid) != gen.SEMANTIC_RIVALS["shape_only_transform"](grid)


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    cases = (
        {"grid_h": 11, "grid_w": 15, "transform": 1, "palette_size": 3, "texture": "standard"},
        {"grid_h": 14, "grid_w": 18, "transform": 5, "palette_size": 5, "texture": "query_satellite"},
        {"grid_h": 12, "grid_w": 16, "transform": 3, "palette_size": 4, "texture": "color_disambiguation"},
    )
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(7331 + index, 40 + index, difficulty=band, **overrides)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == overrides


def test_unknown_and_invalid_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override axis"):
        gen.generate(1, 0, typo_axis="ignored")
    with pytest.raises((ValueError, AssertionError)):
        gen.generate(1, 0, transform=0)
    with pytest.raises((ValueError, AssertionError)):
        gen.generate(1, 0, palette_size=6)


def test_deterministic_fresh_return_and_global_rng_purity() -> None:
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(42, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_every_sliding_four_demo_window_is_identifiable() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(20):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(8800 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen._solve_python(grid)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_self_check_rejects_targeted_impostors() -> None:
    valid = gen.generate(9001, 3, difficulty="medium")
    info, errors = gen._analyze(valid)
    assert errors == []

    all_zero = [[0 for _ in row] for row in valid]

    identity_demo = copy.deepcopy(valid)
    a_cells = info["components"][0]
    ap_cells = info["components"][1]
    ar0, ac0, ar1, ac1 = gen._bbox(a_cells)
    pr0, pc0, pr1, pc1 = gen._bbox(ap_cells)
    for r in range(pr0, pr1 + 1):
        for c in range(pc0, pc1 + 1):
            identity_demo[r][c] = 0
    a_crop = [row[ac0:ac1 + 1] for row in valid[ar0:ar1 + 1]]
    for r, row in enumerate(a_crop):
        for c, value in enumerate(row):
            identity_demo[pr0 + r][pc0 + c] = value

    one_colour_b = copy.deepcopy(valid)
    for r, c in info["components"][2]:
        one_colour_b[r][c] = 1

    extra_component = copy.deepcopy(valid)
    placed = False
    for r in range(len(valid) - 1, -1, -1):
        for c in range(len(valid[0]) - 1, -1, -1):
            if extra_component[r][c] != 0:
                continue
            if all(
                not (0 <= r + dr < len(valid) and 0 <= c + dc < len(valid[0]))
                or extra_component[r + dr][c + dc] == 0
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                extra_component[r][c] = 9
                placed = True
                break
        if placed:
            break
    assert placed

    for name, impostor in {
        "all_zero": all_zero,
        "identity_demo": identity_demo,
        "one_colour_b": one_colour_b,
        "extra_component": extra_component,
    }.items():
        assert gen.self_check(impostor), name

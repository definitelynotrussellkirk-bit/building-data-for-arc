from __future__ import annotations

import copy
import json
import random

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.70913cf98cee.generator")


from reviewer_support import canonical_pairs, find_root

TASK_ID = "70913cf98cee"


def _canonical_inputs():
    root = find_root(__file__)
    for pair in canonical_pairs(TASK_ID, root=root):
        yield pair["input"]


def _mutations(base):
    pairs = gen._header_pairs(base)
    sources = [src for src, _ in pairs]
    destinations = [dst for _, dst in pairs]

    odd_header = copy.deepcopy(base)
    odd_header[0][next(i for i, v in enumerate(odd_header[0]) if v != 0)] = 0

    missing_source = copy.deepcopy(base)
    missing = sources[0]
    for r in range(2, len(missing_source)):
        for c in range(len(missing_source[0])):
            if missing_source[r][c] == missing:
                missing_source[r][c] = 0

    destination_in_body = copy.deepcopy(base)
    for r in range(2, len(destination_in_body)):
        for c in range(len(destination_in_body[0])):
            if destination_in_body[r][c] == sources[0]:
                destination_in_body[r][c] = destinations[0]
                break
        else:
            continue
        break

    duplicate_legend = copy.deepcopy(base)
    nz = [i for i, v in enumerate(duplicate_legend[0]) if v != 0]
    duplicate_legend[0][nz[1]] = duplicate_legend[0][nz[0]]

    dense_body = copy.deepcopy(base)
    for r in range(2, len(dense_body)):
        for c in range(len(dense_body[0])):
            dense_body[r][c] = sources[0]

    broken_separator = copy.deepcopy(base)
    broken_separator[1][0] = sources[0]

    return {
        "odd_header": odd_header,
        "missing_source": missing_source,
        "destination_in_body": destination_in_body,
        "duplicate_legend": duplicate_legend,
        "dense_body": dense_body,
        "broken_separator": broken_separator,
    }


def test_canonical_inputs_pass_self_check():
    grids = list(_canonical_inputs())
    assert len(grids) == 3
    assert all(gen.self_check(grid) == [] for grid in grids)


def test_exact_axes_are_observable_at_boundaries():
    cases = [
        dict(grid_h=7, grid_w=9, n_pairs=2, header_offset=0,
             n_neutral_colors=0, body_style="canonical_shapes"),
        dict(grid_h=12, grid_w=16, n_pairs=4, header_offset=2,
             n_neutral_colors=1, body_style="mixed"),
        dict(grid_h=9, grid_w=12, n_pairs=3, header_offset=1,
             n_neutral_colors=1, body_style="scattered"),
    ]
    for i, case in enumerate(cases):
        grid = gen.generate(100 + i, 200 + i, difficulty="hard", **case)
        observed = gen.observe_overrides(grid)
        for key in ("grid_h", "grid_w", "n_pairs", "header_offset", "n_neutral_colors"):
            assert observed[key] == case[key]
        assert gen.self_check(grid) == []


def test_incompatible_header_axes_reject_loudly():
    with pytest.raises(ValueError, match="cannot fit"):
        gen.generate(1, 1, grid_w=9, n_pairs=4, header_offset=2)


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(
        11, 17, difficulty="hard", grid_h=10, grid_w=14,
        n_pairs=3, header_offset=1, n_neutral_colors=1,
        body_style="mixed",
    )
    mutations = _mutations(base)
    assert len(mutations) >= 4
    for name, mutated in mutations.items():
        assert gen.self_check(mutated), name


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(918273)
    before = random.getstate()
    a = gen.generate(91, 7, difficulty="medium")
    middle = random.getstate()
    b = gen.generate(91, 7, difficulty="medium")
    after = random.getstate()
    assert a == b
    assert a is not b
    assert all(left is not right for left, right in zip(a, b))
    assert before == middle == after
    a[0][0] = 9 if a[0][0] != 9 else 8
    assert a != b


def test_easy_distribution_contains_canonical_morphology():
    for seed in range(30):
        grid = gen.generate(seed, seed * 13 + 5, difficulty="easy")
        obs = gen.semantic_observables(grid)
        assert obs["n_pairs"] == 2
        assert obs["header_offset"] == 0
        assert obs["n_neutral_colors"] == 0
        assert obs["separator_blank"]
        assert obs["destination_cells_in_body"] == 0
        assert obs["changed_cells"] >= 6
        assert len({v for row in grid for v in row}) == 5


def test_body_style_overrides_change_same_seed_scene():
    grids = [
        gen.generate(2026, 24, difficulty="hard", body_style=style,
                     grid_h=12, grid_w=16, n_pairs=4, header_offset=2,
                     n_neutral_colors=1)
        for style in gen.BODY_STYLES
    ]
    assert len({json.dumps(grid) for grid in grids}) == len(gen.BODY_STYLES)

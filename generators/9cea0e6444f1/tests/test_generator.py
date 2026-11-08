"""Task-local regression tests for 9cea0e6444f1."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "9cea0e6444f1"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_9cea0e6444f1", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _norm(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _connected(cells):
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        r, c = stack.pop()
        for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if q in remaining:
                remaining.remove(q)
                stack.append(q)
    return not remaining


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "fe554f47cd7a"


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=find_root(__file__)),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_self_check_accepts_every_canonical_input(pair):
    assert gen.self_check(pair["input"]) == []


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK, root=find_root(__file__)),
    ids=lambda pair: f"oracle-{pair['split']}{pair['pair_index']}",
)
def test_python_oracle_matches_every_canonical_output(pair):
    assert gen._reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "origin_kind,placement_kind,decoy_kind,n_one,n_two",
    [
        ("corner", "horizontal", "none", 4, 8),
        ("split", "vertical", "far_pair", 8, 4),
        ("corner", "diagonal", "far_pair", 8, 8),
        ("split", "diagonal", "none", 5, 7),
    ],
)
def test_exact_overrides_are_observable_and_lawful(
    origin_kind, placement_kind, decoy_kind, n_one, n_two
):
    expected = {
        "grid_h": 9,
        "grid_w": 9,
        "n_one": n_one,
        "n_two": n_two,
        "origin_kind": origin_kind,
        "placement_kind": placement_kind,
        "decoy_kind": decoy_kind,
    }
    grid = gen.generate(917, 13, difficulty="hard", **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected
    assert grid == gen.generate(917, 13, difficulty="hard", **expected)

    one, two = _norm(_cells(grid, 1)), _norm(_cells(grid, 2))
    assert one & two
    assert one - two
    assert two - one
    assert _connected(_cells(grid, 1))
    assert _connected(_cells(grid, 2))
    assert ((0, 0) in one and (0, 0) in two) is (origin_kind == "corner")


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, invented_axis=3)


@pytest.mark.parametrize("seed", [0, 1, 17, 91])
def test_default_schedule_mixes_canonical_profiles_decoys_origins_and_placements(seed):
    observed = [gen.observe_overrides(gen.generate(seed, index, difficulty="medium")) for index in range(6)]
    assert {row["decoy_kind"] for row in observed[:2]} == {"none", "far_pair"}
    assert {row["origin_kind"] for row in observed[:2]} == {"corner", "split"}
    assert {row["placement_kind"] for row in observed[:3]} == {"horizontal", "vertical", "diagonal"}
    assert any(
        row["decoy_kind"] == "none" and (row["grid_h"], row["grid_w"]) in {(9, 9), (11, 11)}
        for row in observed
    )


@pytest.mark.parametrize("seed,index", [(0, 0), (7, 5), (99, 14), (801, 31)])
def test_every_default_draw_refutes_core_shortcuts(seed, index):
    grid = gen.generate(seed, index, difficulty=("easy", "medium", "hard")[index % 3])
    expected = gen._reference_output(grid)
    for name in (
        "absolute_coordinates",
        "color_1_only",
        "color_2_only",
        "intersection_only",
        "xor_only",
        "solid_bbox",
    ):
        assert gen.LESSON_COMPETITORS[name](grid) != expected, name


def test_each_three_example_window_refutes_the_include_all_colors_rival():
    for seed in (0, 1, 17, 91):
        for start in range(8):
            grids = [gen.generate(seed, start + offset, difficulty="medium") for offset in range(3)]
            assert any(
                gen.LESSON_COMPETITORS["all_nonzero_colors"](grid)
                != gen._reference_output(grid)
                for grid in grids
            )


def test_far_pair_decoy_is_a_real_semantic_witness():
    grid = gen.generate(
        809,
        2,
        grid_h=9,
        grid_w=9,
        n_one=6,
        n_two=6,
        origin_kind="split",
        placement_kind="horizontal",
        decoy_kind="far_pair",
    )
    expected = gen._reference_output(grid)
    assert gen.SEMANTIC_WITNESSES["ignore_decoy"](grid)
    assert gen.SEMANTIC_RIVALS["all_nonzero_colors"](grid) != expected


def test_generated_union_is_sparse_and_both_shapes_contribute():
    for index in range(30):
        grid = gen.generate(404, index, difficulty="hard")
        one, two = _norm(_cells(grid, 1)), _norm(_cells(grid, 2))
        union = one | two
        h = max(r for r, _ in union) + 1
        w = max(c for _, c in union) + 1
        assert one & two and one - two and two - one
        assert len(union) < h * w

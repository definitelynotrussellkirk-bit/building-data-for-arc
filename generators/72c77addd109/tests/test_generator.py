"""Task-local regression suite for 72c77addd109."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    color_order_rival,
    has_border_overwrite,
    intended_output,
    load_generator,
    observed,
    reading_order_rival,
    split_objects,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_accepts_canonical_arbitrary_solids_and_matches_outputs(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_rule_hash_and_semantic_contract_are_pinned():
    assert gen.RULE_HASH == "a657cfe83f60"
    assert callable(gen.strict_canonical_like)
    assert {"solid_reading_order", "solid_color_order"} <= set(gen.SEMANTIC_RIVALS)
    assert {"solid_reading_order", "solid_color_order"} <= set(gen.CANONICAL_SHORTCUTS)
    assert gen.WITNESS_RIVALS


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    options = {
        "grid_h": 11,
        "grid_w": 12,
        "solid_style": "mixed",
        "solid_rank_order": "descending",
        "frame_rank_order": "ascending",
        "solid_color_order": "descending",
        "palette_kind": "canonical",
    }
    grid = gen.generate(71, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert has_border_overwrite(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 10),
        ("grid_h", 17),
        ("grid_w", 11),
        ("grid_w", 19),
        ("grid_h", True),
        ("grid_w", "12"),
        ("solid_style", "unknown"),
        ("solid_rank_order", "random"),
        ("frame_rank_order", "random"),
        ("solid_color_order", "random"),
        ("palette_kind", "default"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_declared_axis_endpoints_and_combinations_are_constructive():
    cases = [
        dict(grid_h=11, grid_w=12, solid_style="rectangles", solid_rank_order="ascending",
             frame_rank_order="ascending", solid_color_order="ascending", palette_kind="canonical"),
        dict(grid_h=16, grid_w=18, solid_style="irregular", solid_rank_order="descending",
             frame_rank_order="descending", solid_color_order="descending", palette_kind="varied"),
        dict(grid_h=11, grid_w=18, solid_style="mixed", solid_rank_order="ascending",
             frame_rank_order="descending", solid_color_order="descending", palette_kind="canonical"),
        dict(grid_h=16, grid_w=12, solid_style="mixed", solid_rank_order="descending",
             frame_rank_order="ascending", solid_color_order="ascending", palette_kind="varied"),
    ]
    for i, options in enumerate(cases):
        grid = gen.generate(900 + i, i, difficulty="hard", **options)
        assert gen.self_check(grid) == []
        assert observed(grid) == options


def test_canonical_shortcuts_fit_public_pairs_but_generated_witness_refutes_both():
    for pair in canonical_pairs():
        assert reading_order_rival(pair["input"]) == pair["output"]
        assert color_order_rival(pair["input"]) == pair["output"]
    grid = gen.generate(
        117,
        4,
        grid_h=11,
        grid_w=13,
        solid_style="irregular",
        solid_rank_order="descending",
        frame_rank_order="ascending",
        solid_color_order="descending",
        palette_kind="canonical",
    )
    intended = intended_output(grid)
    assert reading_order_rival(grid) != intended
    assert color_order_rival(grid) != intended
    assert gen.SEMANTIC_RIVALS["solid_reading_order"](grid) == reading_order_rival(grid)
    assert gen.SEMANTIC_RIVALS["solid_color_order"](grid) == color_order_rival(grid)
    assert gen.SEMANTIC_WITNESSES["crossed_solid_reading_order"](grid)
    assert gen.SEMANTIC_WITNESSES["crossed_solid_color_order"](grid)


def test_default_distribution_covers_canonical_profiles_and_nonrectangular_solids():
    profiles = set()
    styles = set()
    rank_orders = set()
    frame_orders = set()
    palettes = set()
    border_cases = 0
    unique = set()
    for band in (None, "easy", "medium", "hard"):
        band_profiles = set()
        for i in range(80):
            grid = gen.generate(2100 + i, i * 7 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(2100 + i, i * 7 + 3, difficulty=band)
            stats = observed(grid)
            profiles.add((stats["grid_h"], stats["grid_w"], len({v for row in grid for v in row})))
            band_profiles.add((stats["grid_h"], stats["grid_w"], len({v for row in grid for v in row})))
            styles.add(stats["solid_style"])
            rank_orders.add(stats["solid_rank_order"])
            frame_orders.add(stats["frame_rank_order"])
            palettes.add(stats["palette_kind"])
            border_cases += has_border_overwrite(grid)
            unique.add(tuple(tuple(row) for row in grid))
            assert intended_output(grid) != grid
        assert band_profiles & {(11, 12, 5), (11, 13, 5)}
    assert {"rectangles", "irregular", "mixed"} <= styles
    assert {"ascending", "descending"} <= rank_orders
    assert {"ascending", "descending"} <= frame_orders
    assert {"canonical", "varied"} <= palettes
    assert border_cases > 0
    assert len(unique) > 250


@pytest.mark.parametrize("mutation", ["erase", "extra", "tie_solid_sizes", "unknown_color"])
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(42, 5, solid_style="irregular", palette_kind="canonical")
    changed = deepcopy(grid)
    frames, solids = split_objects(changed)
    if mutation == "erase":
        r, c = frames[0]["cells"][0]
        changed[r][c] = 0
    elif mutation == "extra":
        changed[-1][-1] = 1
    elif mutation == "tie_solid_sizes":
        smaller = min(solids, key=lambda obj: len(obj["cells"]))
        larger = max(solids, key=lambda obj: len(obj["cells"]))
        target = len(smaller["cells"])
        for r, c in list(larger["cells"])[target:]:
            changed[r][c] = 0
    elif mutation == "unknown_color":
        changed[0][0] = 10
    assert gen.self_check(changed)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(11)]])
def test_malformed_grid_is_diagnostic_not_exception(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_cyclic_query_rotation_leaves_all_named_rivals_refuted(band):
    """The three demonstrations identify the rule regardless of query rotation."""
    period = 6
    for start in range(period):
        seed = 88000 + start
        pairs = []
        for offset in range(4):
            grid = gen.generate(seed, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"]
                    for pair in demos
                ), (band, start, query_index, name)

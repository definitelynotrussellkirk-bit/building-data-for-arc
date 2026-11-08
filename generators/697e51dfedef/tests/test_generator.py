"""Task-local regressions for the size-rank recoloring curriculum."""
from __future__ import annotations

import ast
from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    components,
    load_generator,
    observed_axes,
    oracle_output,
    reading_order_rival,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_axis_surface_and_single_validator() -> None:
    assert gen.RULE_HASH == "5f4ba5cc9570"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "layout_order"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    source = Path(gen.__file__).read_text()
    tree = ast.parse(source)
    validators = [
        node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "self_check"
    ]
    assert len(validators) == 1


def test_all_canonical_pairs_are_accepted_and_match_independent_oracle() -> None:
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert oracle_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 14, "layout_order": "ascending"},
        {"grid_h": 14, "grid_w": 7, "layout_order": "descending"},
        {"grid_h": 9, "grid_w": 9, "layout_order": "scrambled"},
    ],
)
def test_exact_overrides_are_total_observable_and_valid_in_every_band(
    band: str | None, options: dict[str, int | str]
) -> None:
    for seed in range(4):
        grid = gen.generate(seed, seed * 7 + 1, difficulty=band, **options)
        assert gen.self_check(grid, difficulty=band, meta={"overrides": options}) == []
        assert observed_axes(grid) == options
        assert gen.observe_overrides(grid) == options
        assert grid == gen.generate(seed, seed * 7 + 1, difficulty=band, **options)
        assert oracle_output(grid) != grid


@pytest.mark.parametrize(
    "case",
    [
        {"typo": 1},
        {"__override_contract_unknown_axis__": 1},
        {"grid_h": 6},
        {"grid_h": 15},
        {"grid_w": 6},
        {"grid_w": 15},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"grid_h": "9"},
        {"layout_order": "unknown"},
        {"layout_order": 1},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(case: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty="easy", **case)


@pytest.mark.parametrize("difficulty", ["impossible", 0.5, True])
def test_invalid_difficulty_is_rejected(difficulty: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_anchors_profiles_and_survives_every_query_rotation(band: str) -> None:
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "canonical_8_ascending",
        "broad_descending",
        "canonical_9_scrambled",
        "canonical_9_ascending",
        "canonical_8_descending",
        "broad_scrambled",
    )
    canonical_orders = {8: set(), 9: set()}
    for index in range(len(gen.SCHEDULE_PROFILES)):
        grid = gen.generate(73, index, difficulty=band)
        if len(grid) == len(grid[0]) in canonical_orders:
            canonical_orders[len(grid)].add(observed_axes(grid)["layout_order"])
    for size, orders in canonical_orders.items():
        assert "ascending" in orders, (size, orders)
        assert orders & {"descending", "scrambled"}, (size, orders)

    for start in range(24):
        lesson = [gen.generate(73, start + offset, difficulty=band) for offset in range(4)]
        assert [gen.schedule_profile(73, start + offset, difficulty=band) for offset in range(4)]
        assert all(gen.self_check(grid) == [] for grid in lesson)
        profiles = {(len(grid), len(grid[0]), len({cell for row in grid for cell in row})) for grid in lesson}
        assert profiles & {(8, 8, 4), (9, 9, 4)}
        for query_index in range(4):
            demos = [grid for index, grid in enumerate(lesson) if index != query_index]
            assert any(oracle_output(grid) != reading_order_rival(grid) for grid in demos)


def test_reading_order_shortcut_fits_canonical_but_exact_witness_refutes_it() -> None:
    shortcut = gen.CANONICAL_SHORTCUTS["reading_order"]
    assert shortcut is gen.SEMANTIC_RIVALS["reading_order"]
    assert shortcut is gen.LESSON_COMPETITORS["reading_order"]
    assert gen.WITNESS_RIVALS == {"size_not_reading_order": ["reading_order"]}
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())

    grid = witness_input()
    intended = oracle_output(grid)
    rival = reading_order_rival(grid)
    assert gen.self_check(grid) == []
    assert gen.SEMANTIC_WITNESSES["size_not_reading_order"](grid)
    assert shortcut(grid) == rival
    assert intended != rival
    assert intended == [
        [8, 8, 0, 0, 0, 0, 0],
        [8, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 4, 4],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    assert rival == [
        [2, 2, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 8, 8],
        [0, 0, 0, 0, 0, 0, 0],
    ]


def test_lesson_identifiable_names_and_refutes_reading_order() -> None:
    ascending = gen.generate(51, 0, layout_order="ascending")
    descending = gen.generate(51, 1, layout_order="descending")
    query = gen.generate(51, 2, layout_order="scrambled")
    asc_pair = {"input": ascending, "output": oracle_output(ascending)}
    desc_pair = {"input": descending, "output": oracle_output(descending)}
    query_pair = {"input": query, "output": oracle_output(query)}
    reasons = gen.lesson_identifiable([asc_pair, asc_pair, asc_pair], query_pair)
    assert any("reading_order" in reason for reason in reasons)
    assert gen.lesson_identifiable([asc_pair, desc_pair, asc_pair], query_pair) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_constructive_default_distribution_never_drops_an_object(band: str) -> None:
    signatures: set[tuple] = set()
    positions: set[tuple[tuple[int, int], ...]] = set()
    orders: set[str] = set()
    for index in range(512):
        grid = gen.generate(10_000 + index, index, difficulty=band)
        assert grid == gen.generate(10_000 + index, index, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        comps = components(grid)
        assert len(comps) == 3
        assert len({item["color"] for item in comps}) == 3
        assert len({item["size"] for item in comps}) == 3
        observed = observed_axes(grid)
        orders.add(str(observed["layout_order"]))
        signatures.add(
            (
                len(grid),
                len(grid[0]),
                tuple(sorted(item["size"] for item in comps)),
                tuple(sorted(item["color"] for item in comps)),
            )
        )
        positions.add(tuple(sorted(item["origin"] for item in comps)))
    assert orders == {"ascending", "descending", "scrambled"}
    assert len(signatures) >= 80
    assert len(positions) >= 4


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0, 0], [0]],
        [[False] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(7)],
        [[1] * 7 for _ in range(7)],
        [[0, 10, 0], [0, 0, 0], [0, 0, 0]],
        [[1, 2, 0], [0, 0, 0], [0, 3, 0]],
    ],
)
def test_self_check_rejects_malformed_or_out_of_manifold_without_raising(grid) -> None:
    assert gen.self_check(grid)


def test_oracles_and_semantic_hooks_do_not_mutate_inputs() -> None:
    grid = gen.generate(29, 3, layout_order="scrambled")
    original = deepcopy(grid)
    oracle_output(grid)
    reading_order_rival(grid)
    gen.SEMANTIC_RIVALS["reading_order"](grid)
    gen.SEMANTIC_WITNESSES["size_not_reading_order"](grid)
    gen.observe_overrides(grid)
    assert grid == original


def test_real_racket_authority_matches_independent_oracle_when_available() -> None:
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    grids += [gen.generate(319, index, difficulty="hard") for index in range(12)]
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]

"""Focused regressions for the three-panel transform analogy.

The tests use an independent Python transform oracle for structural checks and
public ``Catalog.apply`` for authority parity.  They deliberately avoid using
module helpers as the source of expected labels.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "f5bef0d462cd"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("panel_transform_generator_under_test", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)

NAMES = ("id", "rot90", "rot180", "rot270", "flip-h", "flip-v", "transpose")


def split_panels(grid):
    assert len(grid) == 4 and all(len(row) == 14 for row in grid)
    assert all(row[4] == row[9] == 9 for row in grid)
    return (
        [row[0:4] for row in grid],
        [row[5:9] for row in grid],
        [row[10:14] for row in grid],
    )


def transform(grid, name):
    if name == "id":
        return [row[:] for row in grid]
    if name == "rot90":
        return [list(row) for row in zip(*grid[::-1])]
    if name == "rot180":
        return [row[::-1] for row in grid[::-1]]
    if name == "rot270":
        return [list(row) for row in zip(*grid)][::-1]
    if name == "flip-h":
        return [row[::-1] for row in grid]
    if name == "flip-v":
        return [row[:] for row in grid[::-1]]
    if name == "transpose":
        return [list(row) for row in zip(*grid)]
    raise AssertionError(name)


def infer(grid):
    a, b, _ = split_panels(grid)
    hits = [name for name in NAMES if transform(a, name) == b]
    assert len(hits) == 1, hits
    return hits[0]


def expected(grid):
    _, _, query = split_panels(grid)
    return transform(query, infer(grid))


def nonzero_count(panel):
    return sum(value != 0 for row in panel for value in row)


def test_required_public_contract_is_declared():
    assert GEN.RULE_HASH == "9a215441e24b"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 20
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == {"transform", "motif_cells", "query_cells"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, True])
def test_invalid_difficulty_rejects(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"transform": "anti-transpose"},
        {"transform": 1},
        {"motif_cells": 2},
        {"motif_cells": 6},
        {"motif_cells": 3.0},
        {"motif_cells": True},
        {"query_cells": 2},
        {"query_cells": 6},
        {"query_cells": "4"},
    ],
)
def test_invalid_exact_controls_reject(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("motif_cells", [3, 4, 5])
@pytest.mark.parametrize("query_cells", [3, 4, 5])
def test_every_exact_control_is_observable(name, motif_cells, query_cells):
    grid = GEN.generate(
        419,
        11,
        difficulty="easy",
        transform=name,
        motif_cells=motif_cells,
        query_cells=query_cells,
    )
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {
        "transform": name,
        "motif_cells": motif_cells,
        "query_cells": query_cells,
    }
    a, b, c = split_panels(grid)
    assert transform(a, name) == b
    assert nonzero_count(a) == nonzero_count(b) == motif_cells
    assert nonzero_count(c) == query_cells
    assert len({tuple(tuple(row) for row in transform(c, other)) for other in NAMES}) == 7


def test_difficulty_bands_are_not_dead_and_remain_lawful():
    grids = {band: GEN.generate(91, 5, difficulty=band) for band in ("easy", "medium", "hard")}
    assert len({tuple(tuple(row) for row in grid) for grid in grids.values()}) == 3
    counts = {band: GEN.observe_overrides(grid)["motif_cells"] for band, grid in grids.items()}
    query_counts = {band: GEN.observe_overrides(grid)["query_cells"] for band, grid in grids.items()}
    assert counts == {"easy": 3, "medium": 4, "hard": 5}
    assert query_counts == {"easy": 3, "medium": 5, "hard": 4}
    assert all(GEN.self_check(grid) == [] for grid in grids.values())


def test_default_query_count_varies_across_seeds_but_not_within_a_lesson():
    observed = []
    for seed in range(9):
        lesson = [GEN.observe_overrides(GEN.generate(seed, index, difficulty="medium"))
                  for index in range(4)]
        assert len({row["query_cells"] for row in lesson}) == 1
        observed.extend(lesson)
    assert any(row["motif_cells"] != row["query_cells"] for row in observed)
    assert {row["query_cells"] for row in observed} == {3, 4, 5}


def test_default_schedule_covers_all_transforms_and_every_four_refute_inverse_direction():
    period = GEN.LESSON_SCHEDULE_PERIOD
    for seed in (0, 1, 19):
        names = [GEN.observe_overrides(GEN.generate(seed, i))["transform"] for i in range(2 * period)]
        assert set(names[:period]) == set(NAMES)
        assert names[:period] == names[period:]
        cyclic = names[:period] + names[:3]
        for start in range(period):
            window = cyclic[start : start + 4]
            assert len(set(window)) == 4
            assert {"rot90", "rot270"} <= set(window)


def test_default_inputs_vary_placement_and_color_without_losing_domain():
    grids = [GEN.generate(seed, seed % 7, difficulty=None) for seed in range(40)]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    supports = set()
    palettes = set()
    for grid in grids:
        a, _, c = split_panels(grid)
        supports.add(tuple((r, col) for r, row in enumerate(a) for col, value in enumerate(row) if value))
        palettes.add(tuple(sorted({value for row in grid for value in row if value not in (0, 9)})))
    assert len(supports) >= 20
    assert len(palettes) >= 10


def test_canonical_inputs_and_labels_remain_supported():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])
        assert expected(pair["input"]) == pair["output"]


def test_public_racket_authority_matches_generated_oracle_and_pinned_hash():
    generated = [GEN.generate(728, i, transform=name, motif_cells=3 + i % 3, query_cells=5 - i % 3)
                 for i, name in enumerate(NAMES)]
    pairs = canonical_pairs(TASK, root=ROOT)
    grids = [pair["input"] for pair in pairs] + generated
    report = Catalog(ROOT).apply(TASK, grids, timeout=90, allow_unapproved=True)
    assert report["rule_hash_matches_catalog"]
    assert report["executed_rule_hash"] == GEN.RULE_HASH
    assert [row["error"] for row in report["results"]] == [None] * len(grids)
    outputs = [row["output"] for row in report["results"]]
    assert outputs[: len(pairs)] == [pair["output"] for pair in pairs]
    assert outputs[len(pairs) :] == [expected(grid) for grid in generated]


def test_semantic_contract_declares_executable_rivals_and_witnesses():
    required = {f"fixed_{name}" for name in NAMES} | {"inverse_transform", "return_panel1"}
    assert required <= set(GEN.SEMANTIC_RIVALS)
    assert required <= set(GEN.LESSON_COMPETITORS)
    assert required <= set(GEN.SEMANTIC_WITNESSES)
    assert required <= set(GEN.WITNESS_RIVALS)
    grid = GEN.generate(4, 1, transform="rot90", motif_cells=5, query_cells=5)
    truth = expected(grid)
    for name in required:
        prediction = GEN.SEMANTIC_RIVALS[name](grid)
        assert isinstance(prediction, list)
        assert GEN.SEMANTIC_WITNESSES[name](grid) == (prediction != truth)


def test_every_cyclic_lesson_and_query_rotation_refutes_fixed_transform_shortcuts():
    for seed in range(7):
        pairs = []
        for index in range(10):
            grid = GEN.generate(seed, index, difficulty="medium")
            pairs.append({"input": grid, "output": expected(grid)})
        for start in range(7):
            lesson = pairs[start : start + 4]
            for query_index in range(4):
                query = lesson[query_index]
                demos = lesson[:query_index] + lesson[query_index + 1 :]
                assert GEN.lesson_identifiable(demos, query) == []
                for rival_name in (f"fixed_{name}" for name in NAMES):
                    rival = GEN.LESSON_COMPETITORS[rival_name]
                    assert not (
                        all(rival(pair["input"]) == pair["output"] for pair in demos)
                        and rival(query["input"]) != query["output"]
                    ), (seed, start, query_index, rival_name)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 0], [0]],
        [[0] * 14 for _ in range(4)],
        [[False] + [0] * 13 for _ in range(4)],
    ],
)
def test_self_check_rejects_malformed_or_out_of_domain_inputs(grid):
    assert GEN.self_check(grid)


def test_self_check_rejects_ambiguous_demo_transform_and_same_query_color():
    grid = GEN.generate(9, 2, transform="rot180", motif_cells=4, query_cells=4)
    a, _, _ = split_panels(grid)
    ambiguous = [row[:] for row in grid]
    source_color = next(value for row in a for value in row if value)
    symmetric = [[0] * 4 for _ in range(4)]
    for r, c in ((1, 1), (1, 2), (2, 1), (2, 2)):
        symmetric[r][c] = source_color
    for r in range(4):
        ambiguous[r][0:4] = symmetric[r][:]
        ambiguous[r][5:9] = symmetric[r][:]
    assert GEN.self_check(ambiguous)

    same_color = [row[:] for row in grid]
    for r in range(4):
        for c in range(10, 14):
            if same_color[r][c] not in (0, 9):
                same_color[r][c] = source_color
    assert GEN.self_check(same_color)


def test_default_cell_counts_do_not_encode_quarter_turn_direction():
    """Observable motif sizes must not tell rot90 from rot270.

    The prior default coupled transform phase and query-cell parity.  A learner
    could therefore use panel sizes to choose clockwise versus counterclockwise
    while only consulting panel0→panel1 for self-inverse transforms.
    """
    directions_by_counts = {}
    for seed in range(GEN.LESSON_SCHEDULE_PERIOD):
        for index in range(GEN.LESSON_SCHEDULE_PERIOD):
            for band in ("easy", "medium", "hard"):
                grid = GEN.generate(seed, index, difficulty=band)
                name = infer(grid)
                if name not in {"rot90", "rot270"}:
                    continue
                a, _, query = split_panels(grid)
                key = (nonzero_count(a), nonzero_count(query))
                directions_by_counts.setdefault(key, set()).add(name)

    assert directions_by_counts
    assert all(directions == {"rot90", "rot270"}
               for directions in directions_by_counts.values()), directions_by_counts


def test_retained_baseline_fixed_transform_counterexample_and_repair():
    fixture = json.loads((HOME / "counterexamples" / "baseline_fixed_transform_lesson.json").read_text())
    pairs = fixture["pairs"]
    query_index = fixture["query_index"]
    rival_name = fixture["rival"].removeprefix("fixed_")
    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
    assert all(transform(split_panels(pair["input"])[2], rival_name) == pair["canonical_output"]
               for pair in demos)
    query = pairs[query_index]
    assert transform(split_panels(query["input"])[2], rival_name) != query["canonical_output"]
    assert fixture["executed_rule_hash"] == GEN.RULE_HASH
    assert fixture["rule_hash_matches_catalog"] is True

    repaired = []
    for offset in range(4):
        grid = GEN.generate(
            fixture["seed"],
            fixture["sample_start"] + offset,
            difficulty=fixture["difficulty"],
        )
        repaired.append({"input": grid, "output": expected(grid)})
    repaired_query = repaired[query_index]
    repaired_demos = repaired[:query_index] + repaired[query_index + 1 :]
    rival = GEN.LESSON_COMPETITORS[fixture["rival"]]
    assert not (
        all(rival(pair["input"]) == pair["output"] for pair in repaired_demos)
        and rival(repaired_query["input"]) != repaired_query["output"]
    )

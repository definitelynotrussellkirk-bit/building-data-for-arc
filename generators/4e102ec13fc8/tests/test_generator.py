"""Task-local regression suite for the header-palette-by-depth generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    blue_cells_only_output,
    body_components,
    canonical_pairs,
    largest_component_only_output,
    load_generator,
    observed,
    prefix_palette_output,
    reference_output,
    ROOT,
)

GEN = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(8, 8, 5), (10, 9, 6)}


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_pin_and_independent_mirror_match_all_canonical_pairs():
    assert GEN.RULE_HASH == "6a515fd5e427"
    for pair in canonical_pairs():
        assert GEN.self_check(pair["input"]) == []
        assert reference_output(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=8, grid_w=8, palette_size=2, header_gaps=2,
             component_count=3, shape_color=8),
        dict(grid_h=18, grid_w=18, palette_size=4, header_gaps=0,
             component_count=1, shape_color=1),
        dict(grid_h=10, grid_w=9, palette_size=3, header_gaps=1,
             component_count=2, shape_color=5),
    ],
)
def test_every_exact_override_is_constructive_and_observable(band, options):
    grid = GEN.generate(1701, 19, difficulty=band, **options)
    assert GEN.self_check(grid) == []
    assert observed(grid) == options
    assert GEN.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7), ("grid_h", 19), ("grid_h", True), ("grid_h", 8.0),
        ("grid_w", 7), ("grid_w", 19),
        ("palette_size", 1), ("palette_size", 5),
        ("header_gaps", -1), ("header_gaps", 3),
        ("component_count", 0), ("component_count", 4),
        ("shape_color", 0), ("shape_color", 9), ("shape_color", "2"),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{key: value})


@pytest.mark.parametrize("bad", [
    [[1] * 8 for _ in range(8)],
    [[2, 3, 0, 0, 0, 0, 0, 0]] + [[0] * 8 for _ in range(7)],
    [[2, 3, 0, 0, 0, 0, 0, 0]]
    + [[0] * 8 for _ in range(2)]
    + [[0, 0, 1, 1, 0, 0, 0, 0], [0, 0, 1, 1, 0, 0, 0, 0]]
    + [[0] * 8 for _ in range(3)],
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[True] * 8 for _ in range(8)],
])
def test_self_check_rejects_malformed_or_semantically_thin_impostors(bad):
    assert GEN.self_check(bad)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_hits_canonical_profiles_and_refutes_all_shortcuts(band):
    seen = set()
    for index in range(20):
        grid = GEN.generate(314159, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        facts = observed(grid)
        assert facts["header_gaps"] >= 1
        assert facts["component_count"] >= 2
        assert facts["shape_color"] != 1
        assert max(GEN._depths_for_grid(grid).values()) >= 2
        official = GEN.rule_mirror(grid)
        assert prefix_palette_output(grid) != official
        assert blue_cells_only_output(grid) != official
        assert largest_component_only_output(grid) != official
        seen.add(profile(grid))
    assert seen == CANONICAL_PROFILES


def test_named_shortcuts_fit_every_canonical_demonstration():
    rivals = (prefix_palette_output, blue_cells_only_output, largest_component_only_output)
    for rival in rivals:
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())


def test_declared_witnesses_are_real_counterexamples():
    for index in range(18):
        grid = GEN.generate(712, index, difficulty="medium")
        official = GEN.rule_mirror(grid)
        assert GEN.SEMANTIC_WITNESSES["gapped_header"](grid)
        assert GEN.SEMANTIC_WITNESSES["nonblue_body"](grid)
        assert GEN.SEMANTIC_WITNESSES["multiple_components"](grid)
        for witness, rivals in GEN.WITNESS_RIVALS.items():
            if GEN.SEMANTIC_WITNESSES[witness](grid):
                assert any(GEN.SEMANTIC_RIVALS[name](deepcopy(grid)) != official for name in rivals)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_sliding_lesson_and_query_rotation_is_identifiable(band):
    for start in range(12):
        pairs = []
        for index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(9000 + start, index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index in range(len(pairs)):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


def test_difficulty_bands_materially_change_default_inputs():
    for index in range(8):
        grids = [GEN.generate(431, index, difficulty=band) for band in ("easy", "medium", "hard")]
        assert len({frozen(grid) for grid in grids}) == 3
        assert all(GEN.self_check(grid) == [] for grid in grids)


def test_default_shapes_are_not_rectangle_only_and_components_are_separated():
    shapes = set()
    for index in range(40):
        grid = GEN.generate(6001, index)
        components = body_components(grid)
        largest = max(components, key=len)
        rows = [r for r, _ in largest]
        cols = [c for _, c in largest]
        bbox_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
        assert len(largest) < bbox_area
        normalized = tuple(sorted((r - min(rows), c - min(cols)) for r, c in largest))
        shapes.add(normalized)
    assert len(shapes) >= 4


def test_determinism_freshness_and_global_rng_independence():
    random.seed(0x4E102)
    state = random.getstate()
    first = GEN.generate(123, 19, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123, 19, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    original = deepcopy(first)
    GEN.rule_mirror(first)
    assert first == original
    first[0][0] = 9
    assert GEN.generate(123, 19, difficulty="hard") == second


def test_large_sample_has_high_input_and_output_diversity():
    grids = [GEN.generate(seed, seed * 7 + 3, difficulty=("easy", "medium", "hard")[seed % 3])
             for seed in range(120)]
    outputs = [GEN.rule_mirror(grid) for grid in grids]
    assert len({frozen(grid) for grid in grids}) >= 110
    assert len({frozen(grid) for grid in outputs}) >= 110


def test_real_racket_reference_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    if not racket_runtime_status()["available"]:
        pytest.skip(racket_runtime_status()["reason"])
    # The public Catalog API is the authority path; the independent mirror is only the comparator.
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    catalog = Catalog(ROOT)
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [GEN.generate(919, i, difficulty="hard") for i in range(12)]
    result = catalog.apply(GEN.TASK_ID, grids)
    outputs = [row["output"] for row in result["results"]]
    assert outputs == [reference_output(grid) for grid in grids]

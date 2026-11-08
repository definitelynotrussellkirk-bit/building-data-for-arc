"""Focused regression and semantic tests for 250671db7aa1."""
from __future__ import annotations

import hashlib
import importlib
import itertools
import json
from collections import Counter

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "250671db7aa1"
ROOT = find_root(__file__)
GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def _copy(grid):
    return [row[:] for row in grid]


def test_rule_hash_version_and_canonical_oracle_parity():
    row = _canonical_row()
    digest = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert digest == GENERATOR.RULE_HASH == "27bdc557ee50"
    assert GENERATOR.VERSION == "3.0.0"

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = pair["input"]
        snapshot = _copy(source)
        assert GENERATOR.self_check(source) == []
        assert GENERATOR.strict_canonical_like(source) == []
        assert GENERATOR.rule_mirror(source) == pair["output"]
        assert source == snapshot


def test_axes_are_exact_observable_and_non_degenerate():
    assert set(GENERATOR.AXES) == {
        "grid_h",
        "grid_w",
        "orientation",
        "axis_bias",
        "source_side",
        "source_cells",
        "n_distinct_colors",
        "pattern",
    }
    assert GENERATOR.EXAMPLES_NEEDED == 4
    assert GENERATOR.LESSON_SCHEDULE_PERIOD == 4


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_boundary_override_product_is_exact(band):
    boundaries = {
        "grid_h": (7, 14),
        "grid_w": (7, 14),
        "orientation": ("vertical", "horizontal"),
        "axis_bias": ("start", "end"),
        "source_side": ("before", "after"),
        "source_cells": (4, 8),
        "n_distinct_colors": (1, 4),
        "pattern": ("compact", "split"),
    }
    for index, values in enumerate(itertools.product(*boundaries.values())):
        requested = dict(zip(boundaries, values))
        grid = GENERATOR.generate(
            100_000 + index,
            5 * index + 1,
            difficulty=band,
            **requested,
        )
        assert GENERATOR.self_check(grid) == []
        assert GENERATOR.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 7.0),
        ("grid_w", "9"),
        ("source_cells", True),
        ("n_distinct_colors", 2.0),
    ],
)
def test_integer_overrides_reject_coercion(axis, value):
    with pytest.raises(TypeError, match=axis):
        GENERATOR.generate(17, 3, **{axis: value})


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GENERATOR.generate(1, 2, invented_axis="x")


def test_schedule_teaches_every_declared_rival_under_every_query_rotation():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(GENERATOR.LESSON_SCHEDULE_PERIOD):
            pairs = []
            for offset in range(GENERATOR.EXAMPLES_NEEDED + 1):
                grid = GENERATOR.generate(
                    200_000 + 100 * band_index + start,
                    start + offset,
                    difficulty=band,
                )
                pairs.append({"input": grid, "output": GENERATOR.rule_mirror(grid)})
            for query_index in range(len(pairs)):
                query = pairs[query_index]
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert GENERATOR.lesson_identifiable(demos, query) == []
                for name, rival in GENERATOR.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), (band, start, query_index, name)


def test_canonical_shortcuts_really_fit_canonical_and_generated_witnesses_break_them():
    canonical = _canonical_pairs()
    assert set(GENERATOR.CANONICAL_SHORTCUTS) == {
        "reflect only from the lower-coordinate side",
        "reflect only the modal source color",
        "reflect only the largest source component",
        "reflect across the geometric center",
    }
    for name, rival in GENERATOR.CANONICAL_SHORTCUTS.items():
        for pair in canonical:
            assert rival(pair["input"]) == pair["output"], name

    witness_grids = [
        GENERATOR.generate(300_001, 1),
        GENERATOR.generate(300_002, 2),
        GENERATOR.generate(300_003, 3),
    ]
    for name, rival in GENERATOR.CANONICAL_SHORTCUTS.items():
        assert any(
            rival(grid) != GENERATOR.rule_mirror(grid) for grid in witness_grids
        ), name


def test_semantic_contract_names_real_witnesses_and_rivals():
    assert set(GENERATOR.SEMANTIC_RIVALS) == set(GENERATOR.CANONICAL_SHORTCUTS)
    assert set(GENERATOR.WITNESS_RIVALS) <= set(GENERATOR.SEMANTIC_WITNESSES)
    for witness, rivals in GENERATOR.WITNESS_RIVALS.items():
        assert rivals
        assert set(rivals) <= set(GENERATOR.SEMANTIC_RIVALS)
        assert callable(GENERATOR.SEMANTIC_WITNESSES[witness])


def test_default_population_covers_both_orientations_sides_and_structures():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        observed = {axis: set() for axis in GENERATOR.AXES}
        inputs = set()
        outputs = set()
        witness_counts = Counter()
        for index in range(200):
            grid = GENERATOR.generate(
                400_000 + 10_000 * band_index + index,
                index,
                difficulty=band,
            )
            assert GENERATOR.self_check(grid) == []
            facts = GENERATOR.observe_overrides(grid)
            for axis, value in facts.items():
                observed[axis].add(value)
            for name, predicate in GENERATOR.SEMANTIC_WITNESSES.items():
                witness_counts[name] += bool(predicate(grid))
            inputs.add(json.dumps(grid, separators=(",", ":")))
            outputs.add(
                json.dumps(GENERATOR.rule_mirror(grid), separators=(",", ":"))
            )

        assert observed["orientation"] == {"vertical", "horizontal"}
        assert observed["axis_bias"] == {"start", "center", "end"}
        assert observed["source_side"] == {"before", "after"}
        assert observed["n_distinct_colors"] == {1, 2, 3}
        assert observed["pattern"] == {"compact", "split"}
        assert len(observed["grid_h"]) >= 3
        assert len(observed["grid_w"]) >= 3
        assert len(observed["source_cells"]) >= 3
        assert len(inputs) >= 195
        assert len(outputs) >= 195
        assert all(count >= 40 for count in witness_counts.values())


def test_pinned_profile_floor_has_canonical_support_in_each_band():
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    assert canonical_profiles == {(9, 9, 3), (10, 10, 3)}
    for band in ("easy", "medium", "hard"):
        seen = {
            _profile(GENERATOR.generate(500_000 + i, i, difficulty=band))
            for i in range(20)
        }
        assert seen & canonical_profiles


def test_source_colors_and_components_are_all_reflected_without_mutation():
    grid = GENERATOR.generate(
        600_000,
        3,
        grid_h=11,
        grid_w=12,
        orientation="horizontal",
        axis_bias="start",
        source_side="after",
        source_cells=8,
        n_distinct_colors=4,
        pattern="split",
    )
    snapshot = _copy(grid)
    output = GENERATOR.rule_mirror(grid)
    assert grid == snapshot
    errors, facts = GENERATOR._analyze(grid)
    assert errors == []
    axis = facts["axis_index"]
    for row, col, value in facts["sources"]:
        mirror_row = 2 * axis - row
        assert output[row][col] == value
        assert output[mirror_row][col] == value


def test_self_check_rejects_minimal_impostors_and_mutations():
    valid = GENERATOR.generate(
        700_000,
        2,
        grid_h=9,
        grid_w=11,
        orientation="vertical",
        axis_bias="center",
        source_side="before",
        source_cells=6,
        n_distinct_colors=3,
        pattern="compact",
    )
    assert GENERATOR.self_check(valid) == []

    blank = [[0 for _ in row] for row in valid]
    assert GENERATOR.self_check(blank)

    missing_axis = _copy(valid)
    facts = GENERATOR._analyze(valid)[1]
    missing_axis[0][facts["axis_index"]] = 0
    assert GENERATOR.self_check(missing_axis)

    two_sided = _copy(valid)
    row, col, value = facts["sources"][0]
    mirror_col = 2 * facts["axis_index"] - col
    two_sided[row][mirror_col] = value
    assert GENERATOR.self_check(two_sided)

    extra_five = _copy(valid)
    extra_five[0][0] = 5
    assert GENERATOR.self_check(extra_five)


def test_compact_and_split_patterns_are_observably_distinct():
    for orientation in ("vertical", "horizontal"):
        compact = GENERATOR.generate(
            800_000,
            0,
            orientation=orientation,
            pattern="compact",
            source_cells=8,
        )
        split = GENERATOR.generate(
            800_001,
            1,
            orientation=orientation,
            pattern="split",
            source_cells=8,
        )
        assert GENERATOR.observe_overrides(compact)["pattern"] == "compact"
        assert GENERATOR.observe_overrides(split)["pattern"] == "split"


def test_exact_counterexample_breaks_strongest_direction_shortcut():
    path = ROOT / "generators" / TASK_ID / "counterexamples" / "after_side.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    grid = payload["input"]
    expected = payload["output"]
    assert GENERATOR.self_check(grid) == []
    assert GENERATOR.rule_mirror(grid) == expected
    rival = GENERATOR.CANONICAL_SHORTCUTS[
        "reflect only from the lower-coordinate side"
    ]
    assert rival(grid) != expected

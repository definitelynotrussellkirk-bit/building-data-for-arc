"""Focused regression, semantic, and contract tests for 4e16917b1bde."""
from __future__ import annotations

import hashlib
import importlib
import itertools
import json
import math
import random
from collections import Counter

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "4e16917b1bde"
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


def _copy(grid):
    return [row[:] for row in grid]


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _profile_floor_seed(band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_4e16917b1bde_rule_hash_and_canonical_oracle_parity():
    row = _canonical_row()
    digest = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert digest == GENERATOR.RULE_HASH == "de4ea202a020"
    assert GENERATOR.VERSION == "2.1.0"

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = pair["input"]
        snapshot = _copy(source)
        assert GENERATOR.self_check(source) == []
        assert GENERATOR.strict_canonical_like(source) == []
        assert GENERATOR.rule_mirror(source) == pair["output"]
        assert source == snapshot


def test_4e16917b1bde_every_boundary_override_combination_is_exact():
    boundaries = {
        "grid_h": (5, 12),
        "grid_w": (9, 17),
        "divider_color": (5, 9),
        "divider_bias": ("left", "right"),
        "source_side": ("left", "right"),
        "source_cells": (4, 8),
        "n_distinct_colors": (1, 4),
        "pattern": ("compact", "split"),
    }
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for case_index, values in enumerate(itertools.product(*boundaries.values())):
            requested = dict(zip(boundaries, values))
            grid = GENERATOR.generate(
                30_000 + band_index * 2_000 + case_index,
                7 * case_index + 3,
                difficulty=band,
                **requested,
            )
            assert GENERATOR.self_check(grid) == []
            assert GENERATOR.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 5.0),
        ("grid_w", "9"),
        ("divider_color", "5"),
        ("source_cells", 4.0),
        ("n_distinct_colors", True),
    ],
)
def test_4e16917b1bde_integer_and_color_overrides_do_not_coerce(axis, value):
    with pytest.raises(TypeError, match=axis):
        GENERATOR.generate(17, 3, **{axis: value})


def test_4e16917b1bde_default_divider_palette_covers_all_nonzero_colors():
    observed = set()
    for sample_index in range(360):
        grid = GENERATOR.generate(700_000 + sample_index, sample_index)
        divider_color = GENERATOR.observe_overrides(grid)["divider_color"]
        observed.add(divider_color)
        if sample_index % 5 == 0:
            assert divider_color == 5
    assert observed == set(range(1, 10))


def test_4e16917b1bde_pinned_profile_floor_has_exact_support_in_every_band():
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    assert canonical_profiles == {(5, 9, 3), (6, 10, 3)}

    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            seed = _profile_floor_seed(band, index)
            sample_index = seed % 7919 + index
            grid = GENERATOR.generate(seed, sample_index, difficulty=band)
            exact += _profile(grid) in canonical_profiles
        assert exact >= 1, band


def test_4e16917b1bde_multicolor_sources_have_strong_frequency_skew():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(24):
            grid = GENERATOR.generate(
                800_000 + 100 * band_index + offset,
                offset,
                difficulty=band,
                source_cells=6,
                n_distinct_colors=3,
            )
            _, facts = GENERATOR._analyze(grid)
            counts = Counter(value for _, _, value in facts["sources"])
            assert len(counts) == 3
            assert max(counts.values()) - min(counts.values()) >= 2


def test_4e16917b1bde_every_cyclic_lesson_refutes_common_color_shortcut():
    competitor_name = "mirror only colors within one count of the modal color"
    assert competitor_name in GENERATOR._LESSON_COMPETITORS
    competitor = GENERATOR._LESSON_COMPETITORS[competitor_name]

    for band_index, band in enumerate(("easy", "medium", "hard")):
        cycle = math.lcm(len(GENERATOR._LESSON_SCHEDULE), 5)
        for start in range(cycle):
            pairs = []
            for offset in range(GENERATOR.EXAMPLES_NEEDED + 1):
                grid = GENERATOR.generate(
                    900_000 + 100 * band_index + start,
                    start + offset,
                    difficulty=band,
                )
                pairs.append({"input": grid, "output": GENERATOR.rule_mirror(grid)})
            demos, query = pairs[:-1], pairs[-1]
            assert any(
                competitor(demo["input"]) != demo["output"] for demo in demos
            )
            assert GENERATOR.lesson_identifiable(demos, query) == []


def test_4e16917b1bde_semantic_contract_verifies_the_rare_color_shortcut():
    rival_name = "mirror only colors within one count of the modal color"
    witness_name = "strong_color_frequency_skew"

    assert set(GENERATOR.SEMANTIC_WITNESSES) == (
        set(GENERATOR.WITNESS_RIVALS) | set(GENERATOR.BRANCH_WITNESSES)
    )
    assert GENERATOR.WITNESS_RIVALS == {witness_name: [rival_name]}
    assert set(GENERATOR.CANONICAL_SHORTCUTS) == {rival_name}
    assert set(GENERATOR.LESSON_COMPETITORS) >= set(GENERATOR.SEMANTIC_RIVALS)

    rival = GENERATOR.SEMANTIC_RIVALS[rival_name]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(24):
            grid = GENERATOR.generate(
                950_000 + 100 * band_index + offset,
                offset,
                difficulty=band,
                source_cells=6,
                n_distinct_colors=3,
            )
            assert GENERATOR.SEMANTIC_WITNESSES[witness_name](grid)
            assert rival(grid) != GENERATOR.rule_mirror(grid)


def test_4e16917b1bde_200_per_band_semantic_census_and_disjoint_stability():
    runs = []
    for seed_base in (110_000, 810_000):
        run = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            axis_support = {axis: set() for axis in GENERATOR.AXES}
            witness_counts = Counter()
            inputs = set()
            outputs = set()
            for offset in range(200):
                seed = seed_base + 10_000 * band_index + offset
                grid = GENERATOR.generate(seed, offset, difficulty=band)
                assert GENERATOR.self_check(grid) == []
                assert GENERATOR.strict_canonical_like(grid) == []
                observed = GENERATOR.observe_overrides(grid)
                for axis, value in observed.items():
                    axis_support[axis].add(value)
                for name, witness in GENERATOR.SEMANTIC_WITNESSES.items():
                    witness_counts[name] += bool(witness(grid))
                inputs.add(json.dumps(grid, separators=(",", ":")))
                outputs.add(
                    json.dumps(GENERATOR.rule_mirror(grid), separators=(",", ":"))
                )

            assert len(inputs) >= 198
            assert len(outputs) >= 198
            assert axis_support["source_side"] == {"left", "right"}
            assert axis_support["divider_bias"] == {"left", "center", "right"}
            assert axis_support["pattern"] == {"compact", "split"}
            assert axis_support["n_distinct_colors"] == {1, 2, 3, 4}
            assert len(axis_support["grid_h"]) >= 2
            assert len(axis_support["grid_w"]) >= 2
            assert len(axis_support["source_cells"]) >= 2
            assert all(count >= 40 for count in witness_counts.values())
            run[band] = {
                "unique_inputs": len(inputs),
                "unique_outputs": len(outputs),
                "witness_counts": dict(witness_counts),
            }
        runs.append(run)

    for band in ("easy", "medium", "hard"):
        assert abs(runs[0][band]["unique_inputs"] - runs[1][band]["unique_inputs"]) <= 2
        for witness in GENERATOR.SEMANTIC_WITNESSES:
            assert abs(
                runs[0][band]["witness_counts"][witness]
                - runs[1][band]["witness_counts"][witness]
            ) <= 30


def test_4e16917b1bde_mutation_sensitive_impostors_are_rejected():
    valid = GENERATOR.generate(
        424_242,
        2,
        difficulty="medium",
        grid_h=7,
        grid_w=13,
        divider_color=5,
        divider_bias="center",
        source_side="left",
        source_cells=6,
        n_distinct_colors=3,
        pattern="split",
    )
    observed = GENERATOR.observe_overrides(valid)
    divider = next(
        col
        for col in range(len(valid[0]))
        if all(valid[row][col] == observed["divider_color"] for row in range(len(valid)))
    )
    sources = [
        (row, col, valid[row][col])
        for row in range(len(valid))
        for col in range(len(valid[0]))
        if col != divider and valid[row][col] != 0
    ]

    partial_divider = _copy(valid)
    partial_divider[0][divider] = 0

    second_divider = _copy(valid)
    second_col = 0 if divider != 0 else len(valid[0]) - 1
    for row in range(len(second_divider)):
        second_divider[row][second_col] = 6

    both_sides = _copy(valid)
    source_row, source_col, _ = sources[0]
    both_sides[source_row][2 * divider - source_col] = 4

    divider_color_off_axis = _copy(valid)
    row, col, _ = sources[-1]
    divider_color_off_axis[row][col] = observed["divider_color"]

    only_divider = [[0 for _ in row] for row in valid]
    for row in range(len(only_divider)):
        only_divider[row][divider] = observed["divider_color"]

    out_of_bounds = [[0] * 9 for _ in range(5)]
    for row in range(5):
        out_of_bounds[row][2] = 5
    out_of_bounds[1][8] = 3

    for name, impostor in {
        "partial_divider": partial_divider,
        "second_divider": second_divider,
        "both_sides_or_collision": both_sides,
        "divider_color_off_axis": divider_color_off_axis,
        "only_divider": only_divider,
        "out_of_bounds_reflection": out_of_bounds,
    }.items():
        assert GENERATOR.self_check(impostor), name


def test_4e16917b1bde_negative_recombination_and_lesson_identifiability():
    source = GENERATOR.generate(
        515_151,
        2,
        difficulty="medium",
        source_side="left",
        pattern="split",
        n_distinct_colors=3,
    )
    errors, facts = GENERATOR._analyze(source)
    assert not errors
    recombined = _copy(source)
    row, col, _ = facts["sources"][0]
    recombined[row][col] = 0
    used = {value for values in recombined for value in values}
    replacement = next(color for color in range(1, 10) if color not in used)
    divider = facts["divider_col"]
    destination = None
    for candidate_row in range(len(recombined)):
        for candidate_col in range(divider + 1, len(recombined[0])):
            mirror_col = 2 * divider - candidate_col
            if (
                0 <= mirror_col < len(recombined[0])
                and recombined[candidate_row][candidate_col] == 0
                and recombined[candidate_row][mirror_col] == 0
            ):
                destination = (candidate_row, candidate_col)
                break
        if destination:
            break
    assert destination is not None
    recombined[destination[0]][destination[1]] = replacement
    assert GENERATOR.self_check(recombined)

    demos = []
    for sample_index in range(GENERATOR.EXAMPLES_NEEDED):
        grid = GENERATOR.generate(202_607_25, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": GENERATOR.rule_mirror(grid)})
    query_grid = GENERATOR.generate(
        202_607_25, GENERATOR.EXAMPLES_NEEDED, difficulty="medium"
    )
    query = {"input": query_grid, "output": GENERATOR.rule_mirror(query_grid)}
    assert GENERATOR.lesson_identifiable(demos, query) == []


def test_4e16917b1bde_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20260725)
    state = random.getstate()
    first = GENERATOR.generate(73, 109, difficulty="hard")
    assert random.getstate() == state
    second = GENERATOR.generate(73, 109, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GENERATOR.generate(73, 109, difficulty="hard") == second

    with pytest.raises(ValueError, match="unknown override"):
        GENERATOR.generate(1, 2, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GENERATOR.generate(1, 2, difficulty="nightmare")
    with pytest.raises(ValueError):
        GENERATOR.generate(1, 2, grid_h=4)
    with pytest.raises(ValueError):
        GENERATOR.generate(1, 2, n_distinct_colors=5)

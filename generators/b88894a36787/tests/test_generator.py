"""Source-bound regression tests for the b88894a36787 generator repair."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "b88894a36787"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (geometry_output, header_entries, load_generator,
                             observed, path_overlaps)

gen = load_generator(HOME / "generator.py")
PAIRS = canonical_pairs(TASK, root=ROOT, labeled_only=True)


def test_pins_selected_authority_and_declares_exact_axes():
    assert gen.RULE_HASH == "94000a617419"
    assert gen.VERSION == "3.1.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_markers"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", PAIRS, ids=lambda pair: pair.get("split", "canonical"))
def test_accepts_every_canonical_input_and_mirror_matches_label(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]
    assert gen._prediction(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("values", [
    {"grid_h": 11, "grid_w": 11, "n_markers": 4},
    {"grid_h": 15, "grid_w": 15, "n_markers": 2},
])
def test_exact_overrides_work_in_every_band(band, values):
    grid = gen.generate(17, 8, difficulty=band, **values)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == values
    assert {key: observed(grid)[key] for key in values} == values


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("grid_h", 10), ("grid_h", 16),
    ("grid_w", 10), ("grid_w", 16),
    ("n_markers", 1), ("n_markers", 5),
    ("grid_h", True), ("grid_w", 12.0), ("n_markers", "3"),
])
def test_rejects_unknown_out_of_range_and_coercible_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("seed", [True, False, 1.5, "17", None])
def test_rejects_non_integer_seed_scalars(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize("name,grid", [
    ("empty", []),
    ("no_header", [[0] * 12 for _ in range(11)]),
    ("no_sides", [[0, 0, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0]] + [[0] * 12 for _ in range(10)]),
    ("full_grid", [[2] * 12 for _ in range(11)]),
    ("interior_dot", [[0, 0, 2, 3, 0, 0, 0, 0, 0, 0, 0]] +
                     [[0] * 11 for _ in range(10)]),
])
def test_old_degenerate_and_malformed_inputs_are_rejected(name, grid):
    # The interior-dot fixture is intentionally ragged; every malformed or
    # out-of-domain control should produce diagnostics rather than an exception.
    assert gen.self_check(grid), name


def test_validator_rejects_precise_destructive_mutations():
    grid = gen.generate(44, 1, grid_h=12, grid_w=12, n_markers=3)
    mutations = []

    extra = deepcopy(grid)
    extra[1][1] = 9
    mutations.append(extra)

    duplicate = deepcopy(grid)
    color = next(value for value in duplicate[0] if value)
    duplicate[-1][0] = color
    mutations.append(duplicate)

    gapped = deepcopy(grid)
    cols = [c for c, value in enumerate(gapped[0]) if value]
    gapped[0][cols[-1] + 1] = gapped[0][cols[-1]]
    gapped[0][cols[-1]] = 0
    mutations.append(gapped)

    two_missing = deepcopy(grid)
    header_colors = [value for value in two_missing[0] if value]
    for r in range(1, len(two_missing)):
        for c in (0, len(two_missing[0]) - 1):
            if two_missing[r][c] in header_colors[:2]:
                two_missing[r][c] = 0
    mutations.append(two_missing)

    for changed in mutations:
        assert gen.self_check(changed)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_valid_and_covers_canonical_branches(band):
    shapes = set()
    marker_counts = set()
    missing_counts = set()
    saw_row_two = False
    saw_shared_opposite_row = False
    for index in range(128):
        grid = gen.generate(1200 + index, index, difficulty=band)
        assert grid == gen.generate(1200 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert path_overlaps(grid) == []
        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        marker_counts.add(stats["n_markers"])
        missing_counts.add(stats["n_missing"])
        entries = [(r, c, value) for r, row in enumerate(grid[1:], 1)
                   for c, value in enumerate(row) if value]
        saw_row_two |= any(r == 2 for r, _c, _value in entries)
        by_row = {}
        for r, c, _value in entries:
            by_row.setdefault(r, set()).add(c)
        saw_shared_opposite_row |= any(cols == {0, len(grid[0]) - 1}
                                       for cols in by_row.values())
        original = deepcopy(grid)
        gen._prediction(grid)
        assert grid == original
    assert len(shapes) >= 8
    assert marker_counts == {2, 3, 4}
    assert missing_counts == {0, 1}
    assert saw_row_two
    assert saw_shared_opposite_row


def test_eight_slot_schedule_is_rotation_safe_for_declared_rivals():
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 8
    assert len(gen.SCHEDULE_PROFILES) == gen.LESSON_SCHEDULE_PERIOD
    assert len(set(gen.SCHEDULE_PROFILES)) == gen.LESSON_SCHEDULE_PERIOD
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 17, 20261011):
            for start in range(gen.LESSON_SCHEDULE_PERIOD):
                grids = [gen.generate(seed, start + offset, difficulty=band)
                         for offset in range(gen.EXAMPLES_NEEDED + 1)]
                pairs = [{"input": grid, "output": geometry_output(grid)} for grid in grids]
                assert len({json.dumps(grid) for grid in grids}) == len(grids)
                for query_index in range(len(pairs)):
                    demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                    query = pairs[query_index]
                    assert gen.lesson_identifiable(demos, query) == []
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def _missing_header_indices(grid):
    return [
        index
        for index, (_column, _color, _row, target_column) in enumerate(header_entries(grid))
        if target_column is None
    ]


def test_assumed_missing_position_is_declared_and_fits_all_canonical_pairs():
    assert set(gen.CANONICAL_SHORTCUTS) == {"assumed_missing_position"}
    rival = gen.CANONICAL_SHORTCUTS["assumed_missing_position"]
    assert all(rival(pair["input"]) == pair["output"] for pair in PAIRS)
    assert gen.LESSON_COMPETITORS["assumed_missing_position"] is rival


def test_witness_rival_names_are_registered_as_semantic_rivals():
    for witness, names in gen.WITNESS_RIVALS.items():
        assert witness in gen.SEMANTIC_WITNESSES
        assert set(names) <= set(gen.SEMANTIC_RIVALS)


def test_retained_reflection_is_a_lawful_counterexample_to_missing_position_shortcut():
    witness = json.loads((
        HOME / "counterexamples" / "review-b13f407456697e19-v0001" / "retained" /
        "checks" / "audit" / TASK / "input.json"
    ).read_text())
    assert gen.self_check(witness) == []
    assert _missing_header_indices(witness) == [1]
    assert gen.CANONICAL_SHORTCUTS["assumed_missing_position"](witness) != gen._prediction(witness)


def test_schedule_exposes_both_four_header_interior_missing_positions():
    left_witness_phases = {0, 2, 4, 6}
    for band in (None, "easy", "medium", "hard"):
        for phase in range(gen.LESSON_SCHEDULE_PERIOD):
            grid = gen.generate(29, phase, difficulty=band, grid_h=11, grid_w=11)
            if phase in left_witness_phases:
                assert observed(grid)["n_markers"] == 4
                assert _missing_header_indices(grid) == [1]
                assert gen.CANONICAL_SHORTCUTS["assumed_missing_position"](grid) != gen._prediction(grid)
            elif phase == 1:
                assert observed(grid)["n_markers"] == 4
                assert _missing_header_indices(grid) == [2]


def test_semantic_witnesses_are_real_counterexamples():
    missing = gen.generate(5, 0, grid_h=12, grid_w=12, n_markers=3)
    complete = gen.generate(5, 1, grid_h=12, grid_w=12, n_markers=3)
    assert gen.SEMANTIC_WITNESSES["missing_side_dot"](missing)
    assert gen.SEMANTIC_RIVALS["only_existing_pairs"](missing) != geometry_output(missing)
    assert gen.SEMANTIC_WITNESSES["matched_side_dot"](complete)
    assert gen.SEMANTIC_RIVALS["all_columns_to_bottom"](complete) != geometry_output(complete)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "generator.py")],
            env=env, text=True,
        ))
    assert outputs[0] == outputs[1]


def test_selected_base_rule_text_is_exactly_synchronized_to_canonical():
    canonical = None
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                canonical = row["program_solution"]
                break
    assert canonical is not None
    base = json.loads((ROOT / "shared" / "data" / "base" / "solutions" /
                       "training" / "29700607__b88894a36787.json").read_text())
    assert base["racket_target"]["target_code"] == canonical

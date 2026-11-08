"""Focused semantic and contract tests for generator aea1d569d78b."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "aea1d569d78b"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

CANVAS_PROFILES = {
    "canonical_8x10": (8, 10),
    "canonical_9x8": (9, 8),
    "canonical_9x9": (9, 9),
    "canonical_10x10": (10, 10),
}


def intended_output(grid):
    """Independent mirror of the authoritative row-then-column rule."""
    original = deepcopy(grid)
    out = deepcopy(grid)
    height, width = len(original), len(original[0])
    for row in range(height):
        columns = [column for column in range(width) if original[row][column] == 1]
        if len(columns) == 2:
            left, right = columns
            if all(original[row][column] == 0 for column in range(left + 1, right)):
                for column in range(left + 1, right):
                    out[row][column] = 3
    for column in range(width):
        rows = [row for row in range(height) if original[row][column] == 1]
        if len(rows) == 2:
            top, bottom = rows
            if all(original[row][column] == 0 for row in range(top + 1, bottom)):
                for row in range(top + 1, bottom):
                    out[row][column] = 3
    return out


def connect_through_blockers(grid):
    """Plausible wrong rule: paint zero cells between every pair of blue cells."""
    original = deepcopy(grid)
    out = deepcopy(grid)
    height, width = len(original), len(original[0])
    for row in range(height):
        columns = [column for column in range(width) if original[row][column] == 1]
        if len(columns) == 2:
            for column in range(columns[0] + 1, columns[1]):
                if original[row][column] == 0:
                    out[row][column] = 3
    for column in range(width):
        rows = [row for row in range(height) if original[row][column] == 1]
        if len(rows) == 2:
            for row in range(rows[0] + 1, rows[1]):
                if original[row][column] == 0:
                    out[row][column] = 3
    return out


def only_color_5_blocks(grid):
    """Canonical-fitting shortcut: treats colour 5, not any nonzero cell, as the wall."""
    original = deepcopy(grid)
    out = deepcopy(grid)
    height, width = len(original), len(original[0])
    for row in range(height):
        columns = [column for column in range(width) if original[row][column] == 1]
        if len(columns) == 2:
            interior = range(columns[0] + 1, columns[1])
            if all(original[row][column] != 5 for column in interior):
                for column in interior:
                    if original[row][column] == 0:
                        out[row][column] = 3
    for column in range(width):
        rows = [row for row in range(height) if original[row][column] == 1]
        if len(rows) == 2:
            interior = range(rows[0] + 1, rows[1])
            if all(original[row][column] != 5 for row in interior):
                for row in interior:
                    if original[row][column] == 0:
                        out[row][column] = 3
    return out


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def canonical_row():
    root = find_root(__file__)
    path = root / "shared/data/canonical/puzzles.jsonl"
    with path.open() as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def base_authority():
    root = find_root(__file__)
    path = root / "shared/data/base/solutions/banks/d3d681cdb82a/E51__aea1d569d78b.json"
    return json.loads(path.read_text())


def test_rule_pin_axes_and_authority_text_are_exact():
    assert GEN.RULE_HASH == "5074f7d7c8b5"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"canvas_profile", "blocked_orientation"}
    canonical = canonical_row()["program_solution"]
    racket = base_authority()["racket_target"]
    assert racket["raw_code"] == canonical
    assert racket["target_code"] == canonical
    assert normalized_rule_hash(canonical)[:12] == GEN.RULE_HASH


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile,dims", CANVAS_PROFILES.items())
@pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
def test_every_override_combination_is_constructive_observable_and_semantic(
    band, profile, dims, orientation
):
    grid = GEN.generate(
        91,
        17,
        difficulty=band,
        canvas_profile=profile,
        blocked_orientation=orientation,
    )
    assert (len(grid), len(grid[0])) == dims
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {
        "canvas_profile": profile,
        "blocked_orientation": orientation,
    }
    truth = intended_output(grid)
    assert truth != grid
    assert GEN.rule_mirror(grid) == truth
    assert connect_through_blockers(grid) != truth
    assert GEN.SEMANTIC_WITNESSES["blocked_pair"](grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"canvas_profile": "unknown"},
        {"blocked_orientation": "diagonal"},
        {"canvas_profile": 8},
        {"blocked_orientation": 1},
        {"typo_axis": "horizontal"},
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **kwargs)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty="extreme")


def test_all_canonical_pairs_are_owned_and_reference_mirror_matches_labels():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert intended_output(source) == pair["output"]
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_declared_shortcut_fits_all_canonical_pairs_but_generated_witness_refutes_it():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(GEN.CANONICAL_SHORTCUTS) == {"only_color_5_blocks"}
    rival = GEN.CANONICAL_SHORTCUTS["only_color_5_blocks"]
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    witness = GEN.generate(
        314159,
        2,
        canvas_profile="canonical_9x9",
        blocked_orientation="horizontal",
    )
    truth = intended_output(witness)
    assert rival(witness) != truth
    assert only_color_5_blocks(witness) == rival(witness)


def test_each_single_generated_demo_refutes_every_declared_lesson_competitor():
    for band in ("easy", "medium", "hard"):
        for index in range(60):
            grid = GEN.generate(700 + index, index, difficulty=band)
            pair = {"input": grid, "output": intended_output(grid)}
            assert GEN.lesson_identifiable([pair], pair) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert rival(grid) != pair["output"], (band, index, name)


def test_default_distribution_covers_profiles_orientations_palettes_and_crossings():
    for band in ("easy", "medium", "hard"):
        profiles = set()
        orientations = set()
        palettes = set()
        crossing_count = 0
        inputs = set()
        for index in range(240):
            grid = GEN.generate(20_000 + index, index, difficulty=band)
            observed = GEN.observe_overrides(grid)
            profiles.add(observed["canvas_profile"])
            orientations.add(observed["blocked_orientation"])
            palettes.add(tuple(sorted({value for row in grid for value in row})))
            inputs.add(json.dumps(grid, separators=(",", ":")))
            crossing_count += int(GEN.has_clear_crossing(grid))
            assert GEN.self_check(grid) == []
        assert profiles == set(CANVAS_PROFILES)
        assert orientations == {"horizontal", "vertical"}
        assert len(palettes) >= 8
        assert len(inputs) >= 220
        if band == "easy":
            assert crossing_count == 0
        elif band == "hard":
            assert crossing_count == 240
        else:
            assert 0 < crossing_count < 240


def test_self_check_rejects_malformed_and_semantic_impostors():
    good = GEN.generate(10, 3)
    assert GEN.self_check(good) == []

    malformed = (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 8 for _ in range(8)],
        [[10] * 8 for _ in range(8)],
    )
    for grid in malformed:
        assert GEN.self_check(grid)

    impostors = []
    impostors.append([[0] * 8 for _ in range(8)])
    singleton = [[0] * 8 for _ in range(8)]
    singleton[1][1] = 1
    impostors.append(singleton)
    short_line = [[0] * 8 for _ in range(8)]
    short_line[1][1] = short_line[1][2] = 1
    impostors.append(short_line)
    solid = [[0] * 8 for _ in range(8)]
    for row in (1, 2):
        for column in (1, 2):
            solid[row][column] = 1
    impostors.append(solid)
    green_input = deepcopy(good)
    green_input[0][0] = 3
    impostors.append(green_input)
    extra_blue = deepcopy(good)
    extra_blue[0][0] = 1
    impostors.append(extra_blue)
    for grid in impostors:
        assert GEN.self_check(grid)


def test_determinism_fresh_returns_and_helpers_are_input_pure():
    first = GEN.generate(991, 17, difficulty="hard")
    second = GEN.generate(991, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    snapshot = deepcopy(first)
    GEN.rule_mirror(first)
    GEN.observe_overrides(first)
    GEN.strict_canonical_like(first)
    for rival in GEN.LESSON_COMPETITORS.values():
        rival(first)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(first)
    assert first == snapshot

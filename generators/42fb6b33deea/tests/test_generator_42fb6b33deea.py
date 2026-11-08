"""Focused semantic regressions for generator 42fb6b33deea."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs as load_canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
TASK_ID = "42fb6b33deea"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
BASE = (
    ROOT
    / "data/base/solutions/banks/3c7b85b8eeb1/"
    "M36__42fb6b33deea.json"
)


def _canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _as_grid(rows):
    if rows and isinstance(rows[0], str):
        return [[int(value) for value in row] for row in rows]
    return copy.deepcopy(rows)


def _canonical_pairs():
    return [
        (copy.deepcopy(pair["input"]), copy.deepcopy(pair["output"]))
        for pair in load_canonical_pairs(TASK_ID, root=ROOT)
    ]


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _changed_fraction(grid, output):
    total = len(grid) * len(grid[0])
    changed = sum(
        left != right
        for input_row, output_row in zip(grid, output)
        for left, right in zip(input_row, output_row)
    )
    return changed / total


class _BoundedShuffleRandom(random.Random):
    """Fail if layout code randomizes an entire geometric catalog."""

    def shuffle(self, values):
        assert len(values) <= 16, (
            "layout must sample cached geometry without shuffling "
            f"a {len(values)}-element catalog"
        )
        return super().shuffle(values)


def test_target_box_selection_uses_bounded_random_work():
    rng = _BoundedShuffleRandom(20261011)
    boxes = GEN._choose_target_boxes(16, 18, 3, rng)
    assert len(boxes) == 3
    assert all(
        not GEN._bbox_overlap(left, right)
        for index, left in enumerate(boxes)
        for right in boxes[index + 1 :]
    )


def test_distractor_placement_uses_bounded_random_work():
    rng = _BoundedShuffleRandom(20261011)
    grid = [[0] * 18 for _ in range(16)]
    occupied = {(row, col) for row in range(3) for col in range(6)}
    GEN._place_distractor(grid, 8, 5, occupied, rng)
    assert sum(value == 8 for row in grid for value in row) == 5




@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, -1])
def test_sample_index_rejects_invalid_scalar_values(bad_sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(991, bad_sample_index, difficulty="easy")


@pytest.mark.parametrize(
    ("axis", "bad_value"),
    [
        ("n_target_colors", True),
        ("n_target_colors", 1.0),
        ("n_target_colors", "1"),
        ("n_distractor_colors", True),
        ("n_distractor_colors", False),
        ("n_distractor_colors", 1.0),
        ("n_distractor_colors", "1"),
    ],
)
def test_integer_axes_reject_non_integer_scalar_values(axis, bad_value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(991, 0, difficulty="easy", **{axis: bad_value})


def test_unknown_override_keys_are_rejected_loudly():
    with pytest.raises((KeyError, TypeError, ValueError)):
        GEN.generate(991, 0, difficulty="easy", typoed_axis=123)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_lesson_cycle_contains_an_exact_canonical_scale_anchor(band):
    canonical_profiles = {
        (8, 11, 3),
        (9, 10, 3),
        (9, 12, 3),
        (10, 10, 3),
        (10, 11, 4),
    }
    for sample_index in (1, 4, 7):
        grid = GEN.generate(20261011, sample_index, difficulty=band)
        profile = (
            len(grid),
            len(grid[0]),
            len({value for row in grid for value in row}),
        )
        assert profile in canonical_profiles


def test_rule_hash_and_task_local_authorities_are_exactly_synchronized():
    row = _canonical_row()
    source = row["program_solution"]
    base = json.loads(BASE.read_text())
    assert _normalized_rule_hash(source) == GEN.RULE_HASH == "b800fc792026"
    assert base["racket_target"]["raw_code"] == source
    assert base["racket_target"]["target_code"] == source


def test_all_five_canonical_pairs_are_accepted_and_python_oracle_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for grid, expected in pairs:
        before = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == expected
        assert grid == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_consecutive_samples_cover_decisive_lesson_roles(band):
    for start in range(6):
        observations = []
        for sample_index in range(start, start + 3):
            grid = GEN.generate(913, sample_index, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            observations.append(GEN.observe_overrides(grid))
        assert {item["n_distractor_colors"] for item in observations} == {0, 1, 2}
        assert 1 in {item["n_target_colors"] for item in observations}
        assert any(item["n_target_colors"] >= 2 for item in observations)
        styles = [item["target_style"] for item in observations]
        assert styles.count("count_witness") >= 2
        assert "corners" in styles


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_diverse_and_strongly_demonstrates_fill(band):
    inputs = set()
    outputs = set()
    target_counts = set()
    distractor_counts = set()
    minimum_change = 1.0
    for seed in range(120):
        grid = GEN.generate(seed, seed * 17 + 3, difficulty=band)
        output = GEN.rule_mirror(grid)
        assert GEN.self_check(grid, difficulty=band) == []
        observed = GEN.observe_overrides(grid)
        target_counts.add(observed["n_target_colors"])
        distractor_counts.add(observed["n_distractor_colors"])
        inputs.add(_freeze(grid))
        outputs.add(_freeze(output))
        minimum_change = min(minimum_change, _changed_fraction(grid, output))
    assert target_counts == {1, 2, 3}
    assert distractor_counts == {0, 1, 2}
    assert len(inputs) >= 118
    assert len(outputs) >= 118
    assert minimum_change >= 0.05


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_override_boundaries_are_exact_and_observable_in_every_band(band):
    for grid_h in (5, 16):
        for grid_w in (7, 18):
            for n_targets in (1, 3):
                for n_distractors in (0, 2):
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_target_colors": n_targets,
                        "n_distractor_colors": n_distractors,
                    }
                    grid = GEN.generate(
                        317,
                        911,
                        difficulty=band,
                        **requested,
                    )
                    assert (len(grid), len(grid[0])) == (grid_h, grid_w)
                    observed = GEN.observe_overrides(grid)
                    assert observed["n_target_colors"] == n_targets
                    assert observed["n_distractor_colors"] == n_distractors
                    assert observed["target_style"] in GEN.TARGET_STYLES
                    assert GEN.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": requested},
                    ) == []


def test_palette_axis_changes_realized_colors_without_changing_roles():
    grids = {
        kind: GEN.generate(
            431,
            919,
            difficulty="medium",
            grid_h=10,
            grid_w=12,
            n_target_colors=2,
            n_distractor_colors=1,
            palette_kind=kind,
        )
        for kind in GEN.PALETTE_KINDS
    }
    assert len({_freeze(grid) for grid in grids.values()}) == len(GEN.PALETTE_KINDS)
    for grid in grids.values():
        observed = GEN.observe_overrides(grid)
        assert observed["n_target_colors"] == 2
        assert observed["n_distractor_colors"] == 1
        assert observed["target_style"] in GEN.TARGET_STYLES
        assert GEN.self_check(grid) == []


def test_self_check_rejects_six_nearby_structural_impostors():
    base = GEN.generate(
        733,
        911,
        difficulty="medium",
        grid_h=10,
        grid_w=12,
        n_target_colors=2,
        n_distractor_colors=2,
    )
    analysis = GEN._analysis(base)
    assert analysis["errors"] == []

    no_target = copy.deepcopy(base)
    for color, box in analysis["targets"]:
        row, col = GEN._corners(box)[0]
        no_target[row][col] = 0

    wrong_distractor_count = copy.deepcopy(base)
    color, _, box = analysis["distractors"][1]
    extra = next(
        cell
        for cell in GEN._bbox_cells(box)
        if wrong_distractor_count[cell[0]][cell[1]] == 0
    )
    wrong_distractor_count[extra[0]][extra[1]] = color

    overlapping_targets = [[0] * 10 for _ in range(8)]
    for row, col in ((1, 1), (1, 5), (4, 1), (4, 5)):
        overlapping_targets[row][col] = 2
    for row, col in ((2, 3), (2, 7), (6, 3), (6, 7)):
        overlapping_targets[row][col] = 7

    trivial_target = [[0] * 8 for _ in range(6)]
    for row, col in ((1, 1), (1, 2), (2, 1), (2, 2)):
        trivial_target[row][col] = 4

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    for mutation in (
        no_target,
        wrong_distractor_count,
        overlapping_targets,
        trivial_target,
        ragged,
    ):
        assert GEN.self_check(mutation), mutation


def test_exact_four_noncorner_fixture_is_lawful_and_refutes_corner_geometry():
    fixture_path = (
        ROOT
        / "generators/42fb6b33deea/"
        "counterexamples/exact_four_noncorner.json"
    )
    fixture = json.loads(fixture_path.read_text())
    witness = fixture["input"]
    assert GEN.self_check(witness) == []
    assert GEN.SEMANTIC_WITNESSES["exact_four_noncorner"](witness)
    authoritative = GEN.rule_mirror(witness)
    rival = GEN.CANONICAL_SHORTCUTS["four_actual_corners_only"](witness)
    assert authoritative == fixture["authoritative_output"]
    assert rival == fixture["rival_output"]
    assert authoritative != rival


def test_determinism_fresh_returns_and_process_global_rng_state():
    random.seed(20260724)
    state = random.getstate()
    first = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 8
    third = GEN.generate(97, 103, difficulty="hard")
    assert third == second


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_target_style_override_is_exact_and_observable(band):
    for style in GEN.TARGET_STYLES:
        grid = GEN.generate(
            1207,
            33,
            difficulty=band,
            grid_h=10,
            grid_w=12,
            n_target_colors=2,
            n_distractor_colors=1,
            target_style=style,
        )
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.observe_overrides(grid)["target_style"] == style
        assert GEN.SEMANTIC_WITNESSES["exact_four_noncorner"](grid) == (
            style == "count_witness"
        )


def test_geometric_corner_shortcut_fits_every_canonical_pair():
    rival = GEN.CANONICAL_SHORTCUTS["four_actual_corners_only"]
    for grid, expected in _canonical_pairs():
        assert rival(grid) == expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_consecutive_samples_refute_geometric_corner_shortcut(band):
    rival = GEN.LESSON_COMPETITORS["four_actual_corners_only"]
    witness = GEN.SEMANTIC_WITNESSES["exact_four_noncorner"]
    for start in range(9):
        demos = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(20261011, sample_index, difficulty=band)
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert any(witness(demo["input"]) for demo in demos)
        assert any(rival(demo["input"]) != demo["output"] for demo in demos)
        query_grid = GEN.generate(
            20261011,
            start + GEN.EXAMPLES_NEEDED,
            difficulty=band,
        )
        query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_rotating_any_query_out_of_four_samples_keeps_the_rule_identifiable(band):
    for start in range(9):
        labeled = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(8675309, sample_index, difficulty=band)
            labeled.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index, query in enumerate(labeled):
            demos = [
                pair for index, pair in enumerate(labeled) if index != query_index
            ]
            assert GEN.lesson_identifiable(demos, query) == []

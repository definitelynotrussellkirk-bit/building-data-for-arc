"""Regression tests for request honesty and lesson-level connectivity evidence."""
from __future__ import annotations

from copy import deepcopy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a631936f7715"
ROOT = find_root(__file__)


def _gen():
    module, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)
    return module


def _pair(gen, grid):
    return {"input": deepcopy(grid), "output": gen._reference_output(grid)}


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1"])
def test_seed_rejects_non_exact_integers(value):
    gen = _gen()
    with pytest.raises((TypeError, ValueError)):
        gen.generate(value, 0, difficulty="easy")


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_rejects_invalid_scalars(value):
    gen = _gen()
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, value, difficulty="easy")


@pytest.mark.parametrize("value", [True, False, 0, 1.0, "expert"])
def test_difficulty_rejects_invalid_values(value):
    gen = _gen()
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, 0, difficulty=value)


def test_unknown_override_key_is_rejected_loudly():
    gen = _gen()
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(991, 0, difficulty="medium", misspelled_axis=3)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", True),
        ("grid_h", 4.0),
        ("grid_h", "4"),
        ("grid_h", 3),
        ("grid_h", 17),
        ("grid_w", False),
        ("grid_w", 8.0),
        ("grid_w", "8"),
        ("grid_w", 3),
        ("grid_w", 17),
        ("component_count", True),
        ("component_count", 2.0),
        ("component_count", "2"),
        ("component_count", 1),
        ("component_count", 6),
        ("palette_kind", 4),
        ("palette_kind", "typo"),
        ("texture", 4),
        ("texture", "typo"),
    ],
)
def test_declared_overrides_reject_invalid_types_and_values(axis, value):
    gen = _gen()
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, 0, difficulty="medium", **{axis: value})


def test_valid_request_controls_still_generate_lawful_inputs():
    gen = _gen()
    requests = [
        {"difficulty": "easy", "grid_h": 5},
        {"difficulty": "medium", "grid_w": 11},
        {"difficulty": "hard", "component_count": 4},
        {"difficulty": "medium", "palette_kind": "cool"},
        {"difficulty": "medium", "texture": "no_labels"},
    ]
    for sample_index, request in enumerate(requests):
        grid = gen.generate(20261023, sample_index, **request)
        assert gen.self_check(grid) == []


def test_lawful_degenerate_textures_are_declared_explicitly():
    gen = _gen()
    assert tuple(gen.LAWFUL_DEGENERATE_TEXTURES) == tuple(gen.DEGENERATE_TEXTURES)


def test_declared_eight_connected_shortcut_fits_every_canonical_pair():
    gen = _gen()
    rival = gen.CANONICAL_SHORTCUTS["eight_connected_components"]
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 6
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert gen._reference_output(pair["input"]) == pair["output"]
        assert rival(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_every_four_phase_lesson_rotation_refutes_eight_connectivity():
    gen = _gen()
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    witness = gen.SEMANTIC_WITNESSES["diagonal_components_stay_separate"]
    rival = gen.SEMANTIC_RIVALS["eight_connected_components"]

    for band in ("easy", "medium", "hard"):
        for block_start in (0, 4):
            grids = [
                gen.generate(81000 + block_start, block_start + offset, difficulty=band)
                for offset in range(4)
            ]
            # The two scheduled witness phases make every possible 3-demo
            # rotation contain a concrete 4-vs-8 counterexample.
            assert witness(grids[0])
            assert witness(grids[2])
            assert all(gen.self_check(grid) == [] for grid in grids)
            assert all(
                gen._reference_output(grid) != rival(grid)
                for grid in (grids[0], grids[2])
            )
            pairs = [_pair(gen, grid) for grid in grids]
            for query_index in range(4):
                query = pairs[query_index]
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == []


def test_connectivity_witness_demonstrates_a_nontrivial_transformation_on_max_canvas():
    """Regression for defect-lint's <5% transformation-drift warning."""
    gen = _gen()
    grid = gen._connectivity_witness_grid(
        random.Random(0), 14, 14, 4, [1, 2, 3, 4]
    )
    output = gen._reference_output(grid)
    changed = sum(
        before != after
        for input_row, output_row in zip(grid, output)
        for before, after in zip(input_row, output_row)
    )
    assert changed / (14 * 14) >= 0.05


def test_retained_connectivity_counterexample_matches_selected_and_rival_outputs():
    gen = _gen()
    folder = ROOT / "generators" / TASK_ID / "counterexamples" / "connectivity-teaching-witness"
    input_grid = __import__("json").loads((folder / "input.json").read_text())
    expected = __import__("json").loads((folder / "expected.json").read_text())
    rival = __import__("json").loads((folder / "eight-connected.json").read_text())
    assert gen.self_check(input_grid) == []
    assert gen._reference_output(input_grid) == expected
    assert gen._eight_connected_components(input_grid) == rival
    assert expected != rival

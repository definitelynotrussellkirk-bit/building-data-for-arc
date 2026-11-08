"""Behavioral contract for the b2862040 input generator.

The tests intentionally recover exact controls from returned pixels.  They do
not trust RNG metadata, and they exercise canonical examples as well as the two
semantic counterexamples that make the lesson identifiable.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "9af68e46cf69"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("b2862040_generator_contract", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)

BANDS = ("easy", "medium", "hard")
AXIS_BOUNDS = {
    "grid_h": (9, 30),
    "grid_w": (11, 30),
    "n_holey": (1, 3),
    "n_solid": (1, 4),
}


def _impostor(kind: str) -> list[list[int]]:
    grid = [[9] * 7 for _ in range(7)]
    if kind == "singleton":
        grid[3][3] = 1
    elif kind == "short_line":
        grid[3][2:5] = [1, 1, 1]
    elif kind == "solid_2x2":
        for r in (2, 3):
            for c in (2, 3):
                grid[r][c] = 1
    elif kind == "all_holey":
        for r in range(2, 5):
            for c in range(2, 5):
                if r in (2, 4) or c in (2, 4):
                    grid[r][c] = 1
    elif kind == "all_solid":
        grid[1][1] = grid[3][3] = grid[5][5] = 1
    elif kind == "all_background":
        pass
    else:  # pragma: no cover - test author error
        raise AssertionError(kind)
    return grid


def test_selected_rule_hash_and_public_axes_are_pinned():
    assert GEN.RULE_HASH == "7fd2884c3200"
    assert set(GEN.AXES) == set(AXIS_BOUNDS)
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_labeled_canonical_pairs_are_accepted_and_solved():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == [], (
            pair["variant"], pair["split"], pair["pair_index"]
        )
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN._apply_rule(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", BANDS)
def test_default_generation_is_deterministic_exact_and_semantically_rich(band):
    for seed in range(12):
        grid = GEN.generate(seed, seed * 17 + 3, difficulty=band)
        assert grid == GEN.generate(seed, seed * 17 + 3, difficulty=band)
        assert GEN.self_check(grid, difficulty=band) == []
        observed = GEN.observe_overrides(grid)
        for axis, (lo, hi) in AXIS_BOUNDS.items():
            assert lo <= observed[axis] <= hi
        assert GEN.SEMANTIC_WITNESSES["irregular_hole"](grid)
        assert GEN.SEMANTIC_WITNESSES["open_bbox_decoy"](grid)
        expected = GEN._apply_rule(grid)
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            assert rival(grid) != expected, (band, seed, name)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "axis,value",
    [(name, value) for name, bounds in AXIS_BOUNDS.items() for value in bounds],
)
def test_single_axis_boundaries_are_exact_in_every_band(band, axis, value):
    for seed in (0, 7):
        grid = GEN.generate(seed, seed + 11, difficulty=band, **{axis: value})
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.observe_overrides(grid)[axis] == value


@pytest.mark.parametrize("band", BANDS)
def test_joint_minimum_canvas_maximum_counts_are_constructive(band):
    requested = {"grid_h": 9, "grid_w": 11, "n_holey": 3, "n_solid": 4}
    for seed in range(6):
        grid = GEN.generate(seed, 29, difficulty=band, **requested)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize("kind", [
    "all_background", "singleton", "short_line", "solid_2x2",
    "all_holey", "all_solid",
])
def test_self_check_rejects_minimal_or_one_class_impostors(kind):
    assert GEN.self_check(_impostor(kind)), kind


def test_self_check_rejects_bad_shape_palette_and_output_color():
    assert GEN.self_check([])
    assert GEN.self_check([[]])
    assert GEN.self_check([[9, 9], [9]])
    bad = GEN.generate(1, 2)
    bad[0][0] = 8
    assert GEN.self_check(bad)
    bad = GEN.generate(1, 2)
    bad[0][0] = True
    assert GEN.self_check(bad)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_literal_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, 1.75, "1"])
def test_sample_index_requires_nonnegative_literal_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_difficulty_is_closed_enum(difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("axis", AXIS_BOUNDS)
@pytest.mark.parametrize("value", [True, False, 3.0, 3.75, "3"])
def test_exact_integer_axes_reject_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


@pytest.mark.parametrize(
    "axis,value",
    [(name, bounds[0] - 1) for name, bounds in AXIS_BOUNDS.items()]
    + [(name, bounds[1] + 1) for name, bounds in AXIS_BOUNDS.items()],
)
def test_axes_reject_out_of_range_values(axis, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{axis: value})


def test_unknown_and_retired_axes_are_rejected():
    for axis in (
        "unknown_axis", "texture", "frame_size_kind", "solid_shape_kind",
        "position_bias", "inter_object_padding",
    ):
        with pytest.raises(ValueError):
            GEN.generate(0, 0, **{axis: 1})


@pytest.mark.parametrize("axis", AXIS_BOUNDS)
def test_none_means_unpinned(axis):
    for seed in range(3):
        assert GEN.generate(seed, 17, **{axis: None}) == GEN.generate(seed, 17)


def test_lesson_hook_reports_surviving_wrong_rules_only():
    demos = []
    for i in range(3):
        inp = GEN.generate(100 + i, i * 11)
        demos.append({"input": inp, "output": GEN._apply_rule(inp)})
    query_in = GEN.generate(200, 37)
    query = {"input": query_in, "output": GEN._apply_rule(query_in)}
    assert GEN.lesson_identifiable(demos, query) == []

    wrong = [{"input": pair["input"], "output": GEN.SEMANTIC_RIVALS["any_bbox_background"](pair["input"])}
             for pair in demos]
    assert GEN.lesson_identifiable(wrong, query)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "filename,witness,rival",
    [
        ("irregular-hole-vs-rectangles.json", "irregular_hole", "rectangular_frames_only"),
        ("open-bbox-vs-any-interior.json", "open_bbox_decoy", "any_bbox_background"),
    ],
)
def test_retained_semantic_counterexamples_are_live(filename, witness, rival):
    import hashlib
    import json

    path = SOURCE.parent / "counterexamples" / filename
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["task_id"] == TASK_ID
    assert payload["generator_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert payload["rule_hash"] == GEN.RULE_HASH
    assert payload["witness"] == witness
    assert payload["rival"] == rival
    grid = payload["input"]
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES[witness](grid)
    assert GEN._apply_rule(grid) == payload["selected_output"]
    assert GEN.SEMANTIC_RIVALS[rival](grid) == payload["rival_output"]
    assert payload["selected_output"] != payload["rival_output"]


def test_workspace_contract_probe_checks_declared_contracts():
    tool = _load_module(
        SOURCE.parent / "workspace" / "probe_contract.py",
        "b2862040_contract_probe",
    )
    report = tool.run_probe(per_band=2)
    assert report["passed"] is True
    assert report["generated_samples"] == 6
    assert report["canonical_pairs"] == len(
        canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    )
    assert set(report["witness_hits"]) == set(GEN.SEMANTIC_WITNESSES)
    assert set(report["rival_disagreements"]) == set(GEN.SEMANTIC_RIVALS)
    assert all(value == 6 for value in report["witness_hits"].values())
    assert all(value == 6 for value in report["rival_disagreements"].values())

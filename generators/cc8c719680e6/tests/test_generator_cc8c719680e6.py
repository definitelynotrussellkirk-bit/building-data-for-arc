"""Focused semantic, override, and regression tests for cc8c719680e6."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import random
from pathlib import Path
import sys

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash
from puzzle_generators.per_puzzle.cc8c719680e6 import generator as gen


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _pair(seed: int, sample_index: int, difficulty: str):
    source = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": source, "output": gen.rule_mirror(source)}


def _negative_overlapping_bboxes():
    grid = [[0] * 7 for _ in range(7)]
    # Two disconnected components have no shared source cells, but their bbox
    # footprints overlap at rows 2..3 / column 3.  This feature is absent from
    # the third component and from every lawful generated scene.
    for r, c in {(1, 1), (1, 2), (2, 2), (3, 2), (3, 3)}:
        grid[r][c] = 1
    for r, c in {(2, 4), (3, 4), (4, 4), (4, 3)}:
        grid[r][c] = 2
    for r, c in {(5, 0), (5, 1), (6, 0)}:
        grid[r][c] = 3
    return grid


def test_identity_and_rule_pin():
    assert gen.GENERATOR_ID == gen.TASK_ID == "cc8c719680e6"
    assert gen.VERSION == "2.3.0"
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID) == "8f9e53b42241"
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.MIN_STRICT_FRAC == 0.4
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {
        "scene_profile",
        "n_blobs",
        "color_relation",
        "edge_mode",
        "palette_kind",
    }


@pytest.mark.parametrize("pair", canonical_pairs(gen.TASK_ID))
def test_all_canonical_pairs_are_accepted_and_python_mirror_matches(pair):
    original = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_natural_schedule_is_exact_deterministic_and_semantically_live(difficulty):
    grids = [gen.generate(7301, index, difficulty=difficulty) for index in range(32)]
    assert grids == [gen.generate(7301, index, difficulty=difficulty) for index in range(32)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    signatures = [gen.semantic_signature(grid) for grid in grids]
    assert all(item["adds"] > 0 for item in signatures)
    assert sum(item["deletes"] > 0 for item in signatures) >= 16
    assert {item["scene_profile"] for item in signatures} == set(gen.SCENE_PROFILES)
    assert {item["n_blobs"] for item in signatures} == set(gen.N_BLOBS)
    assert {item["color_relation"] for item in signatures} == set(gen.COLOR_RELATIONS)
    assert {item["edge_mode"] for item in signatures} == set(gen.EDGE_MODES)
    assert {item["palette_kind"] for item in signatures} == set(gen.PALETTE_KINDS)
    assert len({_key(grid) for grid in grids}) >= 28


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_default_cycle_anchors_the_strict_joint_canonical_manifold(difficulty):
    grids = [gen.generate(1517, index, difficulty=difficulty) for index in range(4)]
    strict = [gen.strict_canonical_like(grid) == [] for grid in grids]
    assert strict == [True, False, True, False]
    assert [gen.observe_overrides(grid)["n_blobs"] for grid in grids] == [2, 4, 2, 3]
    # Some exact canonical profiles have no interior source cell, so the
    # four-example lesson—not one fixed slot—owns the deletion witness.
    assert any(gen.semantic_signature(grid)["deletes"] > 0 for grid in grids)


def test_difficulty_changes_realization_without_changing_declared_schedule():
    grids = {
        band: gen.generate(991, 5, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({_key(grid) for grid in grids.values()}) >= 2
    observations = [gen.observe_overrides(grid) for grid in grids.values()]
    assert observations[0] == observations[1] == observations[2]


def test_full_exact_override_cartesian_product_is_constructible_and_observable():
    domains = (
        gen.SCENE_PROFILES,
        gen.N_BLOBS,
        gen.COLOR_RELATIONS,
        gen.EDGE_MODES,
        gen.PALETTE_KINDS,
    )
    for index, values in enumerate(itertools.product(*domains)):
        overrides = dict(zip(gen.AXES, values))
        grid = gen.generate(20000 + index, index, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="accepted-would-be-a-defect")


def test_generation_is_fresh_and_does_not_touch_process_global_rng():
    random.seed(8675309)
    state = random.getstate()
    first = gen.generate(88, 2, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(88, 2, difficulty="medium")
    assert first == second and first is not second
    pristine = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == pristine


def test_self_check_rejects_targeted_rule_hiding_and_structural_impostors():
    blank = [[0] * 7 for _ in range(7)]

    singleton_pair = [[0] * 7 for _ in range(7)]
    singleton_pair[1][1] = 1
    singleton_pair[5][5] = 2

    line_pair = [[0] * 7 for _ in range(7)]
    for c in range(1, 4):
        line_pair[1][c] = 1
    for r in range(3, 6):
        line_pair[r][5] = 2

    solid_rectangles = [[0] * 7 for _ in range(7)]
    for r in range(1, 3):
        for c in range(1, 3):
            solid_rectangles[r][c] = 1
    for r in range(4, 6):
        for c in range(4, 6):
            solid_rectangles[r][c] = 2

    completed_frames = [[0] * 7 for _ in range(7)]
    for color, (r0, c0) in enumerate(((1, 1), (4, 4)), start=1):
        for r in range(r0, r0 + 2):
            for c in range(c0, c0 + 2):
                completed_frames[r][c] = color

    overlapping_bboxes = _negative_overlapping_bboxes()
    impostors = {
        "blank": blank,
        "singletons": singleton_pair,
        "one-dimensional lines": line_pair,
        "solid rectangles": solid_rectangles,
        "already-complete frames": completed_frames,
        "overlapping bbox footprints": overlapping_bboxes,
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name
        assert gen.strict_canonical_like(grid), name
        assert gen.observe_overrides(grid) == {}, name


def test_negative_recombination_is_distribution_rejected_but_mirror_executable():
    grid = _negative_overlapping_bboxes()
    assert any("overlap" in reason for reason in gen.self_check(grid))
    output = gen.rule_mirror(grid)
    assert len(output) == 7 and all(len(row) == 7 for row in output)
    assert all(0 <= value <= 9 for row in output for value in row)


def test_every_named_witness_and_rival_has_a_generated_discriminator():
    grids = [gen.generate(1042, index, difficulty="medium") for index in range(8)]
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(rival(grid) != gen.rule_mirror(grid) for grid in grids), name
    repeated = next(
        grid
        for grid in grids
        if gen.SEMANTIC_WITNESSES["same_color_components_stay_separate"](grid)
    )
    assert gen.CANONICAL_SHORTCUTS["one_bbox_per_color"](repeated) != gen.rule_mirror(repeated)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_sliding_four_example_window_identifies_the_rule(difficulty):
    # Exhaust every residue-class start, plus a second cycle.  The semantic gate
    # uses arbitrary start offsets, so aggregate schedule coverage is not enough.
    for start in range(8):
        demos = [_pair(500 + start, index, difficulty) for index in range(start, start + 4)]
        query = _pair(900 + start, start + 4, difficulty)
        assert gen.lesson_identifiable(demos, query) == []


def test_undercovered_lesson_is_rejected():
    demos = [_pair(123, index, "easy") for index in range(3)]
    query = _pair(124, 3, "easy")
    errors = gen.lesson_identifiable(demos, query)
    assert any("at least 4" in error for error in errors)


def _bbox_span(component):
    r0, c0, r1, c1 = component["bbox"]
    return r1 - r0 + 1, c1 - c0 + 1


def _joint_profile(grid):
    analysis = gen._analyze(grid)
    assert analysis["errors"] == []
    facts = analysis["facts"]
    return (
        facts["height"],
        facts["width"],
        bool(facts["touching"]),
        tuple(sorted(gen._morphology_signature(item) for item in facts["components"])),
    )


def test_default_sampling_reaches_every_canonical_joint_profile():
    observed = set()
    for seed in range(64):
        for sample_index in (0, 2):
            grid = gen.generate(seed, sample_index, difficulty="medium")
            if gen.strict_canonical_like(grid) == []:
                observed.add(_joint_profile(grid))
    assert observed == gen._CANONICAL_JOINT_PROFILES


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_every_default_lesson_window_breaks_legacy_bbox_span_lookup(difficulty):
    # The previous production distribution used only these four exact bbox
    # spans, allowing a shape-template lookup to fit every generated lesson.
    legacy_spans = {(2, 2), (3, 2), (3, 3), (3, 4)}
    novel_spans = set()
    for start in range(8):
        lesson_grids = [
            gen.generate(8100 + start, index, difficulty=difficulty)
            for index in range(start, start + gen.EXAMPLES_NEEDED)
        ]
        lesson_novel = {
            _bbox_span(component)
            for grid in lesson_grids
            for component in gen._components(grid)
            if _bbox_span(component) not in legacy_spans
        }
        assert lesson_novel, f"start={start} contains only legacy bbox spans"
        novel_spans.update(lesson_novel)

    # Require more than a single token counterexample: generalized slots should
    # teach several genuinely different component extents.
    assert len(novel_spans) >= 3


def test_morphology_probe_reconstructs_facts_without_generator_private_helpers(monkeypatch):
    local_root = Path(__file__).resolve().parents[1]
    probe_path = local_root / "workspace" / "morphology_distribution_probe.py"
    if not probe_path.is_file():
        probe_path = local_root / "generators" / gen.TASK_ID / "workspace" / "morphology_distribution_probe.py"
    module_name = "cc8c719680e6_morphology_probe_test"
    spec = importlib.util.spec_from_file_location(module_name, probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = probe
    spec.loader.exec_module(probe)

    class GenerateOnly:
        TASK_ID = gen.TASK_ID
        VERSION = gen.VERSION

        @staticmethod
        def generate(seed, sample_index, *, difficulty=None, **overrides):
            return gen.generate(seed, sample_index, difficulty=difficulty, **overrides)

        def __getattr__(self, name):
            raise AssertionError(f"probe accessed producer-owned helper: {name}")

    monkeypatch.setattr(probe, "_load_generator", lambda _path: GenerateOnly())
    report = probe.measure(Path(gen.__file__), seeds=1)
    assert report["seeds_per_band"] == 1
    assert all(row["generated_grids"] == 4 for row in report["bands"].values())


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_combined_windows_keep_morphology_and_connectivity_witnesses(difficulty):
    for start in range(12):
        grids = [gen.generate(3400 + start, i, difficulty=difficulty)
                 for i in range(start, start + gen.EXAMPLES_NEEDED)]
        for name in ("legacy_bbox_span_lookup", "same_color_8_connected", "color_blind_4_connected"):
            assert any(gen.SEMANTIC_RIVALS[name](grid) != gen.rule_mirror(grid) for grid in grids), (difficulty, start, name)

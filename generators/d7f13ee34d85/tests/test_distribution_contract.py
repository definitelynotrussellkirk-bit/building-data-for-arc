"""Regressions for canonical support and the executable sampling contract."""
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "d7f13ee34d85"
ROOT = find_root(__file__)
TASK_DIR = next(p for p in Path(__file__).resolve().parents
                if p.is_relative_to(ROOT) and p.name == TASK and (p / "generator.py").is_file())
SOURCE = TASK_DIR / "generator.py"
spec = importlib.util.spec_from_file_location("reviewed_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_all_canonical_inputs_are_in_domain_in_every_band():
    for pair in canonical_pairs(TASK, root=find_root(SOURCE), labeled_only=True):
        for band in (None, "easy", "medium", "hard"):
            assert gen.self_check(pair["input"], difficulty=band) == []


def test_rule_pin_and_diagnostic_agree_with_all_canonical_labels():
    assert getattr(gen, "RULE_HASH", None) == "435fa9a55dd3"
    for pair in canonical_pairs(TASK, root=find_root(SOURCE), labeled_only=True):
        assert gen.diagnostic_transform(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_schedule_start_teaches_declared_rivals(band):
    assert getattr(gen, "LESSON_SCHEDULE_PERIOD", 0) > 0
    assert set(gen.CANONICAL_SHORTCUTS) == {"frame_height", "frame_perimeter"}
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        demos = [gen.generate(0, start+i, difficulty=band) for i in range(gen.EXAMPLES_NEEDED)]
        pairs = [{"input": g, "output": gen.diagnostic_transform(g)} for g in demos]
        query = gen.generate(0, start+gen.EXAMPLES_NEEDED, difficulty=band)
        assert gen.lesson_identifiable(pairs, query) == []
        assert any(gen.has_negative_centering(g) for g in demos)
        for rival in gen.LESSON_COMPETITORS.values():
            assert any(rival(p["input"]) != p["output"] for p in pairs)


def test_canonical_shortcut_declarations_are_true():
    assert getattr(gen, "CANONICAL_SHORTCUTS", {})
    pairs = canonical_pairs(TASK, root=find_root(SOURCE), labeled_only=True)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p["input"]) == p["output"] for p in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_query_rotation_retains_teaching_evidence(band):
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        grids = [gen.generate(0, start+i, difficulty=band) for i in range(gen.EXAMPLES_NEEDED+1)]
        pairs = [{"input": g, "output": gen.diagnostic_transform(g)} for g in grids]
        for held_out in range(len(pairs)):
            demos = [p for i, p in enumerate(pairs) if i != held_out]
            assert gen.lesson_identifiable(demos, pairs[held_out]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_ordinary_samples_cover_canonical_branches_and_vary_sizes(band):
    assert hasattr(gen, "observe_axes")
    grids = [gen.generate(seed, seed % 3, difficulty=band) for seed in range(36)]
    assert all(gen.self_check(g, difficulty=band) == [] for g in grids)
    assert any(gen.has_negative_centering(g) for g in grids)
    assert any(gen.observe_axes(g)["frame_palette"] == "shared" for g in grids)
    assert any(any(o["h"] != o["w"] for o in gen.split_objects(g)[0]) for g in grids)
    assert len({tuple(sorted(o["size"] for o in gen.split_objects(g)[1])) for g in grids}) >= 4


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_controls_have_observable_effects(band):
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_frames", "frame_palette", "shape_relation"}
    cases = {"grid_h": (13, 24), "grid_w": (18, 28), "n_frames": (2, 4),
             "frame_palette": ("shared", "distinct"), "shape_relation": ("fits", "oversized")}
    for axis, values in cases.items():
        for value in values:
            g = gen.generate(13, 1, difficulty=band, **{axis: value})
            assert gen.self_check(g, difficulty=band) == []
            assert gen.observe_axes(g)[axis] == value


def test_joint_boundary_and_invalid_requests():
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_w=18, n_frames=4)
    with pytest.raises(ValueError):
        gen.generate(0, 0, __unknown_axis__=1)
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h="13")
    assert gen.self_check([])
    assert gen.self_check([[False]])
    for relation in ("fits", "oversized"):
        g = gen.generate(9, 1, grid_h=13, grid_w=22, n_frames=4,
                         frame_palette="distinct", shape_relation=relation)
        assert gen.self_check(g) == []
        assert gen.observe_axes(g)["shape_relation"] == relation


def test_advancing_seed_and_index_together_preserves_broad_support():
    grids = [gen.generate(seed, seed, difficulty="medium") for seed in range(16)]
    assert max(len(g) for g in grids) > 15
    assert max(len(g[0]) for g in grids) > 20
    assert any(gen.generate(seed, seed, difficulty="easy") !=
               gen.generate(seed, seed, difficulty="hard") for seed in range(16))


@pytest.mark.parametrize("filename", ["canonical-negative-centering.json", "rank-reversal.json"])
def test_retained_authority_counterexamples(filename):
    witness = json.loads((TASK_DIR / "counterexamples" / filename).read_text())
    assert witness["executed_rule_hash"] == gen.RULE_HASH
    assert gen.self_check(witness["input"]) == []
    assert gen.diagnostic_transform(witness["input"]) == witness["output"]
    assert gen.has_negative_centering(witness["input"])
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert rival(witness["input"]) == witness["rival_outputs"][name]
    assert witness["rival_outputs"]["clamp_negative_offset"] != witness["output"]
    if filename == "rank-reversal.json":
        assert all(prediction != witness["output"] for prediction in witness["rival_outputs"].values())

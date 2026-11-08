"""Regression tests for the multi-rectangle completion generator."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = ROOT / "generators" / "39574cf4b561" / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_39574cf4b561", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs():
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row["train"] + row["test"]
    raise AssertionError("canonical task row not found")


def role_counts(grid):
    counts = Counter(value for row in grid for value in row if value)
    return Counter(counts.values())


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_all_canonical_inputs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]

@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_draws_preserve_the_canonical_color_roles(difficulty):
    seen_profiles = set()
    seen_relations = set()
    seen_palettes = set()
    for sample_index in range(40):
        grid = GEN.generate(10_000 + sample_index, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert role_counts(grid) in (
            Counter({3: 3, 1: 1}),
            Counter({3: 4, 1: 1}),
        )
        observed = GEN.observe_overrides(grid)
        seen_profiles.add(observed["scene_profile"])
        seen_relations.add(observed["distractor_relation"])
        seen_palettes.add(observed["palette_kind"])
    assert seen_profiles == set(GEN.SCENE_PROFILES)
    assert seen_relations == set(GEN.DISTRACTOR_RELATIONS)
    assert seen_palettes == set(GEN.PALETTE_KINDS)

def test_exact_override_cross_product_is_observable():
    for profile in GEN.SCENE_PROFILES:
        for missing in GEN.MISSING_PATTERNS:
            for relation in GEN.DISTRACTOR_RELATIONS:
                for palette in GEN.PALETTE_KINDS:
                    grid = GEN.generate(
                        321,
                        17,
                        difficulty="hard",
                        scene_profile=profile,
                        missing_pattern=missing,
                        distractor_relation=relation,
                        palette_kind=palette,
                    )
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == {
                        "scene_profile": profile,
                        "missing_pattern": missing,
                        "distractor_relation": relation,
                        "palette_kind": palette,
                    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"missing_pattern": "diagonal"},
        {"distractor_relation": "overlap_corner"},
        {"palette_kind": "all"},
        {"grid_h": 11},
        {"difficulty": "expert"},
    ],
)
def test_unknown_or_out_of_domain_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        GEN.generate(1, 0, **kwargs)


def test_replay_returns_fresh_objects_and_preserves_global_rng():
    random.seed(77191)
    before = random.getstate()
    first = GEN.generate(91, 23, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(91, 23, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert first != second


def test_self_check_rejects_minimal_impostors():
    base = GEN.generate(
        17,
        2,
        scene_profile="p11x11_three",
        missing_pattern="mixed",
        distractor_relation="inside",
        palette_kind="mixed",
    )
    assert GEN.self_check(base) == []

    blank = [[0 for _ in row] for row in base]
    no_singleton = copy.deepcopy(base)
    for row in no_singleton:
        for index, value in enumerate(row):
            if value == 9:
                row[index] = 0

    complete_one = copy.deepcopy(base)
    rectangle = GEN._analyze(base)["rectangles"][0]
    row, col = rectangle["missing"]
    complete_one[row][col] = rectangle["color"]

    collinear = copy.deepcopy(base)
    color = GEN._analyze(base)["active_colors"][0]
    for row in collinear:
        for index, value in enumerate(row):
            if value == color:
                row[index] = 0
    collinear[0][1] = color
    collinear[0][4] = color
    collinear[0][7] = color

    for impostor in (blank, no_singleton, complete_one, collinear):
        assert GEN.self_check(impostor), impostor

def test_every_semantic_witness_has_a_live_rival_counterexample():
    assert hasattr(GEN, "SEMANTIC_WITNESSES")
    assert hasattr(GEN, "SEMANTIC_RIVALS")
    assert hasattr(GEN, "WITNESS_RIVALS")
    hits = Counter()
    for sample_index in range(80):
        grid = GEN.generate(70_000 + sample_index, sample_index)
        truth = GEN.rule_mirror(grid)
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            hits[name] += 1
            rival_names = GEN.WITNESS_RIVALS.get(name, ())
            assert rival_names, name
            assert any(
                GEN.SEMANTIC_RIVALS[rival](grid) != truth
                for rival in rival_names
            ), name
    assert set(hits) == set(GEN.SEMANTIC_WITNESSES)

def test_axes_declaration_is_statically_literal_for_the_linter():
    import ast

    tree = ast.parse(GENERATOR_PATH.read_text())
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    try:
        value = ast.literal_eval(assignment.value)
    except (ValueError, TypeError) as exc:
        pytest.fail(f"AXES must be statically literal: {exc}")
    assert set(value) == set(GEN.AXES)

def test_difficulty_bands_change_nuisance_geometry_without_changing_the_rule():
    for sample_index in range(12):
        grids = {
            frozen(
                GEN.generate(
                    90_000 + sample_index,
                    sample_index,
                    difficulty=difficulty,
                )
            )
            for difficulty in ("easy", "medium", "hard")
        }
        assert len(grids) >= 2

def test_role_signature_gate_catches_the_baseline_singleton_omission():
    tool_path = (
        ROOT
        / "generators"
        / "39574cf4b561"
        / "workspace"
        / "role_signature_gate.py"
    )
    assert tool_path.exists(), "role-signature gate has not been built"
    tool_spec = importlib.util.spec_from_file_location(
        "role_signature_gate_39574cf4b561", tool_path
    )
    assert tool_spec and tool_spec.loader
    tool = importlib.util.module_from_spec(tool_spec)
    tool_spec.loader.exec_module(tool)

    canonical_signatures = {
        tool.role_signature(pair["input"]) for pair in canonical_pairs()
    }
    assert canonical_signatures == {
        ((1, 1), (3, 3)),
        ((1, 1), (3, 4)),
    }

    baseline_like = [[0] * 10 for _ in range(10)]
    for color, cells in {
        1: ((0, 0), (0, 2), (2, 0)),
        2: ((3, 3), (3, 5), (5, 3)),
        3: ((6, 6), (6, 8), (8, 6)),
    }.items():
        for row, col in cells:
            baseline_like[row][col] = color
    assert tool.role_signature(baseline_like) == ((3, 3),)
    assert tool.role_signature(baseline_like) not in canonical_signatures

    report = tool.audit(draws_per_band=20)
    assert report["status"] == "PASS"
    assert all(not row["missing"] and not row["unexpected"] for row in report["bands"].values())

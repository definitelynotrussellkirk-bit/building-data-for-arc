"""Task-local regression tests for the 195dfcc5b541 generator repair."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    changed_cells,
    geometry_output,
    load_generator,
    no_copy_mutant,
    racket_outputs,
    rotation_only_output,
    stencil_cells,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned_to_current_authority():
    assert gen.RULE_HASH == "22e420574f26"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_accepts_every_canonical_input_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 11, "grid_w": 17, "shape_variant": 0, "copy_count": 2},
        {"grid_h": 18, "grid_w": 18, "shape_variant": 1, "copy_count": 4},
    ],
)
def test_exact_overrides_are_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 10),
        ("grid_h", 19),
        ("grid_w", 16),
        ("grid_w", 19),
        ("shape_variant", -1),
        ("shape_variant", 2),
        ("copy_count", 1),
        ("copy_count", 5),
        ("copy_count", 2.5),
        ("grid_h", True),
        ("shape_variant", "0"),
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_fire_rule_and_refute_rotation_only_rival(band):
    for shape_variant in range(2):
        for index in range(12):
            grid = gen.generate(600 + index, index * 7, difficulty=band, shape_variant=shape_variant)
            intended = geometry_output(grid)
            rival = rotation_only_output(grid)
            assert gen.self_check(grid) == []
            assert intended != grid
            assert rival != intended
            assert gen.SEMANTIC_WITNESSES["reflection_required"](grid)
            assert gen.SEMANTIC_RIVALS["rotations_only"](grid) == rival


def test_stencil_position_support_reaches_edges_and_interior():
    positions = set()
    edge_kinds = set()
    for index in range(256):
        grid = gen.generate(9100 + index, index)
        cells = stencil_cells(grid)
        min_row = min(row for row, _ in cells)
        max_row = max(row for row, _ in cells)
        min_col = min(col for _, col in cells)
        max_col = max(col for _, col in cells)
        positions.add((min_row, min_col))
        if min_row == 0:
            edge_kinds.add("top")
        if max_row == len(grid) - 1:
            edge_kinds.add("bottom")
        if min_col == 0:
            edge_kinds.add("left")
        if max_col == len(grid[0]) - 1:
            edge_kinds.add("right")
        if 0 < min_row and max_row < len(grid) - 1 and 0 < min_col and max_col < len(grid[0]) - 1:
            edge_kinds.add("interior")
    assert len(positions) > 40
    assert edge_kinds == {"top", "bottom", "left", "right", "interior"}


def test_self_check_rejects_dense_palette_preserving_no_copy_mutant():
    original = gen.generate(0, 0)
    mutant = no_copy_mutant(original)
    assert set(value for row in mutant for value in row) == {0, 2, 3, 4, 7, 8}
    assert geometry_output(mutant) == mutant
    assert gen.self_check(mutant)


def test_rotation_only_is_exact_canonical_training_shortcut_but_not_full_rule():
    training = canonical_pairs(training_only=True)
    assert all(rotation_only_output(pair["input"]) == pair["output"] for pair in training)
    query = canonical_pairs()[-1]
    intended = geometry_output(query["input"])
    rival = rotation_only_output(query["input"])
    assert intended == query["output"]
    assert rival != intended
    assert changed_cells(rival, intended) == [(13, 2), (13, 3), (14, 3), (14, 4)]


def test_generation_is_deterministic_and_does_not_mutate_inputs():
    first = gen.generate(412, 111, difficulty="hard")
    assert gen.generate(412, 111, difficulty="hard") == first
    original = deepcopy(first)
    geometry_output(first)
    rotation_only_output(first)
    gen.self_check(first)
    assert first == original


def test_generation_is_constructive_and_does_not_call_solver_oracles(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("generation must not solve its own input")

    monkeypatch.setattr(gen, "_intended_rule", forbidden)
    monkeypatch.setattr(gen, "_rotation_only", forbidden)
    grid = gen.generate(99, 7, grid_h=11, grid_w=17, shape_variant=1, copy_count=4)
    assert len(grid) == 11 and len(grid[0]) == 17


def test_override_observer_uses_input_structure_not_solver_output(monkeypatch):
    grid = gen.generate(101, 8, grid_h=18, grid_w=18, shape_variant=0, copy_count=3)

    def forbidden(*args, **kwargs):
        raise AssertionError("override observation must not run a solver")

    monkeypatch.setattr(gen, "_intended_rule", forbidden)
    assert gen.observe_overrides(grid) == {
        "grid_h": 18,
        "grid_w": 18,
        "shape_variant": 0,
        "copy_count": 3,
    }


def test_real_racket_authority_matches_independent_geometry_oracle():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(
        gen.generate(7300 + index, index * 13, shape_variant=index % 2, copy_count=2 + index % 3)
        for index in range(24)
    )
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]



def test_reference_probe_supports_alternate_portable_runtime_layout(tmp_path):
    runtime = tmp_path / "runtime"
    task_home = runtime / "per_puzzle" / gen.TASK_ID
    workspace = task_home / "workspace"
    workspace.mkdir(parents=True)
    shutil.copy2(HOME / "generator.py", task_home / "generator.py")
    copied_probe = workspace / "reference_probe.py"
    shutil.copy2(HOME / "workspace" / "reference_probe.py", copied_probe)

    pairs = canonical_pairs()
    ledger = runtime / "data" / "canonical" / "puzzles.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        json.dumps(
            {
                "task_id": gen.TASK_ID,
                "train": pairs[:-1],
                "test": pairs[-1:],
                "program_solution": "(rule! identity)",
            }
        )
        + "\n"
    )

    spec = importlib.util.spec_from_file_location("portable_reference_probe", copied_probe)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert len(module.canonical_pairs()) == len(pairs)
    assert module.load_generator().TASK_ID == gen.TASK_ID



def test_shortcut_probe_discovers_declared_rivals_and_all_lesson_rotations():
    probe_path = HOME / "workspace" / "shortcut_probe.py"
    spec = importlib.util.spec_from_file_location("shortcut_probe_under_test", probe_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report = module.build_report(
        gen,
        seeds=[1234],
        starts=[0, 1],
        bands=[None, "hard"],
        verify_racket=False,
    )
    shortcut = report["canonical_shortcuts"]["rotations_only"]
    assert shortcut["training"] == {"fits": 4, "pairs": 4}
    assert shortcut["all_labeled"] == {"fits": 4, "pairs": 5}
    assert report["generated"]["samples"] == 10
    assert report["generated"]["counterexamples"]["rotations_only"] == 10
    assert report["lessons"]["windows"] == 4
    assert report["lessons"]["query_rotations"] == 16
    assert report["lessons"]["ambiguous_rotations"] == []
    assert report["status"] == "pass"

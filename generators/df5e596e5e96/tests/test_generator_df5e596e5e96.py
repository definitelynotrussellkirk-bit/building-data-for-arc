from __future__ import annotations

import copy
import importlib
import importlib.util
import random
import sys
import types
from pathlib import Path

import pytest

try:
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash
except ModuleNotFoundError as exc:
    # The full review repo stores portable ``scripts`` under shared/tools,
    # while prepared runtimes expose that same directory as ``scripts``.
    # Install the package alias only for direct source-tree test runs.
    if exc.name != "scripts":
        raise
    repo_root = Path(__file__).resolve().parents[3]
    scripts_pkg = types.ModuleType("scripts")
    scripts_pkg.__path__ = [str(repo_root / "shared" / "tools")]
    sys.modules["scripts"] = scripts_pkg
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK = "df5e596e5e96"
try:
    GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
except ModuleNotFoundError as exc:
    if exc.name not in {
        f"puzzle_generators.per_puzzle.{TASK}",
        f"puzzle_generators.per_puzzle.{TASK}.generator",
    }:
        raise
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK}_generator", generator_path)
    assert spec is not None and spec.loader is not None
    GEN = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GEN)


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_canonical_inputs_and_python_mirror_match_authority_examples():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK)
    pairs = canonical_pairs(TASK)
    assert len(pairs) == 5
    for pair in pairs:
        pristine = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == pristine


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n_panels", [3, 5])
def test_n_panels_override_is_exact_observable_and_lawful(difficulty, n_panels):
    grid = GEN.generate(4101, 7, difficulty=difficulty, n_panels=n_panels)
    assert GEN.observe_overrides(grid)["n_panels"] == n_panels
    assert len(grid) == 5
    assert len(grid[0]) == 6 * n_panels - 1
    assert GEN.self_check(grid, difficulty=difficulty) == []


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    for bad in (2, 6, True, 3.5, "5"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 0, n_panels=bad)


def test_four_slot_schedule_covers_relation_and_palette_counterexamples():
    grids = [GEN.generate(90210, i, difficulty="medium") for i in range(4)]
    assert [GEN.schedule_profile(90210, i, "medium") for i in range(4)] == list(
        GEN.SCHEDULE_PROFILES
    )
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["same_count_unrelated"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["cross_color_related"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["reflection_relation"](grid) for grid in grids)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_sliding_three_demo_window_refutes_all_declared_competitors(difficulty):
    for start in range(8):
        pairs = []
        for sample_index in range(start, start + 4):
            grid = GEN.generate(7000 + start, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_same_count_unrelated_and_color_blind_shortcuts_fit_canonical_but_not_schedule():
    pairs = canonical_pairs(TASK)
    for name in ("same_count_implies_rotation", "color_sensitive"):
        rival = GEN.CANONICAL_SHORTCUTS[name]
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    grids = [GEN.generate(1234, i, difficulty="hard") for i in range(4)]
    official = [GEN.rule_mirror(grid) for grid in grids]
    for name in ("same_count_implies_rotation", "color_sensitive"):
        rival = GEN.CANONICAL_SHORTCUTS[name]
        assert any(rival(grid) != answer for grid, answer in zip(grids, official))


def test_deterministic_fresh_outputs_and_global_random_independence():
    random.seed(0xDF5E)
    before = random.getstate()
    first = GEN.generate(991, 3, difficulty="hard")
    assert random.getstate() == before
    second = GEN.generate(991, 3, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert frozen(first) != frozen(second)


def test_default_curriculum_varies_relation_matrix_not_only_rendering():
    outputs = {
        frozen(GEN.rule_mirror(GEN.generate(seed, index, difficulty="medium")))
        for seed in range(12)
        for index in range(8)
    }
    assert len(outputs) >= 32


def test_semantic_census_tool_checks_all_cyclic_starts_without_ambiguity():
    tool_path = Path(__file__).resolve().parents[1] / "workspace" / "semantic_census.py"
    spec = importlib.util.spec_from_file_location("df5e_semantic_census", tool_path)
    assert spec is not None and spec.loader is not None
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    report = tool.run_census(lessons_per_band=4, seed_base=8800)
    assert report["cyclic_starts"] == [0, 1, 2, 3]
    assert report["lessons_total"] == 12
    assert report["ambiguous_lessons"] == 0
    assert all(stats["unique_inputs"] == 16 for stats in report["bands"].values())

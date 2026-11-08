"""Focused regression tests for bf8910eef99b."""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (ROOT as reference_root, PALETTES, PROFILES, RIVALS, block, canonical_pairs,
                             load_generator, observed, oracle_output, racket_outputs,
                             witness_input)

gen = load_generator()


def test_contract_is_pinned_and_only_observable_axes_are_advertised():
    assert gen.RULE_HASH == "f45b7e9216b7"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "placement_profile", "palette_id"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_axes_metadata_is_static_literal_for_repository_linter():
    import ast
    source = (HOME / "generator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignment = next(node for node in tree.body
                      if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "AXES"
                              for target in node.targets))
    assert set(ast.literal_eval(assignment.value)) == {
        "grid_h", "grid_w", "placement_profile", "palette_id"
    }


def test_selected_base_authority_is_textually_synchronized():
    import json
    canonical_path = reference_root / "shared/data/canonical/puzzles.jsonl"
    canonical_program = None
    for line in canonical_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "bf8910eef99b":
            canonical_program = row["program_solution"]
            break
    assert canonical_program is not None
    base_path = reference_root / "shared/data/base/solutions/training/93b581b8__bf8910eef99b.json"
    base = json.loads(base_path.read_text(encoding="utf-8"))
    assert base["racket_target"]["raw_code"] == canonical_program
    assert base["racket_target"]["target_code"] == canonical_program


@pytest.mark.parametrize("pair", canonical_pairs(),
                         ids=lambda pair: f"{pair['split']}{pair['pair_index']}")
def test_accepts_every_canonical_pair_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert oracle_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("palette_id", range(len(PALETTES)))
def test_all_exact_controls_are_honored_and_recoverable(band, profile, palette_id):
    expected = {"grid_h": 9, "grid_w": 8,
                "placement_profile": profile, "palette_id": palette_id}
    grid = gen.generate(41, 17, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert observed(grid) == expected
    assert gen.observe_overrides(grid) == expected
    assert oracle_output(grid) != grid


@pytest.mark.parametrize("key,value", [
    ("typo", 1), ("grid_h", 5), ("grid_h", 10), ("grid_w", 5),
    ("grid_w", 10), ("grid_h", True), ("grid_w", 7.0),
    ("palette_id", -1), ("palette_id", 6), ("palette_id", "1"),
    ("placement_profile", "center"), ("placement_profile", 1),
    ("texture", "too_close_to_edge"), ("anchor_corner", True),
])
def test_invalid_retired_and_unknown_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_invalid_seed_scalars_are_rejected(seed):
    with pytest.raises(ValueError, match="seed"):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_sample_index_scalars_are_rejected(sample_index):
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(0, sample_index)


@pytest.mark.parametrize("difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_invalid_difficulty_scalars_are_rejected(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_production_distribution_is_lawful_deterministic_and_teaching_rich(band):
    profiles, palettes, heights, widths, inputs = set(), set(), set(), set(), set()
    for index in range(160):
        grid = gen.generate(9001 + index, index * 13 + 5, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert grid == gen.generate(9001 + index, index * 13 + 5, difficulty=band)
        stats = observed(grid)
        assert stats["placement_profile"] in PROFILES
        assert stats["palette_id"] in range(len(PALETTES))
        truth = oracle_output(grid)
        for rival in RIVALS.values():
            assert rival(grid) != truth
        profiles.add(stats["placement_profile"])
        palettes.add(stats["palette_id"])
        heights.add(stats["grid_h"])
        widths.add(stats["grid_w"])
        inputs.add(tuple(tuple(row) for row in grid))
    assert profiles == set(PROFILES)
    assert palettes == set(range(len(PALETTES)))
    assert 6 in heights and len(heights) >= 3
    assert 6 in widths and len(widths) >= 3
    assert len(inputs) >= 150


def test_declared_rivals_match_independent_implementations_and_are_pure():
    assert set(gen.SEMANTIC_RIVALS) == set(RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(RIVALS) - {"canonical_palette_memorization"}
    assert set(gen.SEMANTIC_WITNESSES) == set(RIVALS)
    assert set(gen.CANONICAL_SHORTCUTS) == {"canonical_palette_memorization"}
    for profile in PROFILES:
        grid = gen.generate(73, 4, grid_h=7, grid_w=8,
                            placement_profile=profile, palette_id=2)
        original = deepcopy(grid)
        truth = oracle_output(grid)
        for name, independent in RIVALS.items():
            first = gen.SEMANTIC_RIVALS[name](grid)
            second = gen.SEMANTIC_RIVALS[name](grid)
            assert first == second == independent(grid)
            assert first != truth
            assert grid == original
            assert gen.SEMANTIC_WITNESSES[name](grid)
            assert gen.WITNESS_RIVALS[name] == [name]


def test_palette_memorization_shortcut_fits_canonical_pairs_but_not_production_palettes():
    shortcut = RIVALS["canonical_palette_memorization"]
    for pair in canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]
    grid = gen.generate(314, 0, grid_h=6, grid_w=6,
                        placement_profile="right_clip", palette_id=0)
    assert gen.self_check(grid) == []
    assert shortcut(grid) != oracle_output(grid)
    assert gen.CANONICAL_SHORTCUTS["canonical_palette_memorization"](grid) == shortcut(grid)


def test_lesson_hook_rejects_a_surviving_rival_but_accepts_generated_windows():
    pairs = []
    for index in range(4):
        grid = gen.generate(91, index)
        pairs.append({"input": grid, "output": oracle_output(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []

    # A deliberately wrong demo label must be diagnosed rather than silently scored.
    bad = deepcopy(pairs[:3])
    bad[0]["output"] = RIVALS["single_cell_copies"](bad[0]["input"])
    assert any("output" in reason for reason in gen.lesson_identifiable(bad, pairs[3]))


@pytest.mark.parametrize("mutation", [
    "repeat_color", "extra_cell", "move_cell", "invisible_top", "bool_cell",
    "bad_color", "too_small", "too_large",
])
def test_validator_rejects_semantic_and_structural_mutations(mutation):
    grid = gen.generate(123, 9, grid_h=6, grid_w=6,
                        placement_profile="top_clip", palette_id=0)
    br, bc, _ = block(grid)
    if mutation == "repeat_color":
        grid[br][bc + 1] = grid[br][bc]
    elif mutation == "extra_cell":
        grid[-1][-1] = 9
    elif mutation == "move_cell":
        grid[br][bc] = 0
        grid[br][max(0, bc - 1)] = 1
    elif mutation == "invisible_top":
        # A top-row source would make both upper target stamps completely invisible.
        colors = [grid[br + dr][bc + dc] for dr in (0, 1) for dc in (0, 1)]
        grid = [[0] * 6 for _ in range(6)]
        grid[0][2], grid[0][3], grid[1][2], grid[1][3] = colors
    elif mutation == "bool_cell":
        grid[br][bc] = True
    elif mutation == "bad_color":
        grid[br][bc] = 10
    elif mutation == "too_small":
        grid = [row[:5] for row in grid[:5]]
    elif mutation == "too_large":
        grid = [row + [0] * 4 for row in grid] + [[0] * 10 for _ in range(4)]
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 6 for _ in range(6)]])
def test_malformed_grid_returns_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_retained_clipping_counterexample_is_lawful_and_refutes_complete_stamp_rival():
    grid = witness_input()
    assert gen.self_check(grid) == []
    assert oracle_output(grid) != RIVALS["complete_stamps_only"](grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(314,159,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "909"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env, text=True))
    assert outputs[0] == outputs[1]


def test_real_racket_authority_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    grids += [gen.generate(701, index, placement_profile=PROFILES[index % 4],
                           palette_id=index % len(PALETTES)) for index in range(32)]
    assert racket_outputs(grids) == [oracle_output(grid) for grid in grids]

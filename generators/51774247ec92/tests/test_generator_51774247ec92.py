"""Focused regressions for the commanded-extraction generator 51774247ec92."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "51774247ec92"
GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _as_grid(rows):
    if rows and isinstance(rows[0], str):
        return [[int(value) for value in row] for row in rows]
    return copy.deepcopy(rows)


def _canonical_pairs():
    for line in (ROOT / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        test = row["test"]
        pairs = row["train"] + (test if isinstance(test, list) else [test])
        return [(_as_grid(pair["input"]), _as_grid(pair["output"])) for pair in pairs]
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_and_all_canonical_pairs_are_accepted_and_exact():
    assert GEN.RULE_HASH == "c74447a07e12"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    component_counts = []
    for grid, expected in pairs:
        before = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.canonical_like(grid) is True
        assert GEN.rule_mirror(grid) == expected
        assert grid == before
        component_counts.append(len(GEN._analysis(grid)["components"]))
    # The held-out canonical motif includes an enclosed disconnected cell; a
    # one-component-only checker would reject a real task input.
    assert component_counts == [1, 1, 1, 1, 2]


def test_commented_task_source_preserves_semantic_sync_with_canonical():
    base = json.loads(
        (ROOT / "data" / "base" / "solutions" / "banks" / "868e1a8cbe17" / f"M124__{TASK_ID}.json").read_text()
    )
    canonical = next(
        json.loads(line)
        for line in (ROOT / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    target = base["racket_target"]["target_code"]
    raw = base["racket_target"]["raw_code"]
    assert raw == target
    assert "Ignore the command row" in target
    assert "including enclosed islands" in target

    def normalized_without_comments(source: str) -> str:
        source = re.sub(r";[^\n]*", "", source)
        return "".join(source.split())

    assert normalized_without_comments(target) == normalized_without_comments(
        canonical["program_solution"]
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable_in_every_band(band):
    cases = [
        dict(
            grid_h=8,
            grid_w=10,
            command=2,
            motif_profile="rect_2x3",
            motif_color_count=2,
            command_in_motif=False,
        ),
        dict(
            grid_h=13,
            grid_w=15,
            command=6,
            motif_profile="tall_4x3",
            motif_color_count=4,
            command_in_motif=True,
        ),
        dict(
            grid_h=9,
            grid_w=12,
            command=4,
            motif_profile="canonical_c",
            motif_color_count=3,
            command_in_motif=True,
        ),
    ]
    for requested in cases:
        grid = GEN.generate(2207, 91, difficulty=band, **requested)
        assert GEN.self_check(grid, difficulty=band) == []
        assert GEN.observe_overrides(grid) == requested


def test_unknown_and_removed_dead_axes_are_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override axis"):
        GEN.generate(1, 0, texture="warm")
    with pytest.raises(ValueError, match="unknown override axis"):
        GEN.generate(1, 0, __override_contract_unknown_axis__=3)


@pytest.mark.parametrize("start", range(10))
def test_five_consecutive_demonstrations_expose_every_command(start):
    pairs = []
    for sample_index in range(start, start + 6):
        grid = GEN.generate(811, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    demo_commands = {
        GEN.observe_overrides(pair["input"])["command"] for pair in pairs[:5]
    }
    assert demo_commands == {2, 3, 4, 5, 6}
    assert GEN.lesson_identifiable(pairs[:5], pairs[5]) == []


def test_command_colour_overlap_and_absence_are_both_real_axes():
    overlap = GEN.generate(
        33,
        4,
        command=5,
        motif_profile="canonical_a",
        motif_color_count=3,
        command_in_motif=True,
    )
    absent = GEN.generate(
        33,
        4,
        command=5,
        motif_profile="canonical_a",
        motif_color_count=3,
        command_in_motif=False,
    )
    assert GEN.observe_overrides(overlap)["command_in_motif"] is True
    assert GEN.observe_overrides(absent)["command_in_motif"] is False
    assert _freeze(overlap) != _freeze(absent)


def test_generated_motifs_make_all_five_transforms_distinct():
    for profile in GEN._PROFILE_NAMES:
        for color_count in (2, 3, 4):
            grid = GEN.generate(
                901,
                17,
                grid_h=13,
                grid_w=15,
                command=3,
                motif_profile=profile,
                motif_color_count=color_count,
                command_in_motif=True,
            )
            crop = GEN._analysis(grid)["crop"]
            outputs = {
                _freeze(GEN._apply_transform(crop, command))
                for command in GEN._COMMANDS
            }
            assert len(outputs) == 5


def test_every_semantic_witness_names_a_rival_it_actually_refutes():
    for sample_index in range(30):
        grid = GEN.generate(901, sample_index, difficulty="hard")
        expected = GEN.rule_mirror(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            rivals = GEN.WITNESS_RIVALS.get(witness_name)
            assert rivals, witness_name
            assert any(
                GEN.SEMANTIC_RIVALS[rival](grid) != expected
                for rival in rivals
            ), witness_name


def test_self_check_rejects_six_structural_impostors():
    base = GEN.generate(
        771,
        19,
        grid_h=10,
        grid_w=12,
        command=3,
        motif_profile="canonical_a",
        motif_color_count=3,
        command_in_motif=True,
    )
    assert GEN.self_check(base) == []
    analysis = GEN._analysis(base)

    no_command = copy.deepcopy(base)
    no_command[0] = [0] * len(no_command[0])

    two_commands = copy.deepcopy(base)
    extra_col = next(c for c, value in enumerate(two_commands[0]) if value == 0)
    two_commands[0][extra_col] = 4

    invalid_command = copy.deepcopy(base)
    command_col = analysis["command_col"]
    invalid_command[0][command_col] = 9

    no_motif = copy.deepcopy(base)
    for r in range(1, len(no_motif)):
        no_motif[r] = [0] * len(no_motif[r])

    external_component = copy.deepcopy(base)
    external_component[-1][-1] = 8

    one_colour = copy.deepcopy(base)
    for r, c in analysis["cells"]:
        one_colour[r][c] = 7

    for name, grid in {
        "no_command": no_command,
        "two_commands": two_commands,
        "invalid_command": invalid_command,
        "no_motif": no_motif,
        "external_component": external_component,
        "one_colour": one_colour,
    }.items():
        assert GEN.self_check(grid), name


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    grid = GEN.generate(
        555,
        8,
        grid_h=10,
        grid_w=12,
        command=4,
        motif_profile="rect_2x3",
        motif_color_count=3,
        command_in_motif=False,
    )
    grid[-1][-1] = next(
        color for color in range(1, 10) if color not in {value for row in grid for value in row}
    )
    assert GEN.self_check(grid)
    output = GEN.rule_mirror(grid)
    assert output
    assert all(isinstance(row, list) and row for row in output)


def test_replay_fresh_objects_and_process_global_rng_state():
    random.seed(20260726)
    state = random.getstate()
    first = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    pristine = copy.deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 8
    second = GEN.generate(97, 103, difficulty="hard")
    assert random.getstate() == state
    assert second == pristine
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

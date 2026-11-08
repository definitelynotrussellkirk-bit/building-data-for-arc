"""Focused regression tests for generator 5d6fcce80b6a."""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import random
import sys
import types
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_PORTABLE_ROOT = _HERE.parents[1]
if (_PORTABLE_ROOT / "data/canonical/puzzles.jsonl").is_file():
    ROOT = _PORTABLE_ROOT
    sys.path.insert(0, str(ROOT))
    from puzzle_generators.rule_wrap import wrap_rule

    GEN = importlib.import_module("puzzle_generators.per_puzzle.5d6fcce80b6a.generator")
else:
    REPO_ROOT = _HERE.parents[3]
    ROOT = REPO_ROOT / "shared"
    sys.path.insert(0, str(ROOT / "runtime"))
    sys.path.insert(0, str(ROOT / "tools"))
    scripts_package = types.ModuleType("scripts")
    scripts_package.__path__ = [str(ROOT / "tools")]
    sys.modules.setdefault("scripts", scripts_package)
    from puzzle_generators.rule_wrap import wrap_rule

    spec = importlib.util.spec_from_file_location(
        "generator_5d6fcce80b6a_review",
        REPO_ROOT / "generators/5d6fcce80b6a/generator.py",
    )
    assert spec is not None and spec.loader is not None
    GEN = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GEN)


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in grid
    )
    return f"'({rows})"


def rule_application(src: str, grid: list[list[int]]) -> str:
    return f"({wrap_rule(src)} {_grid_literal(grid)})"


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def _normalized_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def test_rule_hash_and_selected_authority_are_pinned() -> None:
    row = _canonical_row()
    base = json.loads(
        (ROOT / "data/base/solutions/training/fb791726__5d6fcce80b6a.json").read_text()
    )
    assert GEN.RULE_HASH == _normalized_hash(row["program_solution"]) == "652672c3e3c3"
    assert base["racket_target"]["target_code"] == row["program_solution"]
    assert base["racket_target"]["raw_code"] != row["program_solution"]


def test_canonical_pairs_are_accepted_and_match_python_mirror() -> None:
    row = _canonical_row()
    for pair in [*row["train"], *row["test"]]:
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_override_value_is_exactly_observable() -> None:
    for band in ("easy", "medium", "hard"):
        for profile in GEN.SCENE_PROFILES:
            for palette in GEN.PALETTE_PROFILES:
                grid = GEN.generate(
                    311,
                    17,
                    difficulty=band,
                    scene_profile=profile,
                    palette_profile=palette,
                )
                assert GEN.observe_overrides(grid) == {
                    "scene_profile": profile,
                    "palette_profile": palette,
                }
                assert GEN.self_check(grid, difficulty=band) == []


def test_unknown_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, misspelled_axis=True)


def test_self_check_rejects_targeted_impostors() -> None:
    impostors = {
        "all_zero": [[0, 0, 0] for _ in range(3)],
        "no_separator": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "reserved_three": [[1, 0, 0], [0, 0, 0], [3, 0, 1]],
        "only_one_content_row": [[0, 0, 0], [0, 0, 0], [1, 1, 0]],
        "ragged": [[1, 0, 0], [0, 0], [1, 0, 0]],
        "unclassified_geometry": [[1, 0, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0]],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_four_sample_schedule_identifies_every_sliding_lesson() -> None:
    for band in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(12):
            grid = GEN.generate(47, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for start in range(8):
            demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
            query = pairs[start + GEN.EXAMPLES_NEEDED]
            assert GEN.lesson_identifiable(demos, query) == []


def test_named_rivals_are_refuted_by_scheduled_witnesses() -> None:
    grids = [GEN.generate(91, i, difficulty="medium") for i in range(4)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witness_grids = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert witness_grids, witness_name
        for rival_name in rival_names:
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
                for grid in witness_grids
            ), (witness_name, rival_name)


def test_replay_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(123, 9, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(123, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == GEN.generate(123, 9, difficulty="hard")


def test_absent_color_recombination_is_rejected_but_racket_executes(
    protected_racket_bridge,
) -> None:
    grid = GEN.generate(808, 1, difficulty="medium", palette_profile="pair_12")
    recombined = copy.deepcopy(grid)
    source_cell = next(
        (r, c)
        for r, row in enumerate(recombined)
        for c, value in enumerate(row)
        if value in (1, 2)
    )
    assert all(value != 6 for row in recombined for value in row)
    recombined[source_cell[0]][source_cell[1]] = 6
    assert GEN.self_check(recombined), "teaching distribution must reject the absent-colour splice"

    canonical = _canonical_row()["program_solution"]
    output = protected_racket_bridge.eval_text(
        rule_application(canonical, recombined)
    )
    assert len(output) == 2 * len(recombined)
    assert len(output[0]) == 2 * len(recombined[0])
    assert output[source_cell[0]][source_cell[1]] == 6
    assert output[source_cell[0] + len(recombined)][source_cell[1] + len(recombined[0])] == 6


def _singleton_leading_control() -> list[list[int]]:
    grid = [
        [0, 0, 0, 0, 0],
        [4, 0, 0, 0, 0],
        [0, 4, 0, 0, 0],
        [0, 0, 4, 0, 0],
    ]
    assert GEN.self_check(grid, difficulty="easy") == []
    return grid


def test_non_singleton_witness_is_paired_with_copy_loss_rival() -> None:
    rival_name = "copy_only_leftmost_nonzero_per_row"
    assert GEN.WITNESS_RIVALS["non_singleton_content_is_preserved"] == [rival_name]
    rival = GEN.SEMANTIC_RIVALS[rival_name]

    singleton = _singleton_leading_control()
    assert rival(singleton) == GEN.rule_mirror(singleton)

    multi_cell = GEN.generate(
        91,
        0,
        difficulty="medium",
        scene_profile="internal_anchor",
        palette_profile="single_4",
    )
    assert GEN.SEMANTIC_WITNESSES["non_singleton_content_is_preserved"](multi_cell)
    assert rival(multi_cell) != GEN.rule_mirror(multi_cell)


def test_rectangular_witness_is_paired_with_square_assumption_rival() -> None:
    rival_name = "assume_square_output_width_from_height"
    assert GEN.WITNESS_RIVALS["rectangular_canvas_is_doubled"] == [rival_name]
    rival = GEN.SEMANTIC_RIVALS[rival_name]

    square = GEN.generate(
        17,
        0,
        difficulty="medium",
        scene_profile="internal_anchor",
        palette_profile="single_8",
    )
    rectangular = GEN.generate(
        17,
        1,
        difficulty="medium",
        scene_profile="leading_control",
        palette_profile="pair_12",
    )
    assert len(square) == len(square[0])
    assert len(rectangular) != len(rectangular[0])
    assert rival(square) == GEN.rule_mirror(square)
    assert rival(rectangular) != GEN.rule_mirror(rectangular)


def test_generic_rivals_have_honest_generic_witnesses() -> None:
    assert GEN.WITNESS_RIVALS["separator_rows_are_inserted"] == [
        "diagonal_tiling_without_green_rows"
    ]
    assert GEN.WITNESS_RIVALS["off_diagonal_quadrants_stay_blank"] == [
        "copy_input_to_all_four_quadrants"
    ]


def test_lesson_identifiable_reports_any_surviving_declared_competitor() -> None:
    pairs = []
    for sample_index in range(5):
        grid = GEN.generate(47, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})

    original = dict(GEN.LESSON_COMPETITORS)
    try:
        GEN.LESSON_COMPETITORS["intentional_oracle_duplicate"] = GEN.rule_mirror
        reasons = GEN.lesson_identifiable(pairs[:4], pairs[4])
    finally:
        GEN.LESSON_COMPETITORS.clear()
        GEN.LESSON_COMPETITORS.update(original)

    assert any("intentional_oracle_duplicate" in reason for reason in reasons)


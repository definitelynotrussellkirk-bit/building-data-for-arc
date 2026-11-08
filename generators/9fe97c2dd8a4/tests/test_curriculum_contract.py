from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "9fe97c2dd8a4"
HERE = Path(__file__).resolve()


def _load_generator():
    module_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        # In the selected source tree only shared/runtime is importable.  The
        # generator itself is intentionally loaded from its task directory.
        if exc.name not in {
            f"puzzle_generators.per_puzzle.{TASK_ID}",
            module_name,
        }:
            raise
        source = HERE.parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"selected_generator_{TASK_ID}", source
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


def _data_root() -> Path:
    for root in HERE.parents:
        for candidate in (root / "shared" / "data", root / "data"):
            if (candidate / "canonical" / "puzzles.jsonl").is_file():
                return candidate
    raise AssertionError("canonical data root not found")


def _canonical_row() -> dict:
    with (_data_root() / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


gen = _load_generator()


def test_training_demo_shortcut_is_real_and_held_out_test_falsifies_it():
    """The strongest task-local rival must be executable, not prose only."""
    row = _canonical_row()
    rival = gen.SEMANTIC_RIVALS["include_color_5_in_duplicate_census"]

    assert all(
        rival(pair["input"]) == pair["output"]
        for pair in row["train"]
    )
    held_out = row["test"][0]
    assert rival(held_out["input"]) != held_out["output"]
    assert gen.rule_mirror(held_out["input"]) == held_out["output"]


def test_every_four_demo_cyclic_window_refutes_color_5_census_shortcut():
    rival = gen.LESSON_COMPETITORS["include_color_5_in_duplicate_census"]
    assert tuple(gen.SCHEDULE_PROFILES) == tuple(range(5))

    for difficulty in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(5):
                demos = []
                for offset in range(gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, start + offset, difficulty=difficulty)
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_grid = gen.generate(
                    seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty
                )
                query = {
                    "input": query_grid,
                    "output": gen.rule_mirror(query_grid),
                }

                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (difficulty, seed, start)
                assert gen.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    seed,
                    start,
                )


def test_intentional_override_rejections_name_incompatible_axes():
    assert hasattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS")
    cases = [
        ({"grid_h": 4, "bar_count": 3}, {"grid_h", "bar_count"}),
        ({"grid_w": 3, "marker_col": 17}, {"grid_w", "marker_col"}),
        ({"bar_count": 1, "duplicate_mode": True}, {"bar_count", "duplicate_mode"}),
        ({"marker_col": 2, "duplicate_mode": True}, {"marker_col", "duplicate_mode"}),
    ]
    for overrides, expected_axes in cases:
        with pytest.raises(ValueError) as exc_info:
            gen.generate(1, 0, difficulty="easy", **overrides)
        assert set(exc_info.value.incompatible_axes) == expected_axes


def test_selected_authority_text_matches_canonical_program_exactly():
    row = _canonical_row()
    authority_path = (
        _data_root()
        / "base"
        / "solutions"
        / "training"
        / "e048c9ed__9fe97c2dd8a4.json"
    )
    authority = json.loads(authority_path.read_text())

    assert authority["racket_target"]["target_code"] == row["program_solution"]
    # The archival source is intentionally retained verbatim even though the
    # selected executable target is synchronized to canonical formatting.
    assert authority["racket_target"]["raw_code"] != ""


def test_workspace_probe_reads_live_declarations_and_reports_no_survivors():
    probe_path = HERE.parents[1] / "workspace" / "lesson_probe.py"
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_{TASK_ID}", probe_path
    )
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = probe
    spec.loader.exec_module(probe)

    report = probe.run_probe(lessons_per_band=5)
    assert report["declared_lesson_competitors"] == sorted(
        gen.LESSON_COMPETITORS
    )
    assert all(
        row["surviving_lessons"] == 0
        for row in report["bands"].values()
    )

def test_distribution_census_reaches_canonical_six_color_palette():
    """Mirror the blocking distribution gate's exact seed/sample census."""
    palette_sizes = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(1, 21):
            grid = gen.generate(seed, seed, difficulty=difficulty)
            palette_sizes.append(len({value for row in grid for value in row}))

    assert max(palette_sizes) >= 6


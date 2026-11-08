from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = ROOT / "generators" / "5666b68dd4b9" / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_5666b68dd4b9", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_task() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "5666b68dd4b9":
                return row
    raise AssertionError("canonical task 5666b68dd4b9 not found")


def _normalized_selected_cells(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    selector = grid[0][0]
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == selector and (r, c) != (0, 0)
    ]
    assert cells
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def test_canonical_examples_are_accepted_and_mirrored_exactly():
    generator = _load_generator()
    task = _canonical_task()

    assert generator.RULE_HASH == "5a2705a2ea24"
    for pair in [*task["train"], *task["test"]]:
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]


def test_four_example_schedule_decorrelates_selector_shape_and_transform_code():
    generator = _load_generator()
    grids = [generator.generate(271828, index, difficulty="hard") for index in range(4)]

    assert [grid[0][-1] for grid in grids] == [1, 2, 3, 4]
    assert len({grid[0][0] for grid in grids}) == 1
    assert len({_normalized_selected_cells(grid) for grid in grids}) == 1
    assert all(generator.self_check(grid) == [] for grid in grids)


def test_exact_axes_round_trip_and_unknown_overrides_are_rejected():
    generator = _load_generator()
    requested = {
        "transform_code": 4,
        "grid_profile": "11x13",
        "frame_profile": "7x4",
        "distractor_layout": "inside_frame",
    }

    grid = generator.generate(314159, 3, difficulty="medium", **requested)
    assert generator.observe_overrides(grid) == requested
    assert generator.self_check(grid, meta={"overrides": requested}) == []

    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(1, 0, not_a_real_axis="x")


def test_inside_frame_noise_is_present_in_input_but_cleared_by_rule():
    generator = _load_generator()
    grid = generator.generate(
        161803,
        2,
        transform_code=3,
        grid_profile="10x12",
        frame_profile="6x5",
        distractor_layout="inside_frame",
    )
    analysis = generator._analysis(grid)
    assert analysis["errors"] == []
    frame = analysis["frame"]
    interior_input = {
        grid[r][c]
        for r in range(frame["r0"] + 1, frame["r1"])
        for c in range(frame["c0"] + 1, frame["c1"])
    }
    output = generator.rule_mirror(grid)
    selector = grid[0][0]
    interior_output = {
        output[r][c]
        for r in range(frame["r0"] + 1, frame["r1"])
        for c in range(frame["c0"] + 1, frame["c1"])
    }

    assert any(value not in {0, 8, selector} for value in interior_input)
    assert interior_output <= {0, selector}


def test_declared_witnesses_have_real_rival_disagreements():
    generator = _load_generator()
    candidates = [generator.generate(seed, index, difficulty="hard") for seed in range(8) for index in range(4)]

    for witness_name, witness in generator.SEMANTIC_WITNESSES.items():
        witness_grids = [grid for grid in candidates if witness(grid)]
        assert witness_grids, f"no generated witness for {witness_name}"
        for rival_name in generator.WITNESS_RIVALS[witness_name]:
            rival = generator.SEMANTIC_RIVALS[rival_name]
            agreeing = [
                grid
                for grid in witness_grids
                if rival(grid) == generator.rule_mirror(grid)
            ]
            assert not agreeing, (
                f"{witness_name} fires on {len(agreeing)} grids that do not refute "
                f"{rival_name}"
            )


def test_four_demo_lesson_falsifies_all_declared_competitors():
    generator = _load_generator()
    grids = [generator.generate(424242, index, difficulty="hard") for index in range(5)]
    pairs = [{"input": grid, "output": generator.rule_mirror(grid)} for grid in grids]

    assert generator.EXAMPLES_NEEDED == 4
    assert generator.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_single_seed_stream_contains_at_least_five_distinct_pairs():
    generator = _load_generator()
    grids = [generator.generate(0, index) for index in range(25)]
    pair_fingerprints = {
        json.dumps({"input": grid, "output": generator.rule_mirror(grid)}, sort_keys=True)
        for grid in grids
    }
    assert len(pair_fingerprints) >= 5


def test_review_probe_builds_a_replayable_four_code_report():
    probe_path = GENERATOR_PATH.parent / "workspace" / "review_probe.py"
    spec = importlib.util.spec_from_file_location("review_probe_5666b68dd4b9", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(seed=0, start=0, difficulty="hard", use_racket=False)
    assert report["task_id"] == "5666b68dd4b9"
    assert report["lesson"]["codes"] == [1, 2, 3, 4]
    assert report["lesson"]["identifiable_errors"] == []
    assert report["shortcut_counterexample"]["shortcut_disagrees"] is True
    assert report["shortcut_counterexample"]["generator_emits"] is True

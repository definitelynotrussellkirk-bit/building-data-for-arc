"""Native parametric contract tests for selector-parity marker cropping."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"

CANONICAL = """(rule!
 ;; Crop to the bbox of the maroon(9) markers.
 (let ((bb (bbox-of-cells (find-color g 9)))) (subgrid g (first bb) (second bb) (third bb) (fourth bb))))"""


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    module_name = f"_test_9c3781759581_{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _crop(grid: list[list[int]], color: int) -> list[list[int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    assert cells, f"missing color {color}"
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_adapter_program_preserves_exact_canonical_and_has_distinct_alternate():
    adapter = _load("adapter")
    canonical = adapter.program({"crop_policy": "fixed_color_9"})
    alternate = adapter.program({"crop_policy": "selector_parity"})
    assert canonical == CANONICAL
    assert alternate.startswith("(rule!")
    assert alternate != canonical


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"crop_policy": "fixed_color_5"},
        {"crop_policy": 9},
        {"crop_policy": True},
        {"crop_policy": "fixed_color_9", "extra": 1},
        None,
    ],
)
def test_invalid_settings_are_rejected(settings):
    with pytest.raises((TypeError, ValueError), match="crop_policy|settings"):
        _load("adapter").program(settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 2, 4),
        (-1, 2, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 2, 0),
        (0, 2, 5),
        (0, True, 4),
        (0, 2, 4.0),
    ],
)
def test_invalid_generation_scalars_are_rejected(seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        _load("adapter").generate(
            seed, {"crop_policy": "fixed_color_9"}, demos=demos, queries=queries
        )


def test_generated_claims_match_independent_crop_for_both_settings():
    adapter = _load("adapter")
    for setting in ("fixed_color_9", "selector_parity"):
        episode = adapter.generate(37, {"crop_policy": setting}, demos=4, queries=4)
        assert len(episode["train"]) == 4
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program({"crop_policy": setting})
        assert len({repr(grid) for grid in _inputs(episode)}) == 8
        for pair in episode["train"] + episode["test"]:
            count = sum(cell == 2 for row in pair["input"] for cell in row)
            target = 9 if setting == "fixed_color_9" else (5 if count % 2 else 9)
            assert pair["output"] == _crop(pair["input"], target)
            assert _crop(pair["input"], 5) != _crop(pair["input"], 9)


def test_inputs_are_matched_across_settings_and_prefix_stable_across_counts():
    adapter = _load("adapter")
    canonical = adapter.generate(81, {"crop_policy": "fixed_color_9"}, 6, 4)
    alternate = adapter.generate(81, {"crop_policy": "selector_parity"}, 6, 4)
    assert _inputs(canonical) == _inputs(alternate)

    short = adapter.generate(81, {"crop_policy": "selector_parity"}, 2, 1)
    more_demos = adapter.generate(81, {"crop_policy": "selector_parity"}, 6, 1)
    more_queries = adapter.generate(81, {"crop_policy": "selector_parity"}, 2, 4)
    assert short["train"] == more_demos["train"][:2]
    assert short["test"] == more_queries["test"][:1]
    assert short["test"] == more_demos["test"]
    assert short["train"] == more_queries["train"]


def test_minimum_two_demos_refute_both_fixed_target_bypasses():
    adapter = _load("adapter")
    episode = adapter.generate(5, {"crop_policy": "selector_parity"}, 2, 4)
    counts = [sum(cell == 2 for row in pair["input"] for cell in row) for pair in episode["train"]]
    assert [count % 2 for count in counts] == [1, 0]
    assert [pair["output"] for pair in episode["train"]] == [
        _crop(episode["train"][0]["input"], 5),
        _crop(episode["train"][1]["input"], 9),
    ]
    assert any(pair["output"] != _crop(pair["input"], 5) for pair in episode["train"])
    assert any(pair["output"] != _crop(pair["input"], 9) for pair in episode["train"])


def test_fourth_query_is_substantive_30_by_30_boundary_stress():
    episode = _load("adapter").generate(
        9, {"crop_policy": "selector_parity"}, demos=2, queries=4
    )
    grid = episode["test"][3]["input"]
    assert len(grid) == 30 and len(grid[0]) == 30
    assert sum(cell != 0 for row in grid for cell in row) >= 90
    assert any(grid[0][c] != 0 for c in range(30))
    assert any(grid[-1][c] != 0 for c in range(30))
    assert any(grid[r][0] != 0 for r in range(30))
    assert any(grid[r][-1] != 0 for r in range(30))


def test_wrong_selector_intermediate_changes_the_final_crop():
    family = _load("family")
    episode = family.generate(123, {"crop_policy": "selector_parity"}, 2, 4)
    pair = episode["train"][0]
    facts = family.selector_intermediate(pair["input"])
    assert facts == {"selector_count": 1, "selector_parity": "odd", "target_color": 5}
    assert family.apply_wrong_intermediate(pair["input"]) == _crop(pair["input"], 9)
    assert family.apply_wrong_intermediate(pair["input"]) != pair["output"]
    assert family.counterfactual_program().startswith("(rule!")
    assert family.counterfactual_program() != family.program({"crop_policy": "selector_parity"})


def test_reproducible_lesson_audit_records_shortcuts_and_causal_ablation():
    audit = _load("audit_lessons")
    report = audit.build_report(seed=0, execute_racket=False)
    assert report["schema"] == "arcpuzzles-selector-parity-lesson-audit-v1"
    assert report["matched_inputs"] is True
    lesson = report["minimum_teaching_set"]
    assert lesson["selector_counts"] == [1, 2]
    assert lesson["selected_targets"] == [5, 9]
    assert lesson["fixed_color_5_mismatched_demos"] == 1
    assert lesson["fixed_color_9_mismatched_demos"] == 1
    assert lesson["all_alternate_labels_match_independent_crop"] is True
    assert report["public_projection"]["query_outputs_hidden"] is True
    assert report["public_projection"]["private_metadata_hidden"] is True
    causal = report["causal_case"]
    assert causal["intermediate_value"] == {
        "selector_count": 1,
        "selector_parity": "odd",
        "target_color": 5,
    }
    assert causal["counterfactual_changed"] is True
    assert report["large_query"]["shape"] == [30, 30]
    assert report["large_query"]["nonzero_cells"] >= 90
    assert report["large_query"]["touches_all_boundaries"] is True
    assert report["racket"] == {"executed": False}

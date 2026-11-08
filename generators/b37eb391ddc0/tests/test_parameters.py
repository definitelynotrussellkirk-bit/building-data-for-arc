from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK = "b37eb391ddc0"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def _load():
    path = HOME / "native_family.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK}_native_family_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_parametric_files_exist():
    expected = {
        "adapter.py",
        "native_family.py",
        "canonical.rkt",
        "promotion.json",
        "audit.py",
    }
    assert expected <= {path.name for path in HOME.iterdir() if path.is_file()}


def test_canonical_program_is_exact_and_settings_are_strict():
    family = _load()
    canonical = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    assert family.program({"completion_scope": "all_pairs"}) == canonical
    assert family.program({"completion_scope": "cue_selected_color"}) != canonical
    for bad in (
        {},
        {"completion_scope": "selected_pair"},
        {"completion_scope": 1},
        {"completion_scope": "all_pairs", "extra": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            family.program(bad)


def test_counts_are_prefix_stable_and_inputs_match_across_settings():
    family = _load()
    small = family.generate(17, {"completion_scope": "cue_selected_color"}, 2, 1)
    large = family.generate(17, {"completion_scope": "cue_selected_color"}, 6, 4)
    canonical = family.generate(17, {"completion_scope": "all_pairs"}, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert _inputs(large) == _inputs(canonical)
    frozen = {tuple(map(tuple, grid)) for grid in _inputs(large)}
    assert len(frozen) == 10


def test_every_scene_has_unique_cue_selection_and_global_selected_color_effect():
    family = _load()
    for seed in (0, 17, 31):
        selected = family.generate(seed, {"completion_scope": "cue_selected_color"}, 6, 4)
        canonical = family.generate(seed, {"completion_scope": "all_pairs"}, 6, 4)
        for selected_pair, canonical_pair in zip(
            selected["train"] + selected["test"],
            canonical["train"] + canonical["test"],
        ):
            summary = family.scene_summary(selected_pair["input"])
            assert summary["cue_count"] == 1
            assert summary["candidate_colors"] >= 3
            assert summary["nearest_unique"] is True
            assert summary["selected_color_pairs"] >= 2
            assert summary["nonselected_pairs"] >= 2
            assert selected_pair["output"] == family.reference(
                selected_pair["input"], {"completion_scope": "cue_selected_color"}
            )
            assert canonical_pair["output"] == family.reference(
                canonical_pair["input"], {"completion_scope": "all_pairs"}
            )
            assert selected_pair["output"] != canonical_pair["output"]


def test_max_query_is_distributed_30x30_and_wrong_selected_color_changes_output():
    family = _load()
    episode = family.generate(0, {"completion_scope": "cue_selected_color"}, 3, 4)
    pair = episode["test"][3]
    grid = pair["input"]
    summary = family.scene_summary(grid)
    assert [len(grid), len(grid[0])] == [30, 30]
    assert summary["matching_pairs"] >= 24
    assert summary["occupied_rows"] >= 24
    assert summary["occupied_cols"] >= 24
    wrong = family.reference_with_selector(grid, "farthest_pair_color")
    assert pair["output"] != wrong


def test_public_turn_masks_answers_and_future_queries_without_mutation():
    family = _load()
    episode = family.generate(9, {"completion_scope": "cue_selected_color"}, 3, 4)
    snapshot = deepcopy(episode)
    visible = family.public_turn(episode, 2)
    assert episode == snapshot
    assert set(visible) == {"train", "test"}
    assert visible["train"] == episode["train"]
    assert visible["test"] == [{"input": episode["test"][2]["input"]}]
    assert "program_solution" not in visible


def test_declared_rivals_are_refuted_by_minimum_two_demos():
    family = _load()
    for settings in family.SETTINGS:
        for seed in (0, 17, 31):
            episode = family.generate(seed, settings, 2, 4)
            assert family.teaching_survivors(episode["train"], settings) == (
                family.setting_name(settings),
            )

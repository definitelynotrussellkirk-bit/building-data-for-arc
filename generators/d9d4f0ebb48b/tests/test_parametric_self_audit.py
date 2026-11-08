"""Finite shortcut and public-projection checks for the proposed family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve()
AUDIT = HERE.parents[1] / "workspace" / "parametric" / "self_audit.py"


def _load():
    spec = importlib.util.spec_from_file_location("_test_d9d4_self_audit", AUDIT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _literal_input():
    return [
        [8, 8, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 4, 4, 4, 0],
        [0, 0, 0, 0, 0, 0, 4, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def test_shortcut_oracles_change_the_literal_selector_result():
    audit = _load()
    grid = _literal_input()
    correct = audit.rival_output(grid, "selector_source")
    assert audit.rival_output(grid, "local") != correct
    assert audit.rival_output(grid, "always_first") != correct
    assert audit.rival_output(grid, "marker_color") != correct
    assert audit.rival_output(grid, "reverse_selector") != correct
    assert audit.rival_output(grid, "off_by_one") != correct
    assert audit.wrong_program("always_first") != audit.prototype.program(
        {"fill_color_mode": "selector_source"}
    )


def test_two_visible_demos_eliminate_declared_settings_and_shortcuts():
    audit = _load()
    for mode in ("local", "selector_source"):
        report = audit.visible_audit(seed=2718, mode=mode, demos=2, queries=4)
        assert report["survivors"] == [mode]
        assert report["query_count"] == 4
        assert report["all_inputs_distinct"] is True
        assert all(not result["fits_all_demos"] for result in report["shortcuts"].values())


def test_public_projection_excludes_private_rule_and_query_answers():
    audit = _load()
    report = audit.public_projection(seed=99, mode="selector_source", demos=3, queries=4)
    public = json.loads(report["public_bytes"])
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert report["private_metadata_invariant"] is True
    assert report["first_turn_matches_single_query"] is True
    assert report["future_queries_absent_from_first_turn"] is True

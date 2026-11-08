"""Replay the minimal review counterexamples retained with the task."""
from __future__ import annotations

import json

import pytest
from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    "19158f03ecb2", root=ROOT
)
CASES = json.loads(
    (ROOT / "generators/19158f03ecb2/counterexamples/review-a1e69e9fdec20d2f.json")
    .read_text(encoding="utf-8")
)["cases"]
BY_ID = {case["id"]: case for case in CASES}


def _call(case):
    call = case["call"]
    return GEN.generate(
        call["seed"],
        call["sample_index"],
        difficulty=call["difficulty"],
        **call["overrides"],
    )


def test_override_counterexamples_replay():
    feasible = BY_ID["partial-symmetric-palette-needs-unpinned-width"]
    observed = GEN.observe_overrides(_call(feasible))
    expected = feasible["expected_observation"]
    assert observed["grid_h"] == expected["grid_h"]
    assert observed["palette_size"] == expected["palette_size"]
    assert observed["lr_asymmetric"] is expected["lr_asymmetric"]
    assert expected["grid_w_min"] <= observed["grid_w"] <= expected["grid_w_max"]

    impossible = BY_ID["impossible-exact-symmetric-palette"]
    with pytest.raises(ValueError) as captured:
        _call(impossible)
    assert set(impossible["expected_incompatible_axes"]) <= set(
        captured.value.incompatible_axes
    )


def test_width_gated_shortcut_counterexample_replays():
    case = BY_ID["width-gated-canonical-shortcut"]
    grid = _call(case)
    assert grid == case["input"]
    intended = [row + list(reversed(row)) for row in grid]
    rival = [row + row for row in grid]
    assert intended == case["intended_output"]
    assert rival == case["rival_output"]
    assert intended != rival

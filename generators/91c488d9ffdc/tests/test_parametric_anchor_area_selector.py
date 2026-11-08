from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("rect_parametric", HERE / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def test_default_program_is_exact_canonical_authority():
    assert p.rule_text("all_rectangles") == p.CANONICAL_PROGRAM
    assert hashlib.sha256(p.CANONICAL_PROGRAM.encode()).hexdigest() == p.CANONICAL_SHA256


def test_episode_counts_prefix_stability_and_matched_inputs():
    for demos in range(2, 7):
        for queries in range(1, 5):
            canonical = p.generate_episode(17, outline_mode="all_rectangles", demos=demos, queries=queries)
            alternate = p.generate_episode(17, outline_mode="anchor_area_select", demos=demos, queries=queries)
            maximum = p.generate_episode(17, outline_mode="anchor_area_select", demos=6, queries=4)
            assert [x["input"] for x in canonical["train"] + canonical["test"]] == [x["input"] for x in alternate["train"] + alternate["test"]]
            assert alternate["train"] == maximum["train"][:demos]
            assert alternate["test"] == maximum["test"][:queries]
            visible = canonical["train"] + canonical["test"]
            assert len({json.dumps(x["input"], sort_keys=True) for x in visible}) == len(visible)


def test_two_demos_identify_each_setting_and_queries_disagree():
    for seed in (0, 17, 101):
        episodes = {mode: p.generate_episode(seed, outline_mode=mode, demos=2, queries=4) for mode in p.MODES}
        for selected, episode in episodes.items():
            rival = next(mode for mode in p.MODES if mode != selected)
            assert any(p.apply_mode(pair["input"], rival) != pair["output"] for pair in episode["train"])
            assert all(p.apply_mode(pair["input"], rival) != pair["output"] for pair in episode["test"])


def test_alternate_uses_anchor_area_to_choose_candidate_rectangle():
    episode = p.generate_episode(0, outline_mode="anchor_area_select", demos=3, queries=4)
    branches = set()
    for pair in episode["train"] + episode["test"]:
        info = p.analyze(pair["input"])
        branches.add(info["target_index"])
        target = info["candidates"][info["target_index"]]
        expected = p.border_cells(target["bbox"])
        actual = {(r, c) for r, row in enumerate(pair["output"]) for c, value in enumerate(row) if value}
        assert actual == expected
        assert {pair["output"][r][c] for r, c in actual} == {target["color"]}
    assert {0, 1, 2} <= branches


def test_query_four_is_substantive_30x30_boundary_stress():
    pair = p.generate_episode(5, outline_mode="anchor_area_select", demos=3, queries=4)["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    info = p.analyze(grid)
    assert len(info["rectangles"]) >= 5
    points = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert {0, 29} <= {r for r, _ in points}
    assert {0, 29} <= {c for _, c in points}


def test_public_projection_is_one_query_and_private_free():
    episode = p.generate_episode(3, outline_mode="anchor_area_select", demos=3, queries=4)
    view = p.public_turn(episode, 1)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}
    raw = p.public_bytes(episode, 1)
    assert p.public_id(episode, 1) == hashlib.sha256(raw).hexdigest()
    text = raw.decode()
    for forbidden in ("outline_mode", "program_solution", "settings", "seed"):
        assert forbidden not in text
    assert text.count('"output"') == len(episode["train"])


def test_causal_case_changes_under_off_by_one_area():
    case = p.causal_case(0)
    assert case["settings"] == {"outline_mode": "anchor_area_select"}
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
    assert case["intermediate_value"]["correct_target_index"] != case["intermediate_value"]["wrong_target_index"]


@pytest.mark.parametrize("settings", [None, {}, {"outline_mode": "bad"}, {"outline_mode": True}, {"outline_mode": "all_rectangles", "x": 1}])
def test_invalid_settings_rejected(settings):
    with pytest.raises(ValueError):
        p.validate_settings(settings)


@pytest.mark.parametrize("demos,queries", [(1, 1), (7, 1), (2, 0), (2, 5), (True, 1), (2, True)])
def test_invalid_counts_rejected(demos, queries):
    with pytest.raises(ValueError):
        p.generate_episode(0, outline_mode="all_rectangles", demos=demos, queries=queries)

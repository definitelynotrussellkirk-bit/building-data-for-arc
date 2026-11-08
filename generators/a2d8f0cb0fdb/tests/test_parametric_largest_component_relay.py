from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("a2d_parametric", HERE / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def test_default_program_is_exact_canonical_authority():
    assert p.rule_text("first_header_all") == p.CANONICAL_PROGRAM
    assert hashlib.sha256(p.CANONICAL_PROGRAM.encode()).hexdigest() == p.CANONICAL_SHA256


def test_episode_counts_prefix_stability_and_matched_inputs():
    for demos in range(2, 7):
        for queries in range(1, 5):
            canonical = p.generate_episode(17, selection_mode="first_header_all", demos=demos, queries=queries)
            alternate = p.generate_episode(17, selection_mode="largest_component_indexed_header", demos=demos, queries=queries)
            maximum = p.generate_episode(17, selection_mode="largest_component_indexed_header", demos=6, queries=4)
            assert len(canonical["train"]) == demos
            assert len(canonical["test"]) == queries
            assert [x["input"] for x in canonical["train"] + canonical["test"]] == [x["input"] for x in alternate["train"] + alternate["test"]]
            assert alternate["train"] == maximum["train"][:demos]
            assert alternate["test"] == maximum["test"][:queries]
            visible = canonical["train"] + canonical["test"]
            assert len({json.dumps(x["input"], sort_keys=True) for x in visible}) == len(visible)


def test_two_demos_identify_each_setting_and_all_queries_disagree():
    for seed in (0, 17, 101):
        episodes = {mode: p.generate_episode(seed, selection_mode=mode, demos=2, queries=4) for mode in p.MODES}
        for selected, episode in episodes.items():
            rival = next(mode for mode in p.MODES if mode != selected)
            assert any(p.apply_mode(pair["input"], rival) != pair["output"] for pair in episode["train"])
            assert all(p.apply_mode(pair["input"], rival) != pair["output"] for pair in episode["test"])


def test_alternate_uses_largest_component_size_to_select_header_color():
    episode = p.generate_episode(0, selection_mode="largest_component_indexed_header", demos=3, queries=4)
    branches = set()
    for pair in episode["train"] + episode["test"]:
        info = p.analyze(pair["input"])
        branches.add(info["selected_header_index"])
        nonzero = {(r, c) for r, row in enumerate(pair["output"]) for c, value in enumerate(row) if value}
        assert nonzero == set(info["largest_cells"])
        assert {pair["output"][r][c] for r, c in nonzero} == {info["selected_header_color"]}
    assert branches == {0, 1, 2}


def test_query_four_is_substantive_30x30_boundary_stress():
    pair = p.generate_episode(5, selection_mode="largest_component_indexed_header", demos=3, queries=4)["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert len(nonzero) >= 55
    assert {0, 29} <= {r for r, _ in nonzero}
    assert {0, 29} <= {c for _, c in nonzero}


def test_public_projection_is_one_query_and_private_free():
    episode = p.generate_episode(3, selection_mode="largest_component_indexed_header", demos=3, queries=4)
    view = p.public_turn(episode, 2)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}
    raw = p.public_bytes(episode, 2)
    assert p.public_id(episode, 2) == hashlib.sha256(raw).hexdigest()
    text = raw.decode()
    for forbidden in ("selection_mode", "program_solution", "settings", "seed", '"output"'):
        if forbidden == '"output"':
            assert text.count(forbidden) == len(episode["train"])
        else:
            assert forbidden not in text


def test_causal_case_changes_under_wrong_intermediate():
    case = p.causal_case(0)
    assert case["settings"] == {"selection_mode": "largest_component_indexed_header"}
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
    assert case["intermediate_value"]["largest_size"] != case["intermediate_value"]["smallest_size"]


@pytest.mark.parametrize("settings", [None, {}, {"selection_mode": "bad"}, {"selection_mode": True}, {"selection_mode": "first_header_all", "x": 1}])
def test_invalid_settings_rejected(settings):
    with pytest.raises(ValueError):
        p.validate_settings(settings)


@pytest.mark.parametrize("demos,queries", [(1, 1), (7, 1), (2, 0), (2, 5), (True, 1), (2, True)])
def test_invalid_counts_rejected(demos, queries):
    with pytest.raises(ValueError):
        p.generate_episode(0, selection_mode="first_header_all", demos=demos, queries=queries)

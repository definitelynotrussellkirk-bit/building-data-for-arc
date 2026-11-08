"""Native parametric contract tests for 092360ee834f."""
from __future__ import annotations

import copy
from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "092360ee834f"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def prototype():
    return _load(HOME / "prototype.py", "_parametric_092360ee834f")


@cache
def adapter():
    return _load(HOME / "adapter.py", "_adapter_092360ee834f")


def _canonical_record():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(TASK_ID)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_last_changes_original_tie():
    p = prototype()
    canonical = _canonical_record()
    assert p.program({"match_order": "first"}) == canonical["program_solution"]
    assert p.program({"match_order": "last"}) != canonical["program_solution"]
    tied = canonical["train"][0]
    assert p.transform(tied["input"], {"match_order": "first"}) == tied["output"]
    assert p.transform(tied["input"], {"match_order": "last"}) != tied["output"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_supported_demo_counts_identify_setting_with_matched_four_query_inputs(demos):
    p = prototype()
    first = p.generate(31 + demos, {"match_order": "first"}, demos=demos, queries=4)
    last = p.generate(31 + demos, {"match_order": "last"}, demos=demos, queries=4)
    assert _inputs(first) == _inputs(last)
    assert len(first["train"]) == len(last["train"]) == demos
    assert len(first["test"]) == len(last["test"]) == 4
    assert first["certificate"]["survivors"] == [{"match_order": "first"}]
    assert last["certificate"]["survivors"] == [{"match_order": "last"}]
    assert len({p.digest(grid) for grid in _inputs(first)}) == demos + 4
    assert all(a["output"] != b["output"] for a, b in zip(first["train"], last["train"]))


def test_query_schedule_has_crossed_geometry_and_substantive_30x30_stress():
    p = prototype()
    episode = p.generate(47, {"match_order": "first"}, demos=2, queries=4)
    profiles = [p.analyze_scene(pair["input"]) for pair in episode["test"]]
    assert [(row["grid_h"], row["grid_w"]) for row in profiles] == [
        (12, 14),
        (18, 20),
        (24, 27),
        (30, 30),
    ]
    assert {row["first_match_side"] for row in profiles} == {"left", "right"}
    assert {row["last_match_side"] for row in profiles} == {"left", "right"}
    assert len({row["target_size"] for row in profiles}) >= 3
    stress = profiles[-1]
    assert stress["matching_green_count"] >= 3
    assert stress["green_component_count"] >= 8
    assert stress["body_nonzero_count"] >= 70
    assert stress["body_bbox_height"] >= 26
    assert stress["body_bbox_width"] >= 26
    assert stress["diagonal_trap_count"] >= 1


def test_query_prefix_is_independent_of_demo_and_requested_query_counts():
    p = prototype()
    short = p.generate(53, {"match_order": "first"}, demos=2, queries=1)
    long = p.generate(53, {"match_order": "first"}, demos=6, queries=8)
    assert short["test"] == long["test"][:1]
    assert public_challenge_id(short) == public_challenge_id(
        {"train": short["train"], "test": long["test"][:1]}
    )


def test_real_racket_labels_both_settings_including_30x30():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=60, max_calls_before_restart=256) as bridge:
        for order in ("first", "last"):
            episode = p.generate(61, {"match_order": order}, demos=2, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert p.execute_rule(
                    episode["program_solution"], pair["input"], bridge=bridge
                ) == pair["output"]
            cert = p.certify(
                episode,
                execute=lambda source, grid: p.execute_rule(source, grid, bridge=bridge),
            )
            assert cert["survivors"] == [{"match_order": order}]


def test_public_projection_hides_settings_program_and_all_query_answers():
    p = prototype()
    episode = p.generate(71, {"match_order": "first"}, demos=3, queries=4)
    before = public_challenge_bytes(episode)
    assert p.public_challenge(episode) == json.loads(before)
    assert p.public_id(episode) == public_challenge_id(episode)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"match_order": "last"}
    changed["program_solution"] = "private mutation"
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == before
    assert public_challenge_id(changed) == public_challenge_id(episode)
    visible = copy.deepcopy(episode)
    visible["train"][0]["output"] = [[9]]
    assert public_challenge_id(visible) != public_challenge_id(episode)


def test_invalid_contracts_duplicate_inputs_and_corrupt_labels_fail_closed():
    p = prototype()
    for kwargs in (
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 0},
        {"demos": True, "queries": 4},
    ):
        with pytest.raises(ValueError):
            p.generate(0, {"match_order": "first"}, **kwargs)
    with pytest.raises(ValueError):
        p.generate(0, {"match_order": "middle"}, demos=3, queries=4)
    with pytest.raises(ValueError):
        p.transform([[0.0]], {"match_order": "first"})

    corrupt = p.generate(0, {"match_order": "first"}, demos=2, queries=4)
    corrupt["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError, match="label"):
        p.certify(corrupt)

    duplicate = p.generate(1, {"match_order": "first"}, demos=2, queries=4)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    with pytest.raises(ValueError, match="distinct"):
        p.certify(duplicate)


def test_promotion_adapter_matches_prototype_contract():
    p, a = prototype(), adapter()
    for order in ("first", "last"):
        settings = {"match_order": order}
        assert a.program(settings) == p.program(settings)
        episode = a.generate(79, settings, 2, 4)
        assert set(episode) == {"train", "test", "program_solution"}
        assert episode["program_solution"] == p.program(settings)
        assert len(episode["train"]) == 2 and len(episode["test"]) == 4

@pytest.mark.parametrize("split,count", [("demo", 6), ("query", 8)])
def test_target_override_domain_constructs_every_profile(split, count):
    """Break caught: accepted target_size values must not fail by profile geometry."""
    p = prototype()
    for index in range(count):
        for target in range(2, 9):
            grid = p.sample_input(211, split, index, target_size=target)
            facts = p.analyze_scene(grid)
            assert facts["target_size"] == target
            assert facts["matching_green_count"] >= 2

def test_minimum_lessons_reject_color_blind_component_selection():
    """Break caught: a same-area non-green sentinel must stay a distinct object."""
    p = prototype()
    for seed in range(8):
        for order in ("first", "last"):
            episode = p.generate(seed, {"match_order": order}, demos=2, queries=4)
            wrong_predictions = []
            for pair in episode["train"]:
                grid = pair["input"]
                target = sum(value == 1 for value in grid[0])
                matches = [
                    cells
                    for cells in p._components(grid, color=None, connectivity=4)
                    if len(cells) == target
                ]
                chosen = matches[0] if order == "first" else matches[-1]
                wrong = [[0] * len(grid[0]) for _ in grid]
                for r, c in chosen:
                    wrong[r][c] = 8
                wrong_predictions.append(wrong)
            assert any(
                predicted != pair["output"]
                for predicted, pair in zip(wrong_predictions, episode["train"])
            )

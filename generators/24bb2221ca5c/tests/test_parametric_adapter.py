from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
TASK_HOME = REPO / "generators/24bb2221ca5c"
PARAMETRIC = TASK_HOME / "workspace/parametric"
SOLUTION = (
    REPO
    / "shared/data/base/solutions/banks/01130745873d/"
    "medium_145_fill_holes_in_ring_components__24bb2221ca5c.json"
)


def _load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "native parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("review_24bb_parametric_adapter", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    return json.loads(SOLUTION.read_text(encoding="utf-8"))["racket_target"]["target_code"]


def test_contract_materializes_exact_default_and_three_distinct_programs():
    adapter = _load_adapter()
    programs = {
        name: adapter.program({"fill_policy": name})
        for name in ("all", "largest_hole_area", "most_holes")
    }
    assert programs["all"] == _canonical_program()
    assert all(isinstance(source, str) and source.strip() for source in programs.values())
    assert len(set(programs.values())) == 3
    assert callable(adapter.generate)


def test_contract_rejects_missing_extra_mistyped_and_unknown_settings():
    adapter = _load_adapter()
    bad_settings = (
        {},
        {"fill_policy": "all", "extra": 1},
        {"fill_policy": 1},
        {"fill_policy": True},
        {"fill_policy": "largest_bbox_area"},
    )
    for settings in bad_settings:
        with pytest.raises(ValueError, match="fill_policy"):
            adapter.program(settings)


def test_promotion_contract_declares_bounded_counts_and_exact_resource():
    path = PARAMETRIC / "promotion.json"
    assert path.is_file(), "promotion contract has not been implemented"
    contract = json.loads(path.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/24bb2221ca5c/workspace/parametric/adapter.py",
        "parameters": {
            "fill_policy": ["all", "largest_hole_area", "most_holes"]
        },
        "default": {"fill_policy": "all"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/24bb2221ca5c/workspace/parametric/canonical.rkt"
        ],
    }


POLICIES = ("all", "largest_hole_area", "most_holes")


def _load_prototype():
    path = PARAMETRIC / "prototype.py"
    assert path.is_file(), "constructive episode grammar has not been implemented"
    spec = importlib.util.spec_from_file_location("review_24bb_parametric_prototype", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _episode_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _frozen_grid(grid):
    return tuple(tuple(row) for row in grid)


def _public_bytes(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_episode_streams_are_count_independent_and_setting_neutral():
    adapter = _load_adapter()
    small = adapter.generate(17, {"fill_policy": "all"}, 2, 1)
    full = adapter.generate(17, {"fill_policy": "all"}, 6, 4)

    assert [pair["input"] for pair in small["train"]] == [
        pair["input"] for pair in full["train"][:2]
    ]
    assert [pair["input"] for pair in small["test"]] == [
        pair["input"] for pair in full["test"][:1]
    ]

    full_inputs = _episode_inputs(full)
    assert len({_frozen_grid(grid) for grid in full_inputs}) == 10
    for policy in POLICIES[1:]:
        other = adapter.generate(17, {"fill_policy": policy}, 6, 4)
        assert _episode_inputs(other) == full_inputs


def test_generation_rejects_non_plain_or_out_of_range_seed_and_counts():
    adapter = _load_adapter()
    setting = {"fill_policy": "all"}
    bad_calls = (
        (True, setting, 3, 4),
        (1.0, setting, 3, 4),
        (-1, setting, 3, 4),
        (2**63, setting, 3, 4),
        (0, setting, True, 4),
        (0, setting, 2.0, 4),
        (0, setting, 1, 4),
        (0, setting, 7, 4),
        (0, setting, 3, True),
        (0, setting, 3, 1.0),
        (0, setting, 3, 0),
        (0, setting, 3, 5),
    )
    for seed, settings, demos, queries in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(seed, settings, demos, queries)


def test_two_demo_prefixes_give_three_distinct_rule_signatures():
    adapter = _load_adapter()
    signatures = {}
    for policy in POLICIES:
        episode = adapter.generate(0, {"fill_policy": policy}, 2, 4)
        signatures[policy] = tuple(
            _frozen_grid(pair["output"]) for pair in episode["train"]
        )
        assert episode["program_solution"] == adapter.program({"fill_policy": policy})
    assert len(set(signatures.values())) == len(POLICIES)


def test_constructed_topology_separates_area_hole_count_and_bbox_rivals():
    prototype = _load_prototype()
    episode = prototype.generate(17, {"fill_policy": "all"}, 3, 4)
    profiles = prototype.component_profiles(episode["train"][0]["input"])
    closed = [profile for profile in profiles if profile["hole_count"]]

    assert len(closed) >= 3
    area_winner = max(closed, key=lambda profile: profile["hole_area"])
    count_winner = max(closed, key=lambda profile: profile["hole_count"])
    bbox_winner = max(closed, key=lambda profile: profile["bbox_area"])
    assert area_winner["hole_area"] > sorted(
        (profile["hole_area"] for profile in closed), reverse=True
    )[1]
    assert count_winner["hole_count"] > sorted(
        (profile["hole_count"] for profile in closed), reverse=True
    )[1]
    assert len({
        area_winner["component_index"],
        count_winner["component_index"],
        bbox_winner["component_index"],
    }) == 3

    assert any(profile["corner_gap"] and profile["hole_count"] for profile in profiles)
    assert any(profile["side_gap"] and not profile["hole_count"] for profile in profiles)
    assert any(
        profile["hole_count"] and not all(profile["rectangular_holes"])
        for pair in episode["train"] + episode["test"]
        for profile in prototype.component_profiles(pair["input"])
    )
    assert any(profile["touches_canvas_border"] for profile in profiles)
    closed_colors = [profile["color"] for profile in closed]
    assert len(closed_colors) != len(set(closed_colors))


def test_fourth_query_is_a_substantive_30_by_30_border_stress():
    adapter = _load_adapter()
    episode = adapter.generate(17, {"fill_policy": "all"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = sum(value != 0 for row in grid for value in row)
    assert nonzero >= 180
    assert any(grid[0]) and any(grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    quadrants = (
        [row[:15] for row in grid[:15]],
        [row[15:] for row in grid[:15]],
        [row[:15] for row in grid[15:]],
        [row[15:] for row in grid[15:]],
    )
    assert all(any(value for row in quadrant for value in row) for quadrant in quadrants)


def test_public_turn_masks_query_answers_private_rule_and_future_queries():
    adapter = _load_adapter()
    prototype = _load_prototype()
    full = adapter.generate(17, {"fill_policy": "most_holes"}, 3, 4)
    stopped = adapter.generate(17, {"fill_policy": "most_holes"}, 3, 1)

    first = prototype.public_turn(full, 0)
    assert first == {
        "train": full["train"],
        "test": [{"input": full["test"][0]["input"]}],
    }
    assert _public_bytes(first) == _public_bytes(prototype.public_turn(stopped, 0))
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert first["test"] == [{"input": full["test"][0]["input"]}]
    assert "fill_policy" not in _public_bytes(first).decode("utf-8")
    assert "program_solution" not in _public_bytes(first).decode("utf-8")

    second = prototype.public_turn(full, 1)
    assert second["test"] == [{"input": full["test"][1]["input"]}]
    for invalid in (True, 1.0, -1, 4):
        with pytest.raises(ValueError, match="query_index"):
            prototype.public_turn(full, invalid)


def test_two_demo_component_order_refutes_first_closed_selector():
    prototype = _load_prototype()
    episode = prototype.generate(17, {"fill_policy": "all"}, 2, 1)
    first_closed = []
    area_winners = []
    count_winners = []
    for pair in episode["train"]:
        closed = [
            profile
            for profile in prototype.component_profiles(pair["input"])
            if profile["hole_count"]
        ]
        first_closed.append(min(closed, key=lambda profile: profile["component_index"])["component_index"])
        area_winners.append(max(closed, key=lambda profile: profile["hole_area"])["component_index"])
        count_winners.append(max(closed, key=lambda profile: profile["hole_count"])["component_index"])
    assert first_closed[0] == count_winners[0]
    assert first_closed[1] == area_winners[1]
    assert first_closed[0] != area_winners[0]
    assert first_closed[1] != count_winners[1]


def _load_audit():
    path = PARAMETRIC / "audit.py"
    assert path.is_file(), "protected-Racket audit has not been implemented"
    spec = importlib.util.spec_from_file_location("review_24bb_parametric_audit", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protected_racket_audit_builds_finite_scan_and_causal_case(tmp_path):
    adapter = _load_adapter()
    audit = _load_audit()
    output = tmp_path / "audit"
    binding = {"test_binding": "task3"}
    report = audit.build_evidence(
        output,
        seeds=(0,),
        demos=2,
        queries=1,
        source_binding=binding,
    )

    assert report["status"] == "passed"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["episodes"] == 3
    assert report["label_count"] == 9
    assert report["failures"] == []
    assert report["rival_programs"] >= 4
    assert report["demo_only_certificates"] == 3
    assert report["surviving_rivals"] == []
    assert report["public_projection"]["first_turn_count_invariant"] is True
    assert report["public_projection"]["private_fields_absent"] is True

    witness_path = output / "sequential-dependency.json"
    witness = json.loads(witness_path.read_text(encoding="utf-8"))
    assert witness["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
    assert witness["source_binding"] == binding
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert 1 <= len(witness["cases"]) <= 16
    case = witness["cases"][0]
    assert case["settings"] == {"fill_policy": "largest_hole_area"}
    assert case["program"] == adapter.program(case["settings"])
    assert case["ablation"] == "wrong_intermediate"
    assert case["output"] != case["counterfactual_output"]
    assert case["intermediate_value"]["largest_hole_area_component"] != case[
        "intermediate_value"
    ]["largest_bbox_component"]

    assert (output / "summary.json").is_file()
    assert (output / "episodes.private.json").is_file()
    assert (output / "rules" / "largest_bbox_area.rkt").is_file()

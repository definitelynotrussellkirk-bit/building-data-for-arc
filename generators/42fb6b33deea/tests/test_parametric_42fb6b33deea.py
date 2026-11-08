"""Focused native-parametric checks for 42fb6b33deea."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "42fb6b33deea"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
MODES = ("all_exact_four", "selector_area_gate")


def _load(name: str, path: Path):
    assert path.is_file(), f"missing required source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_42fb6b33deea_prototype", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_42fb6b33deea_adapter", ADAPTER_PATH)


def test_contract_declares_exact_bounded_family():
    assert json.loads(PROMOTION_PATH.read_text(encoding="utf-8")) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"fill_policy": list(MODES)},
        "default": {"fill_policy": "all_exact_four"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/selector_area_gate.rkt",
        ],
    }


def test_default_program_is_byte_exact_and_alternate_names_real_dependency(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.program_for("all_exact_four") == canonical
    assert adapter.program({"fill_policy": "all_exact_four"}) == canonical
    alternate = prototype.program_for("selector_area_gate")
    assert alternate == adapter.program({"fill_policy": "selector_area_gate"})
    assert alternate != canonical
    assert "selector-color" in alternate
    assert "selector-area" in alternate
    assert ">= (bbox-area cells) selector-area" in alternate


def test_episode_inputs_are_matched_distinct_deterministic_and_prefix_stable(prototype, adapter):
    episodes = {
        mode: adapter.generate(17, {"fill_policy": mode}, 3, 4)
        for mode in MODES
    }
    left = [pair["input"] for split in ("train", "test") for pair in episodes[MODES[0]][split]]
    right = [pair["input"] for split in ("train", "test") for pair in episodes[MODES[1]][split]]
    assert left == right
    assert episodes[MODES[0]] == adapter.generate(17, {"fill_policy": MODES[0]}, 3, 4)
    assert len({_freeze(grid) for grid in left}) == 7

    maximum = adapter.generate(17, {"fill_policy": MODES[0]}, 6, 4)
    minimum = adapter.generate(17, {"fill_policy": MODES[0]}, 2, 1)
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"] == maximum["test"][:1]
    assert prototype.public_view(minimum, 0) == prototype.public_view(
        adapter.generate(17, {"fill_policy": MODES[0]}, 2, 4), 0
    )


def test_every_scene_contains_selector_and_threshold_branches(prototype):
    episode = prototype.generate_episode(23, "all_exact_four", demos=6, queries=4)
    for pair in episode["train"] + episode["test"]:
        analysis = prototype.analyze_input(pair["input"])
        assert analysis["errors"] == []
        assert len(analysis["selector_cells"]) == 3
        areas = sorted(target["area"] for target in analysis["targets"])
        assert areas[0] < analysis["selector_area"]
        assert analysis["selector_area"] in areas
        assert areas[-1] > analysis["selector_area"]
        assert any(not target["literal_corners"] for target in analysis["targets"])


def test_two_demos_identify_each_setting_and_reject_declared_rivals(prototype):
    for seed in (0, 17, 91):
        inputs = prototype.episode_inputs(seed, demos=2, queries=4)
        for chosen in MODES:
            labels = [prototype.solve(grid, chosen) for grid in inputs["train"]]
            survivors = [
                name
                for name in prototype.CANDIDATE_POLICIES
                if all(
                    prototype.solve_candidate(grid, name) == expected
                    for grid, expected in zip(inputs["train"], labels)
                )
            ]
            assert survivors == [chosen]


def test_setting_outputs_differ_and_python_labels_follow_selected_policy(prototype):
    episodes = {
        mode: prototype.generate_episode(29, mode, demos=6, queries=4)
        for mode in MODES
    }
    for split in ("train", "test"):
        for left, right in zip(episodes[MODES[0]][split], episodes[MODES[1]][split]):
            assert left["input"] == right["input"]
            assert left["output"] != right["output"]
            assert left["output"] == prototype.solve(left["input"], MODES[0])
            assert right["output"] == prototype.solve(right["input"], MODES[1])


def test_fourth_query_is_substantive_exact_30x30(prototype):
    episode = prototype.generate_episode(41, "selector_area_gate", demos=3, queries=4)
    pair = episode["test"][3]
    grid, output = pair["input"], pair["output"]
    assert len(grid) == 30 and len(grid[0]) == 30
    assert sum(cell != 0 for row in grid for cell in row) >= 24
    assert sum(cell != 0 for row in output for cell in row) >= 110
    other = prototype.solve(grid, "all_exact_four")
    assert sum(a != b for ra, rb in zip(output, other) for a, b in zip(ra, rb)) >= 20


def test_validation_rejects_coercible_or_out_of_range_controls(prototype, adapter):
    for bad in (None, True, 0, "all"):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(bad)
    for bad_settings in (
        None,
        {},
        {"fill_policy": "all_exact_four", "extra": 1},
        {"fill_policy": "missing"},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad_settings)
    for bad_seed in (True, -1, 2**63, 1.0, "17"):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(bad_seed, MODES[0], demos=2, queries=4)
    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, MODES[0], demos=bad_demos, queries=4)
    for bad_queries in (False, 0, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, MODES[0], demos=2, queries=bad_queries)


def test_protected_racket_matches_python_on_small_and_30x30_cases(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = prototype.generate_episode(53, "selector_area_gate", demos=2, queries=4)
    selected = [episode["train"][0], episode["test"][3]]
    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        wrapped = wrap_rule(prototype.program_for("selector_area_gate"))
        for pair in selected:
            literal = "'(" + " ".join(
                "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
            ) + ")"
            assert bridge.eval_text(f"({wrapped} {literal})") == pair["output"]


def test_declared_racket_candidates_match_python_and_leave_one_survivor(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    inputs = prototype.episode_inputs(7, demos=2, queries=1)["train"]
    with RacketBridge(timeout=30, max_calls_before_restart=64) as bridge:
        wrapped = {
            name: wrap_rule(prototype.candidate_program(name))
            for name in prototype.CANDIDATE_POLICIES
        }
        racket_outputs = {}
        for name in prototype.CANDIDATE_POLICIES:
            racket_outputs[name] = []
            for grid in inputs:
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in grid
                ) + ")"
                output = bridge.eval_text(f"({wrapped[name]} {literal})")
                assert output == prototype.solve_candidate(grid, name)
                racket_outputs[name].append(output)
        for chosen in MODES:
            expected = [prototype.solve(grid, chosen) for grid in inputs]
            assert [
                name
                for name, outputs in racket_outputs.items()
                if outputs == expected
            ] == [chosen]


def test_reusable_audit_covers_count_boundaries_without_racket():
    audit = _load(
        "parametric_42fb6b33deea_audit",
        PARAMETRIC / "audit.py",
    )
    report = audit.build_audit(
        seeds=(0,),
        demo_counts=(2, 6),
        query_counts=(1, 4),
        execute_racket=False,
    )
    assert report["status"] == "passed"
    assert report["totals"] == {
        "seeds": 1,
        "requests": 4,
        "episodes": 8,
        "labeled_pairs": 52,
        "matched_input_requests": 4,
        "stress_30x30_episodes": 4,
        "racket_evaluations": 0,
    }
    assert report["finite_rival_survivors"] == {
        "0": {
            "all_exact_four": ["all_exact_four"],
            "selector_area_gate": ["selector_area_gate"],
        }
    }
    assert report["failures"] == []

"""Native parametric-family tests for 63784d19dd2d."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "63784d19dd2d"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
MODES = ("transform_only", "mark_b_overlap")


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
    return _load("parametric_63784d19dd2d_prototype", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_63784d19dd2d_adapter", ADAPTER_PATH)


def test_contract_declares_exact_bounded_family():
    assert json.loads(PROMOTION_PATH.read_text(encoding="utf-8")) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"overlap_mode": list(MODES)},
        "default": {"overlap_mode": "transform_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/mark_b_overlap.rkt",
        ],
    }


def test_default_program_is_byte_exact_and_alternate_names_dependency(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.program_for("transform_only") == canonical
    assert adapter.program({"overlap_mode": "transform_only"}) == canonical
    alternate = prototype.program_for("mark_b_overlap")
    assert alternate == adapter.program({"overlap_mode": "mark_b_overlap"})
    assert alternate != canonical
    assert "transformed-c" in alternate
    assert "overlap-with-b?" in alternate
    assert "MARK-COLOR" in alternate


def test_episode_inputs_are_matched_distinct_deterministic_and_prefix_stable(prototype, adapter):
    episodes = {
        mode: adapter.generate(17, {"overlap_mode": mode}, 3, 4)
        for mode in MODES
    }
    left = [pair["input"] for split in ("train", "test") for pair in episodes[MODES[0]][split]]
    right = [pair["input"] for split in ("train", "test") for pair in episodes[MODES[1]][split]]
    assert left == right
    assert episodes[MODES[0]] == adapter.generate(17, {"overlap_mode": MODES[0]}, 3, 4)
    assert len({_freeze(grid) for grid in left}) == 7

    maximum = adapter.generate(17, {"overlap_mode": MODES[0]}, 6, 4)
    minimum = adapter.generate(17, {"overlap_mode": MODES[0]}, 2, 1)
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"] == maximum["test"][:1]
    assert prototype.public_view(minimum, 0) == prototype.public_view(
        adapter.generate(17, {"overlap_mode": MODES[0]}, 2, 4), 0
    )


def test_every_scene_has_unique_transform_and_partial_b_overlap(prototype):
    episode = prototype.generate_episode(23, "mark_b_overlap", demos=6, queries=4)
    sizes = []
    for pair in episode["train"] + episode["test"]:
        analysis = prototype.analyze_input(pair["input"])
        assert analysis["errors"] == []
        assert analysis["transform_matches"] == [analysis["transform"]]
        assert analysis["transform"] in (2, 3, 4, 5)
        assert 0 < analysis["b_overlap_count"] < analysis["transformed_c_size"]
        assert analysis["transformed_c_support"] != analysis["c_support"]
        assert 2 not in {cell for row in pair["input"] for cell in row}
        sizes.append(analysis["panel_n"])
    assert min(sizes) >= 3 and max(sizes) == 9


def test_two_demos_identify_each_setting_and_reject_declared_rivals(prototype):
    for seed in (0, 17, 91):
        inputs = prototype.episode_inputs(seed, demos=2, queries=4)
        for chosen in MODES:
            labels = [prototype.solve(grid, chosen) for grid in inputs["train"]]
            survivors = [
                name
                for name in prototype.CANDIDATE_RULES
                if all(
                    prototype.solve_candidate(grid, name) == expected
                    for grid, expected in zip(inputs["train"], labels)
                )
            ]
            assert survivors == [chosen]


def test_setting_outputs_differ_and_python_labels_follow_selected_rule(prototype):
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
            assert any(2 in row for row in right["output"])


def test_fourth_query_is_substantive_maximum_width_scene(prototype):
    episode = prototype.generate_episode(41, "mark_b_overlap", demos=3, queries=4)
    pair = episode["test"][3]
    grid, output = pair["input"], pair["output"]
    assert len(grid) == 9 and len(grid[0]) == 29
    assert sum(cell != 0 for row in grid for cell in row) >= 35
    assert sum(cell != 0 for row in output for cell in row) >= 8
    assert any(grid[r][0] != 0 or grid[r][-1] != 0 for r in range(len(grid)))
    other = prototype.solve(grid, "transform_only")
    assert sum(a != b for ra, rb in zip(output, other) for a, b in zip(ra, rb)) >= 2


def test_public_projection_masks_private_fields_and_hashes_visible_bytes_only(prototype):
    episode = prototype.generate_episode(31, "mark_b_overlap", demos=3, queries=4)
    public = prototype.public_view(episode, 2)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    assert "program_solution" not in public
    first = prototype.public_view(episode, 0)
    same_first = prototype.public_view(
        prototype.generate_episode(31, "mark_b_overlap", demos=3, queries=1), 0
    )
    assert first == same_first
    assert prototype.public_bytes(first) == public_challenge_bytes(first)
    assert prototype.public_id(first) == public_challenge_id(first)
    assert prototype.public_id(first) == prototype.public_id(same_first)


def test_validation_rejects_coercible_or_out_of_range_controls(prototype, adapter):
    for bad in (None, True, 0, "all"):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(bad)
    for bad_settings in (
        None,
        {},
        {"overlap_mode": "transform_only", "extra": 1},
        {"overlap_mode": "missing"},
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


def test_protected_racket_matches_python_on_small_and_maximum_cases(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = prototype.generate_episode(53, "mark_b_overlap", demos=2, queries=4)
    selected = [episode["train"][0], episode["test"][3]]
    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        wrapped = wrap_rule(prototype.program_for("mark_b_overlap"))
        for pair in selected:
            literal = "'(" + " ".join(
                "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
            ) + ")"
            assert bridge.eval_text(f"({wrapped} {literal})") == pair["output"]


def test_declared_racket_candidates_match_python_and_leave_one_survivor(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    inputs = prototype.episode_inputs(7, demos=2, queries=1)["train"]
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        wrapped = {
            name: wrap_rule(prototype.candidate_program(name))
            for name in prototype.CANDIDATE_RULES
        }
        racket_outputs = {}
        for name in prototype.CANDIDATE_RULES:
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
            survivors = [name for name, outputs in racket_outputs.items() if outputs == expected]
            assert survivors == [chosen]


def test_reusable_audit_reports_matched_prefix_stable_family():
    audit = _load(
        "parametric_63784d19dd2d_audit",
        PARAMETRIC / "audit.py",
    )
    report = audit.build_audit(
        seeds=(0,),
        demo_counts=(2, 6),
        query_counts=(1, 4),
        execute_racket=False,
    )
    assert report["status"] == "passed"
    assert report["failures"] == []
    assert report["totals"]["requests"] == 4
    assert report["totals"]["matched_input_requests"] == 4
    assert report["totals"]["maximum_width_episodes"] == 4
    assert report["finite_rival_survivors"]["0"] == {
        "mark_b_overlap": ["mark_b_overlap"],
        "transform_only": ["transform_only"],
    }

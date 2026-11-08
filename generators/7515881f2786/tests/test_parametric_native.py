"""Native parametric-family tests for 7515881f2786."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "7515881f2786"
ROOT = find_root(__file__)
HOME = ROOT / f"generators/{TASK_ID}"
PARAMETRIC = HOME / "workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
SETTINGS = ("both", "horizontal", "vertical")


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
    return _load("parametric_7515881f2786_prototype_native", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_7515881f2786_adapter", ADAPTER_PATH)


def test_contract_declares_exact_bounded_family():
    assert json.loads(PROMOTION_PATH.read_text(encoding="utf-8")) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"bridge_axes": list(SETTINGS)},
        "default": {"bridge_axes": "both"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/horizontal.rkt",
            f"generators/{TASK_ID}/workspace/parametric/vertical.rkt",
        ],
    }


def test_default_program_is_byte_exact_and_axis_programs_are_distinct(prototype, adapter):
    canonical = _canonical_program()
    assert prototype.program_for("both") == canonical
    assert adapter.program({"bridge_axes": "both"}) == canonical
    programs = {setting: prototype.program_for(setting) for setting in SETTINGS}
    assert len(set(programs.values())) == 3
    assert programs["horizontal"] == adapter.program({"bridge_axes": "horizontal"})
    assert programs["vertical"] == adapter.program({"bridge_axes": "vertical"})


def test_episode_inputs_are_matched_distinct_deterministic_and_prefix_stable(prototype, adapter):
    episodes = {mode: adapter.generate(17, {"bridge_axes": mode}, 3, 4) for mode in SETTINGS}
    inputs = [
        [pair["input"] for split in ("train", "test") for pair in episodes[mode][split]]
        for mode in SETTINGS
    ]
    assert inputs[1:] == inputs[:-1]
    assert episodes["both"] == adapter.generate(17, {"bridge_axes": "both"}, 3, 4)
    assert len({_freeze(grid) for grid in inputs[0]}) == 7

    maximum = adapter.generate(17, {"bridge_axes": "both"}, 6, 4)
    minimum = adapter.generate(17, {"bridge_axes": "both"}, 2, 1)
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"] == maximum["test"][:1]
    assert prototype.public_view(minimum, 0) == prototype.public_view(
        adapter.generate(17, {"bridge_axes": "both"}, 2, 4), 0
    )


def test_two_demos_identify_each_setting_and_declared_rivals(prototype):
    for seed in (0, 17, 91):
        inputs = prototype.episode_inputs(seed, demos=2, queries=4)["train"]
        analyses = [prototype.analyze_input(grid) for grid in inputs]
        assert all(a["horizontal_segments"] and a["vertical_segments"] for a in analyses)
        assert any(a["horizontal_chain_lines"] for a in analyses)
        assert any(a["vertical_chain_lines"] for a in analyses)
        for chosen in SETTINGS:
            labels = [prototype.solve(grid, chosen) for grid in inputs]
            survivors = [
                name
                for name in prototype.CANDIDATE_RULES
                if all(
                    prototype.solve_candidate(grid, name) == expected
                    for grid, expected in zip(inputs, labels)
                )
            ]
            assert survivors == [chosen]


def test_setting_outputs_differ_and_python_labels_follow_selected_rule(prototype):
    episodes = {mode: prototype.generate_episode(29, mode, demos=6, queries=4) for mode in SETTINGS}
    for split in ("train", "test"):
        for triplet in zip(*(episodes[mode][split] for mode in SETTINGS)):
            assert len({_freeze(pair["input"]) for pair in triplet}) == 1
            assert len({_freeze(pair["output"]) for pair in triplet}) == 3
            for mode, pair in zip(SETTINGS, triplet):
                assert pair["output"] == prototype.solve(pair["input"], mode)


def test_fourth_query_is_substantive_exact_30x30_with_boundary_contact(prototype):
    episode = prototype.generate_episode(41, "both", demos=3, queries=4)
    pair = episode["test"][3]
    grid, output = pair["input"], pair["output"]
    assert len(grid) == 30 and len(grid[0]) == 30
    anchors = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    assert 6 <= len(anchors) <= 10
    assert any(r in (0, 29) or c in (0, 29) for r, c in anchors)
    assert sum(cell == 8 for row in output for cell in row) >= 80
    assert output != prototype.solve(grid, "horizontal")
    assert output != prototype.solve(grid, "vertical")


def test_public_projection_masks_private_fields_and_hashes_visible_bytes_only(prototype):
    episode = prototype.generate_episode(31, "vertical", demos=3, queries=4)
    public = prototype.public_view(episode, 2)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    serialized = json.dumps(public, sort_keys=True)
    for token in ("bridge_axes", "horizontal", "vertical", "program_solution", "seed"):
        assert token not in serialized
    first = prototype.public_view(episode, 0)
    same_first = prototype.public_view(
        prototype.generate_episode(31, "vertical", demos=3, queries=1), 0
    )
    assert first == same_first
    assert prototype.public_bytes(first) == public_challenge_bytes(first)
    assert prototype.public_id(first) == public_challenge_id(first)


def test_validation_rejects_coercible_or_out_of_range_controls(prototype, adapter):
    for bad in (None, True, 0, "diagonal"):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(bad)
    for bad_settings in (
        None,
        {},
        {"bridge_axes": "both", "extra": 1},
        {"bridge_axes": "missing"},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad_settings)
    for bad_seed in (True, -1, 2**63, 1.0, "17"):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(bad_seed, SETTINGS[0], demos=2, queries=4)
    for bad_demos in (True, 1, 7, 2.0, "2"):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, SETTINGS[0], demos=bad_demos, queries=4)
    for bad_queries in (False, 0, 5, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(0, SETTINGS[0], demos=2, queries=bad_queries)


def test_protected_racket_matches_python_on_small_and_30x30_cases(prototype):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = prototype.generate_episode(53, "both", demos=2, queries=4)
    selected = [episode["train"][0], episode["test"][3]]
    with RacketBridge(timeout=30, max_calls_before_restart=16) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        wrapped = wrap_rule(prototype.program_for("both"))
        for pair in selected:
            literal = "'(" + " ".join(
                "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
            ) + ")"
            assert bridge.eval_text(f"({wrapped} {literal})") == pair["output"]


def test_reusable_audit_covers_count_boundaries_without_racket():
    audit = _load("parametric_7515881f2786_audit", PARAMETRIC / "audit.py")
    report = audit.build_audit(
        seeds=(0,), demo_counts=(2, 6), query_counts=(1, 4), execute_racket=False
    )
    assert report["status"] == "passed"
    assert report["totals"] == {
        "seeds": 1,
        "requests": 4,
        "episodes": 12,
        "labeled_pairs": 78,
        "matched_input_requests": 4,
        "stress_30x30_episodes": 6,
        "racket_evaluations": 0,
    }
    assert report["failures"] == []

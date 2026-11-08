"""Focused tests for the native nesting-depth scope family."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "df74e338b4f5"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SCOPES = ("all_markers", "rarest_positive_depth")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("nesting_depth_scope_prototype_tests", HOME / "prototype.py")
ADAPTER = _load("nesting_depth_scope_adapter_tests", HOME / "adapter.py")


def _canonical_program() -> str:
    rows = [
        json.loads(line)
        for line in (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl")
        .read_text()
        .splitlines()
    ]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == TASK_ID and row.get("program_solution")
    }
    assert len(programs) == 1
    return next(iter(programs))


def _pairs(episode):
    return episode["train"] + episode["test"]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def _survivors(demos):
    return [
        scope
        for scope in SCOPES
        if all(
            PROTOTYPE.apply_scope(pair["input"], scope) == pair["output"]
            for pair in demos
        )
    ]


def test_promotion_contract_and_exact_canonical_default() -> None:
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"recolor_scope": list(SCOPES)},
        "default": {"recolor_scope": "all_markers"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/rarest_positive_depth.rkt",
        ],
    }
    assert tuple(PROTOTYPE.SCOPES) == SCOPES
    assert ADAPTER.program({"recolor_scope": "all_markers"}) == _canonical_program()
    assert PROTOTYPE.rule_text("all_markers") == _canonical_program()


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_inputs_are_matched_across_settings_and_every_label_changes(seed: int) -> None:
    episodes = {
        scope: ADAPTER.generate(seed, {"recolor_scope": scope}, demos=3, queries=4)
        for scope in SCOPES
    }
    baseline = _inputs(episodes["all_markers"])
    assert len({json.dumps(grid) for grid in baseline}) == 7
    for scope, episode in episodes.items():
        assert _inputs(episode) == baseline
        assert episode["program_solution"] == ADAPTER.program({"recolor_scope": scope})
        assert all(
            pair["output"] == PROTOTYPE.apply_scope(pair["input"], scope)
            for pair in _pairs(episode)
        )
    for index in range(len(baseline)):
        outputs = {
            json.dumps(_pairs(episodes[scope])[index]["output"]) for scope in SCOPES
        }
        assert len(outputs) == 2


@pytest.mark.parametrize("seed", [0, 17, 91])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
@pytest.mark.parametrize("scope", SCOPES)
def test_two_to_six_demonstrations_identify_the_setting(seed, demos, scope) -> None:
    episode = ADAPTER.generate(seed, {"recolor_scope": scope}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert _survivors(episode["train"]) == [scope]
    assert len({json.dumps(grid) for grid in _inputs(episode)}) == demos + 4


@pytest.mark.parametrize("scope", SCOPES)
def test_one_query_is_the_same_first_turn_as_four_queries(scope: str) -> None:
    settings = {"recolor_scope": scope}
    one = ADAPTER.generate(431, settings, demos=3, queries=1)
    four = ADAPTER.generate(431, settings, demos=3, queries=4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert PROTOTYPE.public_projection(one) == {
        "train": one["train"],
        "test": [{"input": one["test"][0]["input"]}],
    }


def test_teaching_profiles_expose_unique_and_tied_rarest_depths() -> None:
    episode = ADAPTER.generate(
        20261024, {"recolor_scope": "rarest_positive_depth"}, demos=3, queries=4
    )
    analyses = [PROTOTYPE.analyze(pair["input"]) for pair in episode["train"]]
    assert [analysis["positive_depth_counts"] for analysis in analyses] == [
        {1: 4, 2: 3},
        {1: 1, 2: 1, 3: 3},
        {1: 1, 2: 3, 3: 2},
    ]
    assert [analysis["selected_positive_depth"] for analysis in analyses] == [2, 2, 1]


def test_four_query_curriculum_has_aspect_boundary_and_substantive_30x30_stress() -> None:
    episode = ADAPTER.generate(
        20261024, {"recolor_scope": "rarest_positive_depth"}, demos=3, queries=4
    )
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(14, 18), (18, 14), (23, 27), (30, 30)]
    final = episode["test"][-1]["input"]
    analysis = PROTOTYPE.analyze(final)
    assert analysis["frame_count"] == 4
    assert analysis["positive_depth_counts"] == {1: 4, 2: 1, 3: 3, 4: 2}
    assert analysis["selected_positive_depth"] == 2
    assert len(analysis["markers"]) >= 14
    assert sum(value == 9 for row in final for value in row) >= 250
    occupied_rows = {row for row, _ in analysis["markers"]}
    occupied_cols = {col for _, col in analysis["markers"]}
    assert len(occupied_rows) >= 8 and len(occupied_cols) >= 8


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_visible_lessons_refute_axis_only_and_scope_shortcuts(seed: int) -> None:
    for scope in SCOPES:
        episode = ADAPTER.generate(seed, {"recolor_scope": scope}, demos=2, queries=4)
        rivals = PROTOTYPE.audit_rivals(scope)
        assert set(rivals) == {
            "row_span_only",
            "column_span_only",
            "constant_one",
            "inside_any_frame",
            "deepest_positive_only",
            "shallowest_rarest_tie",
            "most_frequent_positive_depth",
            "rarest_including_depth_zero",
        }
        for name, rival in rivals.items():
            assert any(
                rival(pair["input"]) != pair["output"] for pair in episode["train"]
            ), (seed, scope, name, "train")
            assert any(
                rival(pair["input"]) != pair["output"] for pair in episode["test"]
            ), (seed, scope, name, "test")


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"recolor_scope": "unknown"},
        {"recolor_scope": True},
        {"recolor_scope": "all_markers", "extra": 1},
    ],
)
def test_invalid_settings_reject(settings) -> None:
    with pytest.raises(ValueError):
        ADAPTER.program(settings)
    with pytest.raises(ValueError):
        ADAPTER.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 3, 4),
        (-1, 3, 4),
        (0, True, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 3, True),
        (0, 3, 0),
        (0, 3, 5),
    ],
)
def test_invalid_seed_and_count_controls_reject(seed, demos, queries) -> None:
    with pytest.raises(ValueError):
        ADAPTER.generate(
            seed, {"recolor_scope": "all_markers"}, demos=demos, queries=queries
        )


def test_public_identifier_depends_only_on_visible_projection() -> None:
    episode = PROTOTYPE.generate_episode(
        77, recolor_scope="rarest_positive_depth", demos=3, queries=4
    )
    public = PROTOTYPE.public_projection(episode)
    identifier = PROTOTYPE.public_challenge_id(episode)
    altered = json.loads(json.dumps(episode))
    altered["settings"] = {"recolor_scope": "all_markers"}
    altered["private_note"] = "changed"
    for pair in altered["test"]:
        pair["output"] = [[9]]
    assert PROTOTYPE.public_projection(altered) == public
    assert PROTOTYPE.public_challenge_id(altered) == identifier


def test_reusable_audit_report_covers_counts_rivals_and_worker_jobs(tmp_path) -> None:
    audit = _load("nesting_depth_scope_audit_tests", HOME / "audit.py")
    report = audit.build_report(seeds=(0, 17), demo_counts=(2, 6), queries=4)
    assert report["schema"] == "nesting-depth-scope-authoring-audit-v1"
    assert report["summary"] == {
        "jobs": 8,
        "episodes": 8,
        "pairs": 64,
        "distinct_inputs": 64,
        "tested_rivals": 8,
        "surviving_visible_demo_rivals": 0,
        "rivals_without_query_disagreement": 0,
    }
    assert {job["setting_survivors"] for job in report["jobs"]} == {
        "all_markers",
        "rarest_positive_depth",
    }
    assert all(not job["visible_demo_survivors"] for job in report["jobs"])
    request = audit.worker_request(
        ROOT, seeds=(0, 17), demo_counts=(2, 6), queries=4
    )
    assert request["root"] == str(ROOT.resolve())
    assert request["task_id"] == TASK_ID
    assert len(request["jobs"]) == 8
    assert request["jobs"][0] == {
        "seed": 0,
        "settings": {"recolor_scope": "all_markers"},
        "demos": 2,
        "queries": 4,
    }

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "17b0b2791dd2"
HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"
POLICIES = ("exact_vertical3", "nearest_horizontal3")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _modules():
    return (
        _load(PARAM / "prototype.py", "_p17b0_prototype"),
        _load(PARAM / "adapter.py", "_p17b0_adapter"),
        _load(PARAM / "rivals.py", "_p17b0_rivals"),
    )


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_native_files_and_contract_are_complete():
    for name in (
        "adapter.py",
        "prototype.py",
        "rivals.py",
        "audit.py",
        "canonical.rkt",
        "promotion.json",
        "README.md",
    ):
        assert (PARAM / name).is_file(), name
    promotion = json.loads((PARAM / "promotion.json").read_text())
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"target_policy": list(POLICIES)},
        "default": {"target_policy": "exact_vertical3"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
        ],
    }


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    prototype, adapter, _rivals = _modules()
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    default = {"target_policy": "exact_vertical3"}
    alternate = {"target_policy": "nearest_horizontal3"}
    assert prototype.program(default) == canonical
    assert adapter.program(default) == canonical
    assert prototype.program(alternate) == adapter.program(alternate)
    assert prototype.program(alternate) != canonical
    assert prototype.program(alternate).startswith("(rule!")


def test_python_default_matches_all_canonical_pairs():
    prototype, _adapter, _rivals = _modules()
    settings = {"target_policy": "exact_vertical3"}
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert prototype.solve(pair["input"], settings) == pair["output"]


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_independent_counts_are_exact_distinct_and_literal(demos, queries):
    prototype, adapter, _rivals = _modules()
    for policy in POLICIES:
        settings = {"target_policy": policy}
        episode = adapter.generate(23, settings, demos=demos, queries=queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["settings"] == settings
        assert episode["program_solution"] == prototype.program(settings)
        inputs = _inputs(episode)
        assert len({_grid_key(grid) for grid in inputs}) == len(inputs)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.solve(pair["input"], settings)
            assert 1 <= len(pair["input"]) <= 30
            assert 1 <= len(pair["input"][0]) <= 30
            assert all(type(v) is int and 0 <= v <= 9 for row in pair["input"] for v in row)


def test_inputs_are_matched_deterministic_and_prefix_stable():
    prototype, _adapter, _rivals = _modules()
    settings0 = {"target_policy": POLICIES[0]}
    settings1 = {"target_policy": POLICIES[1]}
    small0 = prototype.generate(17, settings0, demos=2, queries=1)
    large0 = prototype.generate(17, settings0, demos=6, queries=4)
    large1 = prototype.generate(17, settings1, demos=6, queries=4)
    assert small0 == prototype.generate(17, settings0, demos=2, queries=1)
    assert _inputs(large0) == _inputs(large1)
    assert [p["input"] for p in small0["train"]] == [p["input"] for p in large0["train"][:2]]
    assert [p["input"] for p in small0["test"]] == [p["input"] for p in large0["test"][:1]]
    for left, right in zip(large0["train"] + large0["test"], large1["train"] + large1["test"], strict=True):
        assert left["input"] == right["input"]
        assert left["output"] != right["output"]


def test_two_demos_teach_policy_and_refute_finite_harmful_rivals():
    prototype, _adapter, rivals = _modules()
    assert len(rivals.NAMES) >= 8
    for seed in (0, 1, 17, 31):
        episodes = {
            policy: prototype.generate(seed, {"target_policy": policy}, demos=2, queries=4)
            for policy in POLICIES
        }
        for policy, episode in episodes.items():
            other = POLICIES[1 - POLICIES.index(policy)]
            assert any(
                prototype.solve(pair["input"], {"target_policy": other}) != pair["output"]
                for pair in episode["train"]
            )
            for name in rivals.NAMES:
                assert any(
                    rivals.output(prototype, pair["input"], name) != pair["output"]
                    for pair in episode["train"]
                ), (seed, policy, name)


def test_queries_cover_relational_geometry_boundaries_and_substantive_30x30():
    prototype, _adapter, _rivals = _modules()
    episode = prototype.generate(
        5, {"target_policy": "nearest_horizontal3"}, demos=3, queries=4
    )
    sizes = {(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]}
    assert (30, 30) in sizes
    selected_patterns = set()
    for pair in episode["test"]:
        facts = prototype.observables(pair["input"])
        assert facts["selector_count"] >= 2
        assert facts["candidate_count"] > facts["selected_candidate_count"] >= 2
        assert facts["all_nearest_unique"] is True
        selected_patterns.add(tuple(facts["selected_candidate_indices"]))
    assert len(selected_patterns) >= 3
    stress = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
    nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 60
    assert any(r in (0, 29) or c in (0, 29) for r, c in nonzero)


def test_sequential_public_projection_hides_private_state_and_future_queries():
    prototype, _adapter, _rivals = _modules()
    episode = prototype.generate(
        9, {"target_policy": "nearest_horizontal3"}, demos=3, queries=4
    )
    ids = []
    for query_index in range(4):
        public = prototype.public_challenge(episode, query_index)
        assert set(public) == {"train", "test"}
        assert public["train"] == episode["train"]
        assert public["test"] == [{"input": episode["test"][query_index]["input"]}]
        serialized = json.dumps(public, sort_keys=True)
        assert "target_policy" not in serialized
        assert "program_solution" not in serialized
        assert _grid_key(episode["test"][query_index]["output"]) not in serialized
        for future in episode["test"][:query_index] + episode["test"][query_index + 1 :]:
            assert _grid_key(future["input"]) not in serialized
        expected_bytes = public_challenge_bytes(public)
        assert prototype.public_id(episode, query_index) == public_challenge_id(public)
        assert json.loads(expected_bytes) == public
        ids.append(prototype.public_id(episode, query_index))
    assert len(set(ids)) == 4


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"target_policy": "unknown"},
        {"target_policy": 1},
        {"target_policy": "exact_vertical3", "extra": 1},
    ],
)
def test_malformed_settings_reject(settings):
    prototype, adapter, _rivals = _modules()
    with pytest.raises(ValueError):
        prototype.program(settings)
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos=2, queries=4)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True},
        {"seed": -1},
        {"demos": 1},
        {"demos": 7},
        {"demos": 2.0},
        {"queries": 0},
        {"queries": 5},
        {"queries": True},
    ],
)
def test_request_boundaries_reject(kwargs):
    prototype, _adapter, _rivals = _modules()
    request = {"seed": 0, "demos": 2, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        prototype.generate(
            request["seed"],
            {"target_policy": "exact_vertical3"},
            demos=request["demos"],
            queries=request["queries"],
        )


def test_audit_tool_runs_bounded_without_racket():
    audit = _load(PARAM / "audit.py", "_p17b0_audit")
    report = audit.run_bounded(
        sampler_seeds=(0, 1),
        execution_seeds=(),
        demo_counts=(2, 3, 6),
        queries=4,
        execute_racket=False,
    )
    assert report["status"] == "passed"
    assert report["sampler_requests"] == 2 * 3 * len(POLICIES)
    assert report["harmful_survivors"] == []
    assert report["public_projection_failures"] == []
    assert report["racket_evaluations"] == 0

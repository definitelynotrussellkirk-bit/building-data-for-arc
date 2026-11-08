from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root


TASK_ID = "cfadc43e5098"
TEST_ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location("cfadc43e5098_parametric", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = []
    for line in canonical_path(TEST_ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    assert len(rows) == 2
    assert rows[0]["program_solution"] == rows[1]["program_solution"]
    return rows[0]["program_solution"]


def frozen(grid):
    return tuple(map(tuple, grid))


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=64) as instance:
        yield instance


def test_parameter_contract_and_default_program_are_exact():
    prototype = load_prototype()
    assert prototype.ALLOWED_BLOCKER_POLICIES == ("same_color", "any_color")
    assert prototype.DEFAULT_BLOCKER_POLICY == "same_color"
    assert prototype.racket_program("same_color") == canonical_program()
    alternate = prototype.racket_program("any_color")
    assert alternate != canonical_program()
    assert alternate.count("#t") == canonical_program().count("#t") + 1
    assert prototype.racket_sha256("same_color") == hashlib.sha256(canonical_program().encode()).hexdigest()


@pytest.mark.parametrize("policy", ["same_color", "any_color"])
def test_episode_has_two_demos_four_distinct_queries_and_racket_labels(bridge, policy):
    prototype = load_prototype()
    episode = prototype.build_episode(
        bridge,
        seed=17,
        blocker_policy=policy,
        demo_count=2,
        query_count=4,
    )
    assert episode["parameter"] == {"blocker_policy": policy}
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    all_pairs = episode["train"] + episode["test"]
    assert len({frozen(pair["input"]) for pair in all_pairs}) == 6
    for pair in all_pairs:
        assert pair["output"] == prototype.run_racket(bridge, policy, pair["input"])

    analysis = prototype.analyze_episode(bridge, episode)
    assert analysis["production"]["status"] == "no_ambiguity_found"
    assert analysis["production"]["actual_demo_count"] == 2
    assert analysis["production"]["actual_query_count"] == 4
    assert all(row["query_input_distinct"] for row in analysis["queries"])
    assert all(row["query_differs_under_alternative"] for row in analysis["queries"])
    assert all(row["alternative_refuted_by_demonstrations"] for row in analysis["queries"])


def test_public_projection_uses_only_visible_content_for_identifier(bridge):
    prototype = load_prototype()
    episode = prototype.build_episode(bridge, seed=23, blocker_policy="same_color", demo_count=2, query_count=4)
    public = prototype.public_challenge(episode)
    assert set(public) == {"schema", "episode_id", "train", "test"}
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    assert "blocker_policy" not in serialized
    assert "program_solution" not in serialized

    hidden_changed = deepcopy(episode)
    hidden_changed["parameter"]["blocker_policy"] = "any_color"
    hidden_changed["test"][0]["output"][0][0] = (hidden_changed["test"][0]["output"][0][0] + 1) % 10
    assert prototype.public_challenge(hidden_changed)["episode_id"] == public["episode_id"]


def test_invalid_parameter_and_counts_fail_closed(bridge):
    prototype = load_prototype()
    with pytest.raises(ValueError):
        prototype.racket_program("all_objects")
    with pytest.raises(TypeError):
        prototype.build_episode(bridge, seed=True)
    with pytest.raises(ValueError):
        prototype.build_episode(bridge, seed=1, demo_count=0)
    with pytest.raises(ValueError):
        prototype.build_episode(bridge, seed=1, query_count=0)

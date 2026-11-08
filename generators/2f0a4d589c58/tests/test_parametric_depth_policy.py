"""Focused tests for the proposed crossing-bar depth-policy prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace/parametric/prototype.py"
GENERATOR_PATH = TASK_ROOT / "generator.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "2f0a4d589c58":
                rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def test_prototype_module_exists():
    assert PROTOTYPE_PATH.is_file()


def test_default_program_is_exact_canonical_and_alternatives_are_distinct():
    prototype = _load(PROTOTYPE_PATH, "depth_policy_default_test")
    canonical = _canonical_program()
    assert prototype.instantiate(canonical) == canonical
    programs = {
        policy: prototype.instantiate(canonical, policy)
        for policy in prototype.DEPTH_POLICIES
    }
    assert len(set(programs.values())) == len(prototype.DEPTH_POLICIES)
    assert programs[prototype.DEFAULT_DEPTH_POLICY] == canonical


def test_fixture_inputs_stay_in_the_canonical_generator_domain():
    prototype = _load(PROTOTYPE_PATH, "depth_policy_fixture_test")
    generator = _load(GENERATOR_PATH, "depth_policy_generator_test")
    fixtures = prototype.fixture_inputs(20261020)
    assert len(fixtures) == 4
    assert all(generator.self_check(grid) == [] for grid in fixtures)
    fronts = [generator.observe_overrides(grid)["occluder"] for grid in fixtures]
    assert set(fronts[:3]) == {"horizontal", "vertical"}
    assert fronts[3] == "vertical"


def test_racket_executes_every_policy_and_matches_independent_python_oracle():
    prototype = _load(PROTOTYPE_PATH, "depth_policy_racket_test")
    canonical = _canonical_program()
    from arc_repl.racket_bridge import RacketBridge

    fixtures = prototype.fixture_inputs(20261020)
    with RacketBridge() as bridge:
        outputs = {
            policy: [
                prototype.execute(bridge, prototype.instantiate(canonical, policy), grid)
                for grid in fixtures
            ]
            for policy in prototype.DEPTH_POLICIES
        }
    for policy in prototype.DEPTH_POLICIES:
        assert outputs[policy] == [
            prototype.python_apply(grid, policy) for grid in fixtures
        ]
    for index in range(len(fixtures)):
        assert len({
            json.dumps(outputs[policy][index], separators=(",", ":"))
            for policy in prototype.DEPTH_POLICIES
        }) >= 2


def test_each_seed_uses_one_policy_and_demonstrations_distinguish_query_rivals():
    prototype = _load(PROTOTYPE_PATH, "depth_policy_episode_test")
    canonical = _canonical_program()
    from arc_repl.racket_bridge import RacketBridge

    seeds = prototype.representative_seeds()
    assert set(seeds) == set(prototype.DEPTH_POLICIES)
    with RacketBridge() as bridge:
        episodes = [
            prototype.episode(seed, canonical, bridge)
            for seed in seeds.values()
        ]
    assert {row["parameters"]["depth_policy"] for row in episodes} == set(
        prototype.DEPTH_POLICIES
    )
    for row in episodes:
        assert len(row["train"]) == 3 and len(row["test"]) == 1
        assert all(rival["demo_differences"] for rival in row["rivals"])
        public = prototype.public_challenge(row)
        assert all("output" in pair for pair in public["train"])
        assert all("output" not in pair for pair in public["test"])


def test_materialized_rule_hashes_match_exact_saved_bytes(tmp_path):
    prototype = _load(PROTOTYPE_PATH, "depth_policy_materialize_test")
    out = tmp_path / "depth-policy"
    report = prototype.materialize(out)
    assert report["status"] == "prototype"
    assert report["default_program_exact"] is True
    for policy in prototype.DEPTH_POLICIES:
        private = json.loads(
            (out / "private" / f"episode-{policy}.json").read_text(encoding="utf-8")
        )
        rule_bytes = (out / "private" / "rules" / f"{policy}.rkt").read_bytes()
        assert hashlib.sha256(rule_bytes).hexdigest() == private["program_sha256"]
        public = json.loads(
            (out / "public" / f"episode-{policy}.json").read_text(encoding="utf-8")
        )
        assert all("output" not in pair for pair in public["test"])

"""Native parametric regressions for e942ce41cbf5."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "e942ce41cbf5"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _modules():
    return _load("prototype", "prototype.py"), _load("adapter", "adapter.py")


def _setting(policy: str) -> dict[str, str]:
    return {"operation_policy": policy}


def _inputs(episode: dict) -> list:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_settings_are_strict():
    prototype, adapter = _modules()
    canonical = (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8")
    ranked = (PARAMETRIC / "rank_control4.rkt").read_text(encoding="utf-8")

    assert adapter.program(_setting("canonical")) == canonical
    assert adapter.program(_setting("rank_control4")) == ranked
    assert canonical != ranked

    for bad in ({}, {"operation_policy": "unknown"}, {"operation_policy": "canonical", "x": 1}, None):
        with pytest.raises(ValueError):
            adapter.program(bad)
    assert prototype.POLICIES == ("canonical", "rank_control4")


def test_generation_is_deterministic_prefix_stable_and_matched_across_settings():
    prototype, adapter = _modules()
    for seed in (0, 17, 991):
        canonical = adapter.generate(seed, _setting("canonical"), 6, 4)
        ranked = adapter.generate(seed, _setting("rank_control4"), 6, 4)
        assert _inputs(canonical) == _inputs(ranked)
        assert canonical == adapter.generate(seed, _setting("canonical"), 6, 4)
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == 10

        for demos in range(2, 7):
            short = adapter.generate(seed, _setting("canonical"), demos, 1)
            assert short["train"] == canonical["train"][:demos]
            assert short["test"] == canonical["test"][:1]
        for queries in range(1, 5):
            short = adapter.generate(seed, _setting("canonical"), 3, queries)
            assert short["train"] == canonical["train"][:3]
            assert short["test"] == canonical["test"][:queries]


def test_two_demonstrations_identify_the_selected_setting_and_claims_match_mirror():
    prototype, adapter = _modules()
    for seed in range(12):
        episodes = {
            policy: adapter.generate(seed, _setting(policy), 2, 4)
            for policy in prototype.POLICIES
        }
        assert [pair["input"] for pair in episodes["canonical"]["train"]] == [
            pair["input"] for pair in episodes["rank_control4"]["train"]
        ]
        assert episodes["canonical"]["train"][0]["output"] != episodes["rank_control4"]["train"][0]["output"]
        first = prototype.describe_case(episodes["rank_control4"]["train"][0]["input"])
        second = prototype.describe_case(episodes["rank_control4"]["train"][1]["input"])
        assert first["operation_control"] == second["operation_control"] == 4
        assert [first["post_transform_relation"], second["post_transform_relation"]] == [
            "xor_smaller", "intersection_smaller"
        ]
        assert [first["ranked_operation"], second["ranked_operation"]] == [6, 4]
        assert first["pre_transform_relation"] != first["post_transform_relation"]
        assert first["wrong_pretransform_operation"] != first["ranked_operation"]

        for chosen, episode in episodes.items():
            survivors = []
            for rival in prototype.POLICIES:
                if all(prototype.solve(pair["input"], rival) == pair["output"] for pair in episode["train"]):
                    survivors.append(rival)
            assert survivors == [chosen]
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.solve(pair["input"], chosen)

        three = {
            policy: adapter.generate(seed, _setting(policy), 3, 4)
            for policy in prototype.POLICIES
        }
        assert prototype.describe_case(three["rank_control4"]["train"][2]["input"])["operation_control"] == 6
        assert three["rank_control4"]["train"][2]["output"] == three["canonical"]["train"][2]["output"]


def test_minimum_lesson_refutes_fixed_transform_shortcuts():
    prototype, adapter = _modules()

    def predict_with_fixed_transform(grid, transform_control):
        blue, red_raw, operation, _ = prototype._parse(grid)
        red = prototype._transform(red_raw, transform_control)
        return prototype._render(prototype._combine(blue, red, operation))

    for seed in range(64):
        episode = adapter.generate(seed, _setting("canonical"), 2, 4)
        for fixed in prototype.TRANSFORM_CONTROLS:
            assert not all(
                predict_with_fixed_transform(pair["input"], fixed) == pair["output"]
                for pair in episode["train"]
            )


def test_fourth_query_is_substantive_30x30_and_exposes_the_causal_dependency():
    prototype, adapter = _modules()
    episode = adapter.generate(17, _setting("rank_control4"), 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 150
    assert len({r for r, _ in nonzero}) >= 24
    assert len({c for _, c in nonzero}) >= 24
    assert any(r in (0, 29) or c in (0, 29) for r, c in nonzero)

    description = prototype.describe_case(grid)
    assert description["post_transform_relation"] == "xor_smaller"
    assert description["pre_transform_relation"] == "intersection_smaller"
    intended = prototype.solve(grid, "rank_control4")
    wrong = prototype.solve_ranked_with_pretransform_intermediate(grid)
    assert intended != wrong


def test_public_turn_hides_private_fields_and_first_turn_matches_single_query_use():
    prototype, adapter = _modules()
    full = adapter.generate(33, _setting("rank_control4"), 3, 4)
    single = adapter.generate(33, _setting("rank_control4"), 3, 1)
    first_full = prototype.public_turn(full, 0)
    first_single = prototype.public_turn(single, 0)
    assert first_full == first_single
    assert set(first_full) == {"train", "test"}
    assert len(first_full["test"]) == 1
    assert set(first_full["test"][0]) == {"input"}
    raw = public_challenge_bytes(first_full)
    public = json.loads(raw)
    assert public == first_full
    assert public_challenge_id(first_full) == __import__("hashlib").sha256(raw).hexdigest()

    altered = copy.deepcopy(full)
    altered["program_solution"] = "private-change"
    altered["test"][0]["output"] = [[9]]
    assert prototype.public_turn(altered, 0) == first_full


def test_bounded_self_audit_refutes_declared_shortcuts():
    audit = _load("self_audit", "self_audit.py")
    report = audit.structural_audit(range(32))
    assert report["status"] == "pass"
    assert report["episodes"] == 64
    assert report["lesson_prefixes"] == 320
    assert report["teaching_gaps"] == []
    assert report["rival_errors"] == []
    assert report["stress_30x30"] == 64
    assert report["causal_cases"] == 64


def test_invalid_counts_and_query_indices_are_rejected():
    prototype, adapter = _modules()
    for demos, queries in ((1, 4), (7, 4), (3, 0), (3, 5), (True, 4)):
        with pytest.raises(ValueError):
            adapter.generate(0, _setting("canonical"), demos, queries)
    episode = adapter.generate(0, _setting("canonical"), 2, 1)
    for index in (-1, 1, True):
        with pytest.raises(ValueError):
            prototype.public_turn(episode, index)

"""Focused contract tests for the native post-lookup repeat-policy family."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "0dba62203065"
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
    return _load(HOME / "prototype.py", "_0dba_repeat_policy_prototype")


@cache
def adapter():
    return _load(HOME / "adapter.py", "_0dba_repeat_policy_adapter")


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for row in Catalog(ROOT).get(TASK_ID)["variants"]
        if isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_alternate_consumes_post_lookup_colors():
    p = prototype()
    canonical = _canonical_program()
    alternate = p.program_for("mark_repeated")
    assert p.program_for("retain") == canonical
    assert alternate != canonical
    assert "(new-color (at g 0 (second bb)))" in alternate
    assert "stage1" in alternate
    assert "obj-color" in alternate
    assert "(length same-color)" in alternate
    assert "paint-cells out" in alternate
    assert " 9" in alternate


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
@pytest.mark.parametrize("policy", ["retain", "mark_repeated"])
def test_adapter_supports_counts_matched_inputs_prefixes_and_claim_labels(demos, queries, policy):
    p = prototype()
    a = adapter()
    settings = {"repeat_policy": policy}
    episode = a.generate(1729, settings, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == a.program(settings) == p.program_for(policy)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)}) == demos + queries
    assert all(pair["output"] == p.transform(pair["input"], policy) for pair in episode["train"])
    assert all(pair["output"] == p.transform(pair["input"], policy) for pair in episode["test"])

    full = a.generate(1729, settings, demos=6, queries=4)
    assert episode["train"] == full["train"][:demos]
    assert episode["test"] == full["test"][:queries]
    other = "mark_repeated" if policy == "retain" else "retain"
    matched = a.generate(1729, {"repeat_policy": other}, demos=demos, queries=queries)
    assert _inputs(episode) == _inputs(matched)
    assert all(x["output"] != y["output"] for x, y in zip(episode["train"], matched["train"], strict=True))


def test_four_queries_cover_transfer_boundary_and_substantive_30x30_stress():
    p = prototype()
    episode = adapter().generate(17, {"repeat_policy": "mark_repeated"}, demos=3, queries=4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(12, 14), (18, 20), (24, 27), (30, 30)]
    stress = episode["test"][-1]["input"]
    analysis = p.analyze(stress)
    assert len(analysis["components"]) >= 7
    assert sum(len(cells) for cells in analysis["components"]) >= 35
    assert any(min(c for _, c in cells) == 0 for cells in analysis["components"])
    assert any(max(c for _, c in cells) == 28 for cells in analysis["components"])
    assert all(stress[r][29] == 0 for r in range(1, 30))


def test_two_visible_demos_reject_all_declared_harmful_rivals_for_each_setting():
    p = prototype()
    for seed in (0, 17, 999):
        for policy in p.POLICIES:
            episode = adapter().generate(seed, {"repeat_policy": policy}, demos=2, queries=4)
            report = p.audit_episode(episode, policy)
            assert report["harmful_survivors"] == []
            assert report["setting_survivors"] == [policy]
            assert set(report["refuted_rivals"]) == set(p.RIVALS)


def test_sequential_public_views_reveal_one_query_without_private_leaks():
    p = prototype()
    a = adapter()
    one = a.generate(23, {"repeat_policy": "retain"}, demos=3, queries=1)
    full = a.generate(23, {"repeat_policy": "retain"}, demos=3, queries=4)
    views = p.sequential_views(full)
    assert len(views) == 4
    assert views[0] == p.public_challenge(one)
    assert public_challenge_bytes(views[0]) == public_challenge_bytes(p.public_challenge(one))
    assert public_challenge_id(views[0]) == public_challenge_id(p.public_challenge(one))
    for index, view in enumerate(views):
        assert set(view) == {"train", "test"}
        assert view["train"] == p.public_challenge(full)["train"]
        assert view["test"] == [{"input": full["test"][index]["input"]}]
        rendered = json.dumps(view, sort_keys=True)
        assert "repeat_policy" not in rendered
        assert "program_solution" not in rendered
        assert "mark_repeated" not in rendered
        assert "retain" not in rendered


def test_dependency_facts_bind_stage_one_color_groups_to_stage_two_marking():
    p = prototype()
    pair = adapter().generate(17, {"repeat_policy": "mark_repeated"}, demos=3, queries=4)["test"][-1]
    facts = p.dependency_facts(pair["input"], "mark_repeated")
    assert facts["policy"] == "mark_repeated"
    assert facts["step_a"] == "left-edge header lookup recolors each body object"
    assert facts["step_b"] == "mark every post-lookup color class with multiplicity above one"
    assert len(facts["objects"]) >= 7
    frequencies = facts["post_lookup_color_frequencies"]
    assert any(count > 1 for count in frequencies.values())
    assert any(count == 1 for count in frequencies.values())
    for obj in facts["objects"]:
        assert obj["selected_column"] == obj["left_column"]
        assert obj["post_lookup_color"] == pair["input"][0][obj["selected_column"]]
        assert obj["marked"] is (frequencies[str(obj["post_lookup_color"])] > 1)
    assert p.lookup_stage(pair["input"]) == p.transform(pair["input"], "retain")
    assert p.transform(pair["input"], "mark_repeated") != p.transform(pair["input"], "retain")


def test_invalid_settings_counts_and_seed_fail_closed():
    a = adapter()
    for settings in ({}, {"repeat_policy": "x"}, {"repeat_policy": 1},
                     {"repeat_policy": "retain", "x": 1}):
        with pytest.raises(ValueError):
            a.program(settings)
        with pytest.raises(ValueError):
            a.generate(0, settings, 3, 4)
    for bad in (True, -1, 2**63, 1.5, "3"):
        with pytest.raises(ValueError, match="seed"):
            a.generate(bad, {"repeat_policy": "retain"}, 3, 4)
    for bad in (1, 7, True, 3.0):
        with pytest.raises(ValueError, match="demos"):
            a.generate(0, {"repeat_policy": "retain"}, bad, 4)
    for bad in (0, 5, True, 4.0):
        with pytest.raises(ValueError, match="queries"):
            a.generate(0, {"repeat_policy": "retain"}, 3, bad)


def test_audit_tool_has_bounded_job_matrix_independent_oracle_and_clean_episode():
    audit = _load(HOME / "audit.py", "_0dba_repeat_policy_audit")
    jobs = audit.build_jobs(seeds=(0, 17), demo_counts=(2, 3, 6))
    assert len(jobs) == 12
    assert {job["demos"] for job in jobs} == {2, 3, 6}
    assert {job["queries"] for job in jobs} == {4}
    assert {job["seed"] for job in jobs} == {0, 17}
    assert {job["settings"]["repeat_policy"] for job in jobs} == {"retain", "mark_repeated"}

    episode = adapter().generate(17, {"repeat_policy": "mark_repeated"}, demos=2, queries=4)
    record = audit.analyze_episode(episode, "mark_repeated")
    assert record["setting_survivors"] == ["mark_repeated"]
    assert record["harmful_survivors"] == []
    assert set(record["refuted_rivals"]) == set(prototype().RIVALS)
    assert record["oracle_mismatches"] == []
    assert record["public_turn_failures"] == []

"""Parametric family regressions for 4d0f228177b0."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "4d0f228177b0":
                value = row.get("program_solution")
                if isinstance(value, str):
                    programs.add(value)
    assert len(programs) == 1
    return next(iter(programs))


def test_adapter_default_program_is_exact_canonical_bytes():
    adapter = _load("parametric_adapter_4d0", "adapter.py")
    assert adapter.program({"finish": "canonical"}) == _canonical_program()
    assert adapter.program({"finish": "first_hit_payload"}) != _canonical_program()


def test_minimum_two_demos_are_matched_and_identify_each_setting():
    proto = _load("parametric_proto_4d0", "prototype.py")
    adapter = _load("parametric_adapter_4d0_counts", "adapter.py")
    canonical = adapter.generate(13, {"finish": "canonical"}, 2, 4)
    alternate = adapter.generate(13, {"finish": "first_hit_payload"}, 2, 4)
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in alternate["train"] + alternate["test"]
    ]
    assert proto.lesson_errors(canonical, {"finish": "canonical"}) == []
    assert proto.lesson_errors(alternate, {"finish": "first_hit_payload"}) == []
    assert canonical["train"] != alternate["train"]


def test_demo_and_query_counts_are_independent_prefixes():
    adapter = _load("parametric_adapter_4d0_prefix", "adapter.py")
    setting = {"finish": "first_hit_payload"}
    small = adapter.generate(29, setting, 2, 1)
    large = adapter.generate(29, setting, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    inputs = [json.dumps(p["input"]) for p in large["train"] + large["test"]]
    assert len(inputs) == len(set(inputs)) == 10


def test_four_query_bank_has_transfer_boundary_inactive_and_30x30_stress():
    proto = _load("parametric_proto_4d0_queries", "prototype.py")
    adapter = _load("parametric_adapter_4d0_queries", "adapter.py")
    episode = adapter.generate(41, {"finish": "first_hit_payload"}, 3, 4)
    profiles = [proto.scene_facts(pair["input"]) for pair in episode["test"]]
    assert {p["vertical_color"] for p in profiles if p["active"]} == {3, 6}
    assert any(not p["active"] for p in profiles)
    assert any(p["height"] == 30 and p["width"] == 30 for p in profiles)
    assert any(p["boundary_payload"] for p in profiles)


def test_alternate_uses_first_hit_color_and_recolors_remote_payloads_only():
    proto = _load("parametric_proto_4d0_semantics", "prototype.py")
    scenes = proto.build_banks(7)
    for scene in scenes["demos"][:2] + scenes["queries"]:
        facts = proto.scene_facts(scene)
        canonical = proto.apply(scene, {"finish": "canonical"})
        alternate = proto.apply(scene, {"finish": "first_hit_payload"})
        if facts["active"]:
            selected = facts["first_hit_color"]
            assert selected in (7, 9)
            assert facts["later_hit_color"] in ({7, 9} - {selected})
            selected_cells = [
                (r, c)
                for r, row in enumerate(canonical)
                for c, value in enumerate(row)
                if value == selected
            ]
            assert len(selected_cells) >= 3
            assert all(alternate[r][c] == 8 for r, c in selected_cells)
            other = 7 if selected == 9 else 9
            assert any(
                value == other and alternate[r][c] == other
                for r, row in enumerate(scene)
                for c, value in enumerate(row)
            )
            assert alternate != canonical
        else:
            assert alternate == canonical


def test_validator_and_adapter_reject_malformed_requests():
    proto = _load("parametric_proto_4d0_validation", "prototype.py")
    adapter = _load("parametric_adapter_4d0_validation", "adapter.py")
    with pytest.raises(ValueError):
        adapter.program({"finish": "unknown"})
    for demos, queries in ((1, 4), (7, 4), (2, 0), (2, 5), (True, 4)):
        with pytest.raises(ValueError):
            adapter.generate(1, {"finish": "canonical"}, demos, queries)
    valid = proto.build_banks(1)["demos"][0]
    malformed = [row[:] for row in valid]
    malformed[0][0] = False
    with pytest.raises(ValueError):
        proto.validate_input(malformed)


def test_certificate_rejects_forgery_duplicate_bool_wrong_program_and_counts():
    adapter = _load("parametric_adapter_4d0_certificate", "adapter.py")
    setting = {"finish": "first_hit_payload"}
    episode = adapter.generate(5, setting, 2, 4)
    assert adapter.certificate_errors(episode, setting, demos=2, queries=4) == []

    forged = json.loads(json.dumps(episode))
    forged["test"][0]["output"][0][0] = (forged["test"][0]["output"][0][0] + 1) % 10
    assert adapter.certificate_errors(forged, setting, demos=2, queries=4)

    duplicate = json.loads(json.dumps(episode))
    duplicate["test"][0]["input"] = duplicate["train"][0]["input"]
    assert adapter.certificate_errors(duplicate, setting, demos=2, queries=4)

    boolean = json.loads(json.dumps(episode))
    boolean["train"][0]["input"][0][0] = False
    assert adapter.certificate_errors(boolean, setting, demos=2, queries=4)

    wrong_program = json.loads(json.dumps(episode))
    wrong_program["program_solution"] = adapter.program({"finish": "canonical"})
    assert adapter.certificate_errors(wrong_program, setting, demos=2, queries=4)

    assert adapter.certificate_errors(episode, setting, demos=3, queries=4)

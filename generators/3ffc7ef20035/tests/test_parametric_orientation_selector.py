from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "3ffc7ef20035"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load("test_3ffc7ef20035_orientation_prototype", "prototype.py")


def _adapter():
    return _load("test_3ffc7ef20035_orientation_adapter", "adapter.py")


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _pairs(episode):
    return episode["train"] + episode["test"]


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    prototype = _prototype()
    assert prototype.DEFAULT_SCOPE == "all_blue_bbox"
    assert prototype.SCOPES == ("all_blue_bbox", "bar_orientation_component")
    assert prototype.program_for("all_blue_bbox") == _canonical_program()
    assert prototype.program_for("bar_orientation_component") != _canonical_program()
    assert hashlib.sha256(prototype.program_for("all_blue_bbox").encode()).hexdigest() == (
        "9def40d6c822da10f74a0c9db35672e1c16209db56723d189c7c324948ad3a75"
    )


def test_adapter_validates_exact_setting_contract():
    adapter = _adapter()
    assert adapter.program({"scope": "all_blue_bbox"}) == _canonical_program()
    with pytest.raises(ValueError, match="exactly scope"):
        adapter.program({})
    with pytest.raises(ValueError, match="undeclared scope"):
        adapter.program({"scope": "nearest"})
    with pytest.raises(ValueError, match="exactly scope"):
        adapter.program({"scope": "all_blue_bbox", "extra": True})


@pytest.mark.parametrize("demos", range(2, 7))
def test_supported_demo_counts_return_four_distinct_queries_and_teach_both_orientations(demos):
    prototype = _prototype()
    episode = prototype.generate_episode(
        1000 + demos,
        scope="bar_orientation_component",
        demos=demos,
        queries=4,
    )
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in _pairs(episode)]
    assert len(keys) == len(set(keys))
    demo_orientations = {
        prototype.observe_scene(pair["input"])["selector_orientation"]
        for pair in episode["train"]
    }
    assert demo_orientations == {"horizontal", "vertical"}
    assert all(
        pair["output"] == prototype.transform_python(pair["input"], "bar_orientation_component")
        for pair in _pairs(episode)
    )


def test_identical_request_uses_identical_inputs_across_settings_but_different_labels():
    prototype = _prototype()
    canonical = prototype.generate_episode(314159, scope="all_blue_bbox", demos=3, queries=4)
    selected = prototype.generate_episode(
        314159, scope="bar_orientation_component", demos=3, queries=4
    )
    assert [pair["input"] for pair in _pairs(canonical)] == [
        pair["input"] for pair in _pairs(selected)
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(_pairs(canonical), _pairs(selected), strict=True)
    )


def test_four_query_episode_contains_substantive_30_by_30_stress_scene():
    prototype = _prototype()
    episode = prototype.generate_episode(
        271828, scope="bar_orientation_component", demos=3, queries=4
    )
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    scene = prototype.observe_scene(stress)
    assert [component["size"] for component in scene["blue_components"]] == [24, 27]
    r0, c0, r1, c1 = scene["global_blue_bbox"]
    assert r1 - r0 + 1 >= 24
    assert c1 - c0 + 1 >= 24
    assert scene["selector_size"] == 3
    assert sum(cell != 0 for row in stress for cell in row) >= 54


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    prototype = _prototype()
    random.seed(1234567)
    before = random.getstate()
    left = prototype.generate_episode(77, scope="all_blue_bbox", demos=6, queries=4)
    after = random.getstate()
    right = prototype.generate_episode(77, scope="all_blue_bbox", demos=6, queries=4)
    assert before == after
    assert left == right
    assert left is not right
    assert left["train"][0]["input"] is not right["train"][0]["input"]
    left["train"][0]["input"][0][0] = 9
    assert left != right


@pytest.mark.parametrize("scope", ("all_blue_bbox", "bar_orientation_component"))
@pytest.mark.parametrize("demos", range(2, 7))
def test_named_rival_audit_finds_no_demo_fitting_query_changing_rule(scope, demos):
    prototype = _prototype()
    for seed in (0, 17, 991):
        episode = prototype.generate_episode(seed, scope=scope, demos=demos, queries=4)
        audit = prototype.audit_episode(episode)
        assert audit["selected_scope"] == scope
        assert audit["blocking_rivals"] == []
        assert audit["surviving_hypotheses"] == [scope]
        assert audit["query_count"] == 4


def test_public_turns_reveal_one_query_without_private_or_future_fields():
    prototype = _prototype()
    episode = prototype.generate_episode(
        424242, scope="bar_orientation_component", demos=3, queries=4
    )
    turns = prototype.public_turns(episode)
    assert len(turns) == 4
    assert all(len(turn["test"]) == 1 for turn in turns)
    assert [turn["test"][0]["input"] for turn in turns] == [
        pair["input"] for pair in episode["test"]
    ]
    first = prototype.public_turn(episode, 0)
    assert public_challenge_bytes(first) == public_challenge_bytes(turns[0])
    assert public_challenge_id(first) == public_challenge_id(turns[0])
    visible = public_challenge_bytes(first)
    assert b"bar_orientation_component" not in visible
    assert b"program" not in visible
    assert b"settings" not in visible
    mutated = copy.deepcopy(episode)
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_bytes(prototype.public_turn(mutated, 0)) == visible
    assert episode["test"][1]["input"] not in [pair["input"] for pair in first["test"]]


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"seed": True, "scope": "all_blue_bbox", "demos": 3, "queries": 4}, "seed"),
        ({"seed": 0, "scope": "bad", "demos": 3, "queries": 4}, "scope"),
        ({"seed": 0, "scope": "all_blue_bbox", "demos": 1, "queries": 4}, "demos"),
        ({"seed": 0, "scope": "all_blue_bbox", "demos": 7, "queries": 4}, "demos"),
        ({"seed": 0, "scope": "all_blue_bbox", "demos": 3, "queries": 0}, "queries"),
        ({"seed": 0, "scope": "all_blue_bbox", "demos": 3, "queries": 9}, "queries"),
    ],
)
def test_invalid_generation_requests_fail_loudly(kwargs, message):
    prototype = _prototype()
    with pytest.raises((TypeError, ValueError), match=message):
        prototype.generate_episode(**kwargs)


def test_audit_tool_writes_bounded_report_and_opaque_public_files(tmp_path):
    audit_tool = _load("test_3ffc7ef20035_orientation_audit", "audit.py")
    report = audit_tool.run_audit(
        tmp_path / "audit",
        seeds=(0, 17),
        demo_counts=(2, 3),
        queries=4,
    )
    assert report["status"] == "passed"
    assert report["episodes_checked"] == 8
    assert report["matched_input_requests_checked"] == 4
    assert report["blocking_rivals"] == []
    public_dir = tmp_path / "audit" / "public"
    files = sorted(public_dir.glob("challenge-*.json"))
    assert len(files) == 8
    assert all(file.stem.removeprefix("challenge-") == hashlib.sha256(file.read_bytes()).hexdigest() for file in files)
    assert all(set(json.loads(file.read_text())) == {"train", "test"} for file in files)
    assert all(len(json.loads(file.read_text())["test"]) == 1 for file in files)
    assert (tmp_path / "audit" / "summary.json").is_file()

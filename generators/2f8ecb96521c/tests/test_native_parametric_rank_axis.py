"""Native parametric contract for size and dominant-axis rank assignment."""
from __future__ import annotations

import copy
import importlib.util
import json

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "2f8ecb96521c"
ROOT = find_root(__file__)
HERE = ROOT / f"generators/{TASK_ID}/workspace/parametric"


def load(name: str):
    path = HERE / name
    assert path.is_file(), f"missing native source: {path}"
    spec = importlib.util.spec_from_file_location(f"rank_axis_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return next(iter(programs))


def pairs(episode):
    return [*episode["train"], *episode["test"]]


def test_contract_and_exact_programs():
    p = load("native_family.py")
    adapter = load("adapter.py")
    promotion = json.loads((HERE / "promotion.json").read_text())

    assert p.MODES == ("small_to_large", "large_to_small", "dominant_axis")
    assert p.DEFAULT == {"rank_order": "small_to_large"}
    assert p.program(p.DEFAULT) == canonical_program()
    assert adapter.program(p.DEFAULT) == canonical_program()
    assert len({p.program({"rank_order": mode}) for mode in p.MODES}) == 3
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"rank_order": list(p.MODES)},
        "default": p.DEFAULT,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/native_family.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/README.md",
        ],
    }


def test_generation_is_prefix_stable_matched_and_identifiable():
    p = load("native_family.py")
    episodes = {
        mode: p.generate(17, {"rank_order": mode}, demos=6, queries=4)
        for mode in p.MODES
    }
    two = p.generate(17, p.DEFAULT, demos=2, queries=4)
    one_query = p.generate(17, p.DEFAULT, demos=6, queries=1)

    assert two["train"] == episodes["small_to_large"]["train"][:2]
    assert one_query["train"] == episodes["small_to_large"]["train"]
    assert one_query["test"] == episodes["small_to_large"]["test"][:1]
    input_vectors = [[pair["input"] for pair in pairs(ep)] for ep in episodes.values()]
    assert all(vector == input_vectors[0] for vector in input_vectors[1:])
    assert len({json.dumps(grid, separators=(",", ":")) for grid in input_vectors[0]}) == 10

    label_vectors = {
        mode: json.dumps([pair["output"] for pair in ep["train"][:2]], separators=(",", ":"))
        for mode, ep in episodes.items()
    }
    assert len(set(label_vectors.values())) == 3
    assert all(p.teaching_check(ep) == [] for ep in episodes.values())


def test_dominant_axis_intermediate_changes_the_object_order():
    p = load("native_family.py")
    ep = p.generate(5, {"rank_order": "dominant_axis"}, demos=2, queries=4)
    facts = [p.analyze(pair["input"]) for pair in ep["train"]]
    assert [fact["axis_first_is_small"] for fact in facts] == [True, False]
    assert {fact["dominant_axis"] for fact in facts} == {"row", "column"}
    for pair in ep["train"]:
        assert p.claim(pair["input"], "dominant_axis") == pair["output"]


def test_fourth_query_is_a_substantive_30x30_all_boundary_stress():
    p = load("native_family.py")
    pair = p.generate(31, {"rank_order": "dominant_axis"}, demos=3, queries=4)["test"][3]
    grid = pair["input"]
    assert len(grid) == len(grid[0]) == 30
    assert sum(v != 0 for row in grid for v in row) >= 350
    assert all(any(v != 0 for v in edge) for edge in (
        grid[0], grid[-1], [row[0] for row in grid], [row[-1] for row in grid]
    ))
    facts = p.analyze(grid)
    assert facts["areas"][0] != facts["areas"][1]
    assert facts["dominant_axis"] in {"row", "column"}


def test_public_first_turn_masks_settings_program_answers_and_future_queries():
    p = load("native_family.py")
    ep = p.generate(37, {"rank_order": "dominant_axis"}, demos=3, queries=4)
    first = p.public_turn_bytes(ep, 0)
    visible = json.loads(first)
    assert set(visible) == {"train", "test"}
    assert visible["test"] == [{"input": ep["test"][0]["input"]}]
    assert first == public_challenge_bytes({"train": ep["train"], "test": ep["test"][:1]})

    changed = copy.deepcopy(ep)
    changed["settings"] = {"private": "changed"}
    changed["program_solution"] = "changed"
    changed["test"][0]["output"] = [[9]]
    changed["test"][3]["input"] = [[9]]
    assert p.public_turn_bytes(changed, 0) == first


def test_validation_fails_closed():
    p = load("native_family.py")
    for settings in ({}, {"rank_order": "bad"}, {"rank_order": True},
                     {"rank_order": "small_to_large", "extra": 1}):
        with pytest.raises(ValueError):
            p.program(settings)
    for kwargs in (
        {"seed": True}, {"seed": -1}, {"demos": 1}, {"demos": 7},
        {"demos": 2.0}, {"queries": 0}, {"queries": 5}, {"queries": True},
    ):
        args = {"seed": 0, "settings": p.DEFAULT, "demos": 3, "queries": 4}
        args.update(kwargs)
        with pytest.raises(ValueError):
            p.generate(**args)
    for grid in ([], [[]], [[True]], [[0], [0, 1]], [[10]], [[4, 4], [4, 4]]):
        with pytest.raises(ValueError):
            p.analyze(grid)
    for index in (-1, 4, True):
        with pytest.raises(ValueError):
            p.public_turn_bytes(p.generate(0, p.DEFAULT, 3, 4), index)


def test_minimum_lesson_rejects_all_declared_rivals_across_audit_seeds():
    p = load("native_family.py")
    findings = []
    for seed in range(32):
        for mode in p.MODES:
            episode = p.generate(seed, {p.PARAMETER: mode}, demos=2, queries=4)
            if episode["certificate"]["findings"]:
                findings.append((seed, mode, episode["certificate"]["findings"]))
    assert findings == []


def test_reusable_audit_covers_every_supported_prefix_without_findings():
    audit = load("audit_native.py")
    report = audit.build_report(range(4))
    assert report["ok"] is True
    assert report["findings"] == []
    assert report["episodes_checked"] == 4 * 3 * 5 * 4
    assert report["demo_counts"] == [2, 3, 4, 5, 6]
    assert report["query_counts"] == [1, 2, 3, 4]
    assert set(report["declared_rivals"]) == set(load("native_family.py").RIVALS)

"""Proposed full-template versus marker-fragment propagation family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTO = HOME / "workspace" / "parametric"


def load(name="adapter"):
    path = PROTO / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"tested_b2_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_selected_authority():
    adapter = load()
    canonical = {
        row["program_solution"]
        for row in map(json.loads, (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
        if row.get("task_id") == "b2d6e6b60917"
    }
    assert canonical == {adapter.program({"template": "full"})}
    assert adapter.program({"template": "fragment"}) != adapter.program({"template": "full"})


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_and_demo_only_identification(demos):
    adapter, proto = load(), load("prototype")
    full = adapter.generate(17, {"template": "full"}, demos, 4)
    fragment = adapter.generate(17, {"template": "fragment"}, demos, 4)
    one = adapter.generate(17, {"template": "full"}, demos, 1)
    assert len(full["train"]) == demos and len(full["test"]) == 4
    assert full["train"] == one["train"] and full["test"][:1] == one["test"]
    assert all_inputs(full) == all_inputs(fragment)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs(full)}) == demos + 4
    assert all(a["output"] != b["output"] for split in ("train", "test") for a, b in zip(full[split], fragment[split]))
    assert proto.teaching_certificate(full)["survivors"] == [{"template": "full"}]
    assert proto.teaching_certificate(fragment)["survivors"] == [{"template": "fragment"}]
    assert proto.visible_turn(full, 0) == public_challenge_bytes(one)
    changed = deepcopy(full)
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == public_challenge_bytes(full)
    assert public_challenge_id(changed) == public_challenge_id(full)


def test_four_queries_include_substantive_30x30_ray_scene():
    adapter = load()
    episode = adapter.generate(91, {"template": "full"}, 3, 4)
    pair = episode["test"][-1]
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    occupied = {(r, c) for r, row in enumerate(pair["output"]) for c, value in enumerate(row) if value}
    assert len(occupied) >= 45
    assert max(r for r, _ in occupied) - min(r for r, _ in occupied) >= 20
    assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 20


def test_default_program_and_python_mirror_cover_all_canonical_pairs():
    from reviewer_support import load_selected_generator

    adapter = load()
    generator = load_selected_generator("b2d6e6b60917", root=ROOT)[0]
    assert adapter.program({"template": "full"})
    for pair in canonical_pairs("b2d6e6b60917", root=ROOT, labeled_only=True):
        assert generator.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("changes", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"settings": {}}, {"settings": {"template": "bbox"}},
    {"settings": {"template": "full", "extra": 1}},
    {"demos": 1}, {"demos": 7}, {"queries": 0}, {"queries": 5},
])
def test_invalid_controls_fail(changes):
    adapter = load()
    kwargs = dict(seed=17, settings={"template": "full"}, demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises(ValueError):
        adapter.generate(**kwargs)

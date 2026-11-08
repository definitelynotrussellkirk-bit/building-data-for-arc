"""Proposed source/reflection color-swap family for c6a422753abe."""
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
    spec = importlib.util.spec_from_file_location(f"tested_c6_{name}", path)
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
        if row.get("task_id") == "c6a422753abe"
    }
    assert canonical == {adapter.program({"swap_location": "source"})}
    assert adapter.program({"swap_location": "reflection"}) != adapter.program({"swap_location": "source"})


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_identification_and_public_projection(demos):
    adapter, proto = load(), load("prototype")
    source = adapter.generate(17, {"swap_location": "source"}, demos, 4)
    reflection = adapter.generate(17, {"swap_location": "reflection"}, demos, 4)
    one = adapter.generate(17, {"swap_location": "source"}, demos, 1)
    assert len(source["train"]) == demos and len(source["test"]) == 4
    assert source["train"] == one["train"] and source["test"][:1] == one["test"]
    assert all_inputs(source) == all_inputs(reflection)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs(source)}) == demos + 4
    assert all(a["output"] != b["output"] for split in ("train", "test") for a, b in zip(source[split], reflection[split]))
    assert proto.teaching_certificate(source)["survivors"] == [{"swap_location": "source"}]
    assert proto.teaching_certificate(reflection)["survivors"] == [{"swap_location": "reflection"}]
    assert proto.visible_turn(source, 0) == public_challenge_bytes(one)
    changed = deepcopy(source)
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(changed) == public_challenge_bytes(source)
    assert public_challenge_id(changed) == public_challenge_id(source)


def test_four_queries_include_substantive_30x30_case():
    adapter = load()
    episode = adapter.generate(91, {"swap_location": "source"}, 3, 4)
    pair = episode["test"][-1]
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    occupied = {(r, c) for r, row in enumerate(pair["output"]) for c, value in enumerate(row) if value not in (0, 1)}
    assert len(occupied) >= 36
    assert max(c for _, c in occupied) - min(c for _, c in occupied) >= 20


def test_default_program_and_python_mirror_cover_all_canonical_pairs():
    from reviewer_support import load_selected_generator

    adapter = load()
    generator = load_selected_generator("c6a422753abe", root=ROOT)[0]
    assert adapter.program({"swap_location": "source"})
    for pair in canonical_pairs("c6a422753abe", root=ROOT, labeled_only=True):
        assert generator.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("changes", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"settings": {}}, {"settings": {"swap_location": "both"}},
    {"settings": {"swap_location": "source", "extra": 1}},
    {"demos": 1}, {"demos": 7}, {"queries": 0}, {"queries": 5},
])
def test_invalid_controls_fail(changes):
    adapter = load()
    kwargs = dict(seed=17, settings={"swap_location": "source"}, demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises(ValueError):
        adapter.generate(**kwargs)

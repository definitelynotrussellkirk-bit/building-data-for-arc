"""Proposed clockwise/counterclockwise family for d336f5fb2da4."""
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
    spec = importlib.util.spec_from_file_location(f"tested_d336_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_authority():
    adapter = load()
    canonical = {
        row["program_solution"]
        for row in map(json.loads, (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
        if row.get("task_id") == "d336f5fb2da4"
    }
    assert canonical == {adapter.program({"magenta_rotation": "cw"})}
    assert adapter.program({"magenta_rotation": "ccw"}) != adapter.program({"magenta_rotation": "cw"})


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_inputs_prefix_and_finite_identification(demos):
    adapter = load()
    proto = load("prototype")
    cw = adapter.generate(17, {"magenta_rotation": "cw"}, demos, 4)
    ccw = adapter.generate(17, {"magenta_rotation": "ccw"}, demos, 4)
    one = adapter.generate(17, {"magenta_rotation": "cw"}, demos, 1)
    assert len(cw["train"]) == demos and len(cw["test"]) == 4
    assert cw["train"] == one["train"] and cw["test"][:1] == one["test"]
    assert _inputs(cw) == _inputs(ccw)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(cw)}) == demos + 4
    assert cw["train"][0]["output"] != ccw["train"][0]["output"]
    assert cw["train"][1]["output"] != ccw["train"][1]["output"]
    assert proto.teaching_certificate(cw)["survivors"] == [{"magenta_rotation": "cw"}]
    assert proto.teaching_certificate(ccw)["survivors"] == [{"magenta_rotation": "ccw"}]
    assert public_challenge_bytes(cw)
    assert public_challenge_id(cw) == public_challenge_id(deepcopy(cw))
    assert proto.visible_turn(cw, 0) == public_challenge_bytes(one)


def test_four_queries_include_substantive_30_by_30_and_setting_witness():
    adapter = load()
    cw = adapter.generate(91, {"magenta_rotation": "cw"}, 3, 4)
    ccw = adapter.generate(91, {"magenta_rotation": "ccw"}, 3, 4)
    big = cw["test"][-1]
    assert (len(big["input"]), len(big["input"][0])) == (30, 30)
    cyan = {(r, c) for r, row in enumerate(big["output"]) for c, value in enumerate(row) if value == 8}
    assert len(cyan) >= 20
    assert max(r for r, _ in cyan) - min(r for r, _ in cyan) >= 15
    assert max(c for _, c in cyan) - min(c for _, c in cyan) >= 15
    assert any(a["output"] != b["output"] for a, b in zip(cw["test"], ccw["test"]))


def test_default_program_and_python_mirror_cover_all_canonical_pairs():
    from reviewer_support import load_selected_generator

    adapter = load()
    generator = load_selected_generator("d336f5fb2da4", root=ROOT)[0]
    assert adapter.program({"magenta_rotation": "cw"})
    for pair in canonical_pairs("d336f5fb2da4", root=ROOT, labeled_only=True):
        assert generator.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("changes", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"settings": {}}, {"settings": {"magenta_rotation": "half"}},
    {"settings": {"magenta_rotation": "cw", "extra": 1}},
    {"demos": 1}, {"demos": 7}, {"queries": 0}, {"queries": 5},
])
def test_invalid_controls_are_rejected(changes):
    adapter = load()
    kwargs = dict(seed=17, settings={"magenta_rotation": "cw"}, demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises(ValueError):
        adapter.generate(**kwargs)

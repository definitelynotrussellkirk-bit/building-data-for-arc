"""Parametric edge-versus-bounded diagonal-ray family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
from reviewer_support import find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTO = HOME / "workspace" / "parametric"
SETTINGS = ({"extent": "edge"}, {"extent": "two_steps"})


def load_adapter():
    path = PROTO / "adapter.py"
    assert path.is_file(), "the requested parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("tested_e0ef_parametric_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_and_alternate_is_behaviorally_distinct():
    adapter = load_adapter()
    variants = Catalog(ROOT)._variants()["e0ef0cfeaf88"]
    authority = {variant["program_solution"] for variant in variants}.pop()
    assert adapter.program(SETTINGS[0]) == authority
    assert adapter.program(SETTINGS[1]) != authority

    episode = adapter.generate(0, SETTINGS[0], demos=2, queries=1)
    grid = episode["train"][0]["input"]
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        edge = apply(adapter.program(SETTINGS[0]), grid)
        bounded = apply(adapter.program(SETTINGS[1]), grid)
    finally:
        bridge.close()
    assert edge == episode["train"][0]["output"]
    assert edge != bounded


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_distinctness_and_30x30_boundary_stress(demos):
    adapter = load_adapter()
    edge = adapter.generate(17, SETTINGS[0], demos=demos, queries=4)
    bounded = adapter.generate(17, SETTINGS[1], demos=demos, queries=4)
    one = adapter.generate(17, SETTINGS[0], demos=demos, queries=1)

    assert len(edge["train"]) == demos and len(edge["test"]) == 4
    assert edge["train"] == one["train"]
    assert edge["test"][:1] == one["test"]
    left_inputs = [pair["input"] for split in ("train", "test") for pair in edge[split]]
    right_inputs = [pair["input"] for split in ("train", "test") for pair in bounded[split]]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == demos + 4
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(edge[split], bounded[split], strict=True)
    )
    public_challenge_bytes(edge)

    pair = edge["test"][-1]
    large, output = pair["input"], pair["output"]
    assert len(large) == len(large[0]) == 30
    assert sum(cell != 0 for row in large for cell in row) == 8
    assert any(output[0]) and any(output[-1])
    assert any(row[0] for row in output) and any(row[-1] for row in output)
    assert sum(cell != 0 for row in output for cell in row) >= 50


def test_every_sample_leaves_more_than_two_steps_for_at_least_one_tail():
    adapter = load_adapter()
    edge = adapter.generate(0, SETTINGS[0], demos=6, queries=4)
    bounded = adapter.generate(0, SETTINGS[1], demos=6, queries=4)
    for split in ("train", "test"):
        for a, b in zip(edge[split], bounded[split], strict=True):
            assert a["input"] == b["input"]
            assert a["output"] != b["output"]
            assert sum(x != y for ar, br in zip(a["output"], b["output"], strict=True)
                       for x, y in zip(ar, br, strict=True)) >= 1


def test_protected_racket_labels_and_demo_only_identification():
    load_adapter()
    contract = json.loads((PROTO / "promotion.json").read_text())
    jobs = [
        dict(seed=seed, settings=settings, demos=demos, queries=4)
        for seed, demos in ((0, 2), (17, 6))
        for settings in SETTINGS
    ]
    result = evaluate_contract(ROOT, "e0ef0cfeaf88", contract, jobs)
    assert result["racket"]["protected"] is True
    assert [check["survivors"] for check in result["checks"]] == [
        [job["settings"]] for job in jobs
    ]
    assert [check["label_count"] for check in result["checks"]] == [
        job["demos"] + 4 for job in jobs
    ]


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
        {"settings": {}}, {"settings": {"extent": True}},
        {"settings": {"extent": "three_steps"}},
        {"settings": {"extent": "edge", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_before_generation(patch):
    request = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    request.update(patch)
    with pytest.raises(ValueError):
        load_adapter().generate(**request)

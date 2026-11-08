"""Proposed cardinal/diagonal completion family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
from reviewer_support import find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTO = HOME / "workspace" / "parametric"
SETTINGS = ({"footprint": "cardinal"}, {"footprint": "diagonal"})


def load_adapter():
    path = PROTO / "adapter.py"
    assert path.is_file(), "the requested parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("tested_1314_parametric_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_and_both_rules_execute_differently():
    adapter = load_adapter()
    authority = json.loads(
        (ROOT / "shared/data/base/solutions/training/14754a24__1314f4ccf5cc.json").read_text()
    )["racket_target"]["target_code"]
    assert adapter.program({"footprint": "cardinal"}) == authority
    assert adapter.program({"footprint": "diagonal"}) != authority

    episode = adapter.generate(0, {"footprint": "cardinal"}, demos=2, queries=1)
    grid = episode["train"][0]["input"]
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        cardinal = apply(adapter.program(SETTINGS[0]), grid)
        diagonal = apply(adapter.program(SETTINGS[1]), grid)
    finally:
        bridge.close()
    assert cardinal == episode["train"][0]["output"]
    assert cardinal != diagonal


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_distinctness_and_large_query(demos):
    adapter = load_adapter()
    cardinal = adapter.generate(17, SETTINGS[0], demos=demos, queries=4)
    diagonal = adapter.generate(17, SETTINGS[1], demos=demos, queries=4)
    one = adapter.generate(17, SETTINGS[0], demos=demos, queries=1)

    assert len(cardinal["train"]) == demos and len(cardinal["test"]) == 4
    assert cardinal["train"] == one["train"]
    assert cardinal["test"][:1] == one["test"]
    left_inputs = [pair["input"] for split in ("train", "test") for pair in cardinal[split]]
    right_inputs = [pair["input"] for split in ("train", "test") for pair in diagonal[split]]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == demos + 4
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(cardinal[split], diagonal[split], strict=True)
    )
    public_challenge_bytes(cardinal)

    large = cardinal["test"][-1]["input"]
    assert len(large) == len(large[0]) == 30
    nonzero = sum(cell != 0 for row in large for cell in row)
    assert nonzero >= 180
    quadrants = [
        any(large[r][c] for r in rs for c in cs)
        for rs, cs in (
            (range(0, 15), range(0, 15)),
            (range(0, 15), range(15, 30)),
            (range(15, 30), range(0, 15)),
            (range(15, 30), range(15, 30)),
        )
    ]
    assert all(quadrants)


def test_sampler_reserves_boundary_frame_against_clipped_rivals():
    episode = load_adapter().generate(0, SETTINGS[0], demos=2, queries=4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        h, w = len(grid), len(grid[0])
        yellow = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4]
        assert yellow
        assert all(0 < r < h - 1 and 0 < c < w - 1 for r, c in yellow)


def test_protected_racket_labels_and_demo_only_identification():
    load_adapter()
    contract = json.loads((PROTO / "promotion.json").read_text())
    jobs = [
        dict(seed=seed, settings=settings, demos=demos, queries=4)
        for seed, demos in ((0, 2), (17, 6))
        for settings in SETTINGS
    ]
    result = evaluate_contract(ROOT, "1314f4ccf5cc", contract, jobs)
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
        {"settings": {}}, {"settings": {"footprint": True}},
        {"settings": {"footprint": "square"}},
        {"settings": {"footprint": "cardinal", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_before_generation(patch):
    request = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    request.update(patch)
    with pytest.raises(ValueError):
        load_adapter().generate(**request)

"""Parametric transpose-versus-clockwise object-packing family."""
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
SETTINGS = ({"transform": "transpose"}, {"transform": "rotate_cw"})


def load_adapter():
    path = PROTO / "adapter.py"
    assert path.is_file(), "the requested parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("tested_d4be_parametric_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_and_alternate_executes_differently():
    adapter = load_adapter()
    variants = Catalog(ROOT)._variants()["d4be41674012"]
    authority = {variant["program_solution"] for variant in variants}.pop()
    assert adapter.program(SETTINGS[0]) == authority
    assert adapter.program(SETTINGS[1]) != authority

    episode = adapter.generate(0, SETTINGS[0], demos=2, queries=1)
    grid = episode["train"][0]["input"]
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        assert identity["backend"] == "racket" and identity["protected"] is True
        transposed = apply(adapter.program(SETTINGS[0]), grid)
        rotated = apply(adapter.program(SETTINGS[1]), grid)
    finally:
        bridge.close()
    assert transposed == episode["train"][0]["output"]
    assert transposed != rotated


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_distinctness_and_large_spread(demos):
    adapter = load_adapter()
    transposed = adapter.generate(17, SETTINGS[0], demos=demos, queries=4)
    rotated = adapter.generate(17, SETTINGS[1], demos=demos, queries=4)
    one = adapter.generate(17, SETTINGS[0], demos=demos, queries=1)

    assert len(transposed["train"]) == demos and len(transposed["test"]) == 4
    assert transposed["train"] == one["train"]
    assert transposed["test"][:1] == one["test"]
    left_inputs = [pair["input"] for split in ("train", "test") for pair in transposed[split]]
    right_inputs = [pair["input"] for split in ("train", "test") for pair in rotated[split]]
    assert left_inputs == right_inputs
    assert len({json.dumps(grid, separators=(",", ":")) for grid in left_inputs}) == demos + 4
    assert all(
        a["output"] != b["output"]
        for split in ("train", "test")
        for a, b in zip(transposed[split], rotated[split], strict=True)
    )
    public_challenge_bytes(transposed)

    large = transposed["test"][-1]["input"]
    assert len(large) == len(large[0]) == 30
    occupied = [(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value]
    assert len(occupied) >= 20
    assert min(r for r, _ in occupied) <= 4 and max(r for r, _ in occupied) >= 24
    assert min(c for _, c in occupied) <= 3 and max(c for _, c in occupied) >= 25


def test_every_retained_object_scene_teaches_transform_not_order_or_palette():
    adapter = load_adapter()
    transposed = adapter.generate(3, SETTINGS[0], demos=6, queries=4)
    rotated = adapter.generate(3, SETTINGS[1], demos=6, queries=4)
    for split in ("train", "test"):
        for a, b in zip(transposed[split], rotated[split], strict=True):
            assert a["input"] == b["input"]
            assert a["output"] != b["output"]
            assert len(a["output"]) == len(b["output"])
            assert len(a["output"][0]) == len(b["output"][0])


def test_protected_racket_labels_and_demo_only_identification():
    load_adapter()
    contract = json.loads((PROTO / "promotion.json").read_text())
    jobs = [
        dict(seed=seed, settings=settings, demos=demos, queries=4)
        for seed, demos in ((0, 2), (17, 6))
        for settings in SETTINGS
    ]
    result = evaluate_contract(ROOT, "d4be41674012", contract, jobs)
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
        {"settings": {}}, {"settings": {"transform": True}},
        {"settings": {"transform": "flip"}},
        {"settings": {"transform": "transpose", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_before_generation(patch):
    request = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    request.update(patch)
    with pytest.raises(ValueError):
        load_adapter().generate(**request)

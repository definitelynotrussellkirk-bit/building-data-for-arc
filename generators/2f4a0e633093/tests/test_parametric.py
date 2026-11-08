"""Native area-ranked gallery family for 2f4a0e633093."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes

TASK = "2f4a0e633093"
HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace" / "parametric"
ROOT = find_root(__file__)
SETTINGS = ({"layout": "fixed_panels"}, {"layout": "area_ranked"})


def load(name="adapter"):
    path = PROTO / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"tested_2f4_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_authority():
    from arcpuzzles import Catalog

    adapter = load()
    programs = {row["program_solution"] for row in Catalog(ROOT).get(TASK)["variants"]}
    assert programs == {adapter.program(SETTINGS[0])}
    assert adapter.program(SETTINGS[1]) != adapter.program(SETTINGS[0])


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_matched_inputs_prefix_and_setting_identification(demos):
    adapter = load()
    fixed = adapter.generate(17, SETTINGS[0], demos, 4)
    ranked = adapter.generate(17, SETTINGS[1], demos, 4)
    one = adapter.generate(17, SETTINGS[1], demos, 1)
    assert len(fixed["train"]) == demos and len(fixed["test"]) == 4
    assert fixed["train"] == adapter.generate(17, SETTINGS[0], demos, 1)["train"]
    assert one["train"] == ranked["train"] and one["test"] == ranked["test"][:1]
    assert _inputs(fixed) == _inputs(ranked)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(fixed)}) == demos + 4
    assert all(a["output"] != b["output"] for a, b in zip(fixed["train"], ranked["train"]))
    assert public_challenge_bytes(one) == public_challenge_bytes(
        {"train": ranked["train"], "test": ranked["test"][:1]}
    )


def test_area_order_intermediate_controls_gallery_rows():
    family = load("family")
    pair = load().generate(5, SETTINGS[1], 3, 4)["train"][0]
    info = family.analyze(pair["input"])
    assert info["areas"] == sorted(info["areas"])
    correct = family.apply(pair["input"], SETTINGS[1])
    wrong = family.area_ranked_output(pair["input"], permutation=(2, 1, 0))
    assert correct == pair["output"]
    assert wrong != correct


def test_four_queries_include_substantive_30_by_30_dynamic_gallery():
    episode = load().generate(91, SETTINGS[1], 3, 4)
    big = next(pair for pair in episode["test"] if len(pair["input"]) == 30)
    assert (len(big["input"]), len(big["input"][0])) == (30, 30)
    assert sum(value != 0 for row in big["input"] for value in row) >= 85
    assert 20 <= len(big["output"]) <= 30
    assert 20 <= len(big["output"][0]) <= 30
    assert big["output"] != load("family").apply(big["input"], SETTINGS[0])


def test_public_bytes_ignore_private_fields_and_future_queries():
    episode = load().generate(33, SETTINGS[1], 3, 4)
    visible = {"train": episode["train"], "test": episode["test"][:1]}
    changed = deepcopy(episode)
    changed["settings"] = {"layout": "private"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"] = changed["test"][:1]
    assert public_challenge_bytes(changed) == public_challenge_bytes(visible)


@pytest.mark.parametrize("changes", [
    {"seed": True}, {"seed": -1}, {"settings": {}},
    {"settings": {"layout": "unknown"}}, {"settings": {"layout": "fixed_panels", "x": 1}},
    {"demos": 1}, {"demos": 7}, {"queries": 0}, {"queries": 5},
])
def test_invalid_requests_are_rejected(changes):
    kwargs = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises((TypeError, ValueError)):
        load().generate(**kwargs)


def test_bounded_audit_covers_all_counts_and_has_no_failures():
    report = load("audit").audit(seed_count=3)
    assert report["status"] == "passed"
    assert report["jobs"] == 15
    assert report["failures"] == []
    assert report["distinct_permutations"] >= 2
    assert report["rival_checks"]["constant_order_rejected"] == report["jobs"]
    assert report["rival_checks"]["bbox_area_order_rejected"] == report["jobs"]
    assert report["rival_checks"]["source_order_rejected"] == report["sampled_grids"]

"""Native transformed-accent ordering family for d1c500f060a1."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes

TASK = "d1c500f060a1"
HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace" / "parametric"
ROOT = find_root(__file__)
SETTINGS = ({"pack_order": "as_found"}, {"pack_order": "accent_scan"})


def load(name="adapter"):
    path = PROTO / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"tested_d1c_{name}", path)
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
    found = adapter.generate(17, SETTINGS[0], demos, 4)
    sorted_episode = adapter.generate(17, SETTINGS[1], demos, 4)
    one = adapter.generate(17, SETTINGS[1], demos, 1)
    assert len(found["train"]) == demos and len(found["test"]) == 4
    assert one["train"] == sorted_episode["train"] and one["test"] == sorted_episode["test"][:1]
    assert _inputs(found) == _inputs(sorted_episode)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(found)}) == demos + 4
    assert any(a["output"] != b["output"] for a, b in zip(found["train"], sorted_episode["train"]))
    assert public_challenge_bytes(one) == public_challenge_bytes(
        {"train": sorted_episode["train"], "test": sorted_episode["test"][:1]})


def test_transformed_accent_keys_drive_the_second_stage_order():
    family = load("family")
    episode = load().generate(5, SETTINGS[1], 3, 4)
    pair = episode["train"][0]
    info = family.analyze(pair["input"])
    keys = family.transformed_keys(info)
    assert len(keys) == len(set(keys)) >= 4
    assert tuple(range(len(keys))) != tuple(sorted(range(len(keys)), key=keys.__getitem__))
    correct = family.apply(pair["input"], SETTINGS[1])
    wrong = family.apply(pair["input"], SETTINGS[0])
    assert correct == pair["output"]
    assert wrong != correct


def test_four_queries_include_substantive_30_by_30_case():
    adapter = load()
    episode = adapter.generate(91, SETTINGS[1], 3, 4)
    big = next(pair for pair in episode["test"] if len(pair["input"]) == 30
               and len(pair["input"][0]) == 30)
    assert len(big["output"]) <= 30 and len(big["output"][0]) <= 30
    assert sum(value != 0 for row in big["output"] for value in row) >= 60
    assert big["output"] != load("family").apply(big["input"], SETTINGS[0])


def test_public_bytes_ignore_private_fields_and_future_queries():
    adapter = load()
    episode = adapter.generate(33, SETTINGS[1], 3, 4)
    visible = {"train": episode["train"], "test": episode["test"][:1]}
    changed = deepcopy(episode)
    changed["settings"] = {"pack_order": "private"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"] = changed["test"][:1]
    assert public_challenge_bytes(changed) == public_challenge_bytes(visible)


@pytest.mark.parametrize("changes", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"settings": {}}, {"settings": {"pack_order": "width"}},
    {"settings": {"pack_order": "as_found", "extra": 1}},
    {"demos": 1}, {"demos": 7}, {"queries": 0}, {"queries": 5},
])
def test_invalid_requests_are_rejected(changes):
    adapter = load()
    kwargs = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**kwargs)

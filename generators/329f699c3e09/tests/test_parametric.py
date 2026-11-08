"""Native reflected-probe route family for 329f699c3e09."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, public_challenge_bytes

TASK = "329f699c3e09"
HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace" / "parametric"
ROOT = find_root(__file__)
SETTINGS = ({"mode": "paint_reflections"}, {"mode": "probe_first_hit"})


def load(name="adapter"):
    path = PROTO / f"{name}.py"
    assert path.is_file(), f"missing parametric {name}.py"
    spec = importlib.util.spec_from_file_location(f"tested_329_{name}", path)
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
    canonical = adapter.generate(17, SETTINGS[0], demos, 4)
    routed = adapter.generate(17, SETTINGS[1], demos, 4)
    one = adapter.generate(17, SETTINGS[1], demos, 1)
    assert len(canonical["train"]) == demos and len(canonical["test"]) == 4
    assert canonical["train"] == adapter.generate(17, SETTINGS[0], demos, 1)["train"]
    assert one["train"] == routed["train"] and one["test"] == routed["test"][:1]
    assert _inputs(canonical) == _inputs(routed)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == demos + 4
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], routed["train"]))
    assert public_challenge_bytes(one) == public_challenge_bytes(
        {"train": routed["train"], "test": routed["test"][:1]}
    )


def test_reflected_probe_intermediate_controls_first_hit_stage():
    family = load("family")
    episode = load().generate(5, SETTINGS[1], 3, 4)
    pair = episode["train"][0]
    info = family.analyze(pair["input"])
    assert info["probes"] and info["target_colors"]
    correct = family.apply(pair["input"], SETTINGS[1])
    wrong = family.apply_with_route(pair["input"], use_reflected_probes=False)
    assert correct == pair["output"]
    assert wrong != correct
    assert set(info["target_colors"]).isdisjoint(info["source_side_colors"])


def test_four_queries_include_substantive_30_by_30_case():
    adapter = load()
    episode = adapter.generate(91, SETTINGS[1], 3, 4)
    big = next(pair for pair in episode["test"] if len(pair["input"]) == 30)
    assert (len(big["input"]), len(big["input"][0])) == (30, 30)
    assert sum(value != 0 for row in big["input"] for value in row) >= 75
    assert sum(value == 8 for row in big["output"] for value in row) >= 25
    assert big["output"] != load("family").apply(big["input"], SETTINGS[0])


def test_public_bytes_ignore_private_fields_and_future_queries():
    episode = load().generate(33, SETTINGS[1], 3, 4)
    visible = {"train": episode["train"], "test": episode["test"][:1]}
    changed = deepcopy(episode)
    changed["settings"] = {"mode": "private"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"] = changed["test"][:1]
    assert public_challenge_bytes(changed) == public_challenge_bytes(visible)


@pytest.mark.parametrize("changes", [
    {"seed": True}, {"seed": -1}, {"settings": {}},
    {"settings": {"mode": "unknown"}}, {"settings": {"mode": "paint_reflections", "x": 1}},
    {"demos": 1}, {"demos": 7}, {"queries": 0}, {"queries": 5},
])
def test_invalid_requests_are_rejected(changes):
    kwargs = dict(seed=17, settings=SETTINGS[0], demos=3, queries=4)
    kwargs.update(changes)
    with pytest.raises((TypeError, ValueError)):
        load().generate(**kwargs)


def _side_of(info, r, c):
    coordinate = r if info["axis"] == "row" else c
    return -1 if coordinate < info["divider"] else 1


def test_sampler_defeats_far_side_and_hit_object_only_shortcuts():
    family = load("family")
    episode = load().generate(42, SETTINGS[1], 2, 4)
    for pair in episode["train"] + episode["test"]:
        grid, output = pair["input"], pair["output"]
        info = family.analyze(grid)
        source_side = _side_of(info, *info["sources"][0])
        probe_side = _side_of(info, *info["probes"][0])
        assert source_side == -probe_side
        # A selected color is cloned on the source side, proving that the rule
        # selects a color by the ray and then applies that color globally.
        assert any(
            value in info["target_colors"]
            and _side_of(info, r, c) == source_side
            and output[r][c] == 8
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
        )
        # A substantial non-hit object exists on the probe side and is preserved,
        # defeating the shortcut "recolor everything opposite the sources."
        assert any(
            value not in (0, 6, 7, 8)
            and value not in info["target_colors"]
            and _side_of(info, r, c) == probe_side
            and output[r][c] == value
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
        )


def test_bounded_audit_covers_all_counts_and_has_no_failures():
    report = load("audit").audit(seed_count=3)
    assert report["status"] == "passed"
    assert report["jobs"] == 15
    assert report["failures"] == []
    assert report["rival_checks"]["far_side_all_rejected"] == report["sampled_grids"]
    assert report["rival_checks"]["hit_side_only_rejected"] == report["sampled_grids"]

"""Focused behavior tests for the separately proposed parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def _adapter():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "The parametric family has no native adapter yet"
    spec = importlib.util.spec_from_file_location("_test_a0444de97675_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_is_exact_canonical_and_scale_changes_output():
    from reviewer_support import canonical_path, find_root
    adapter = _adapter()
    rows = [json.loads(line) for line in canonical_path(find_root(__file__)).open()]
    canonical = next(row for row in rows if row["task_id"] == "a0444de97675")
    assert adapter.program({"scale": 2}) == canonical["program_solution"]
    for pair in canonical["train"] + canonical["test"]:
        if "output" in pair:
            assert adapter.prototype.solve(pair["input"], 2) == pair["output"]
    episodes = [adapter.generate(17, {"scale": scale}, 2, 4) for scale in (1, 2, 3)]
    for split in ("train", "test"):
        assert [[p["input"] for p in ep[split]] for ep in episodes].count(
            [p["input"] for p in episodes[0][split]]) == 3
        base = episodes[0][split][0]["output"]
        for scale, episode in zip((1, 2, 3), episodes):
            out = episode[split][0]["output"]
            assert len(out) == scale * len(base)
            assert len(out[0]) == scale * len(base[0])


@pytest.mark.parametrize("demos", range(2, 7))
def test_independent_counts_novel_queries_and_two_demo_teaching(demos):
    adapter = _adapter()
    for scale in (1, 2, 3):
        ep = adapter.generate(91, {"scale": scale}, demos, 4)
        assert len(ep["train"]) == demos and len(ep["test"]) == 4
        pairs = ep["train"] + ep["test"]
        assert len({json.dumps(p["input"]) for p in pairs}) == demos + 4
        assert adapter.prototype.teaching_check(ep["train"], ep["test"], scale)["ambiguities"] == []
        for pair in pairs:
            assert 1 <= len(pair["output"]) <= 30
            assert 1 <= len(pair["output"][0]) <= 30


def test_public_first_turn_has_no_private_or_future_content():
    from reviewer_support import public_challenge_bytes, public_challenge_id
    adapter = _adapter()
    full = adapter.generate(123, {"scale": 3}, 3, 4)
    single = adapter.generate(123, {"scale": 3}, 3, 1)
    first = {"train": full["train"], "test": full["test"][:1]}
    assert public_challenge_bytes(first) == public_challenge_bytes(single)
    visible = json.loads(public_challenge_bytes(first))
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
    mutated = copy.deepcopy(first)
    mutated.update(settings={"scale": 99}, seed=-1, program_solution="secret")
    mutated["test"][0]["output"] = [[9]]
    assert public_challenge_id(mutated) == public_challenge_id(first)
    more_demos = adapter.generate(123, {"scale": 3}, 6, 4)
    assert full["train"] == more_demos["train"][:3]
    assert full["test"] == more_demos["test"]


def test_size_boundaries_have_content_and_preserve_original_crop():
    proto = _adapter().prototype
    for height, width in ((8, 9), (30, 30), (8, 30), (30, 9)):
        grid = proto.sample_scene(2026, 0, height=height, width=width)
        assert (len(grid), len(grid[0])) == (height, width)
        original = copy.deepcopy(grid)
        info = proto.inspect_scene(grid)
        assert info["area_matches"] == 1
        assert info["body_objects"] >= 5
        assert info["target_has_foreign_crop_cell"]
        assert proto.solve(grid, 2) != proto.rival_output(grid, 2, "isolated_object")
        assert grid == original
        if (height, width) == (30, 30):
            assert info["body_objects"] >= 10
            assert info["occupied_body_cells"] >= 90
            assert info["occupied_row_span"] >= 25
            assert info["occupied_col_span"] >= 25


def test_two_demos_refute_multicolor_group_and_fixed_area_rank_shortcuts():
    adapter = _adapter()
    proto = adapter.prototype

    def group_rival(grid):
        monochrome = proto.objects(grid)
        groups = [group for group in proto.objects(grid, color_sensitive=False)
                  if len({grid[r][c] for r, c in group}) > 1]
        group = set(max(groups, key=len))
        obj = max((obj for obj in monochrome if set(obj) <= group), key=len)
        return proto._crop(grid, obj, 2)

    for seed in (0, 17):
        ep = adapter.generate(seed, {"scale": 2}, 2, 4)
        assert any(group_rival(pair["input"]) != pair["output"] for pair in ep["train"])
        for rank in (2, 3):
            predictions = [proto._crop(pair["input"], sorted(proto.objects(pair["input"]),
                           key=lambda obj: (-len(obj), proto.bbox(obj)))[rank - 1], 2)
                           for pair in ep["train"]]
            assert any(output != pair["output"] for output, pair in zip(predictions, ep["train"]))


@pytest.mark.parametrize("settings", ({}, {"scale": True}, {"scale": 2.0}, {"scale": 0}, {"scale": 4}, {"scale": 2, "extra": 1}))
def test_settings_reject_invalid_or_undeclared_values(settings):
    with pytest.raises((TypeError, ValueError)):
        _adapter().generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed,demos,queries", ((True, 3, 4), (-1, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, 4.0)))
def test_request_bounds_are_strict(seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        _adapter().generate(seed, {"scale": 2}, demos, queries)

"""Focused regressions for the native anchor/offset stamping family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "71d5c4ac6ea3"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
GENERATOR_PATH = HOME / "generator.py"
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load(GENERATOR_PATH, "_test_71d_base")


@pytest.fixture(scope="module")
def proto():
    return _load(PROTOTYPE_PATH, "_test_71d_parametric")


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _anchor(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    assert len(points) == 1
    return points[0]


def test_base_rule_hash_exact_axes_and_anchor_variation(generator):
    assert generator.RULE_HASH == "ed3afc80127d"
    assert set(generator.AXES) == {"grid_h", "grid_w", "n_seeds", "n_offsets", "texture"}
    for texture in ("plain", "wide_offsets", "edge_seeds"):
        for n_offsets, n_seeds in ((2, 1), (5, 4)):
            grid = generator.generate(
                13,
                41 + n_offsets + n_seeds,
                difficulty="easy",
                grid_h=14,
                grid_w=14,
                n_offsets=n_offsets,
                n_seeds=n_seeds,
                texture=texture,
            )
            assert generator.observe_overrides(grid) == {
                "grid_h": 14,
                "grid_w": 14,
                "n_offsets": n_offsets,
                "n_seeds": n_seeds,
            }
            assert generator.self_check(
                grid,
                meta={"overrides": {"grid_h": 14, "grid_w": 14, "n_offsets": n_offsets, "n_seeds": n_seeds}},
            ) == []
    anchors = [_anchor(generator.generate(2, index, difficulty="easy")) for index in (49, 50, 51)]
    assert len(set(anchors)) >= 2


def test_base_rejects_unknown_and_incompatible_overrides(generator):
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, misspelled_axis=3)
    with pytest.raises(ValueError, match="n_offsets.*no_offsets|no_offsets.*n_offsets"):
        generator.generate(0, 0, texture="no_offsets", n_offsets=2)
    with pytest.raises(ValueError, match="n_seeds.*no_seeds|no_seeds.*n_seeds"):
        generator.generate(0, 0, texture="no_seeds", n_seeds=1)


def test_default_program_is_exact_canonical_and_alternative_rotates_offsets(proto):
    canonical = _canonical_program()
    assert proto.program({"offset_mode": "as_drawn"}) == canonical
    alternative = proto.program({"offset_mode": "rotate_cw"})
    assert alternative != canonical
    assert "rotate-offset" in alternative
    assert "stamp-offsets" in alternative


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_anchor_teaching_and_30x30_stress(proto, demos):
    canonical = proto.generate(17, {"offset_mode": "as_drawn"}, demos=demos, queries=4)
    rotated = proto.generate(17, {"offset_mode": "rotate_cw"}, demos=demos, queries=4)
    assert len(canonical["train"]) == len(rotated["train"]) == demos
    assert len(canonical["test"]) == len(rotated["test"]) == 4
    assert _inputs(canonical) == _inputs(rotated)
    assert len({proto.digest(grid) for grid in _inputs(canonical)}) == demos + 4
    assert len({_anchor(pair["input"]) for pair in canonical["train"]}) >= 2
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], rotated["train"]))
    stress = canonical["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    analysis = proto.analyze_input(stress)
    assert analysis["offset_count"] >= 7
    assert analysis["seed_count"] >= 5
    assert analysis["content_bbox_height"] >= 24
    assert analysis["content_bbox_width"] >= 24
    assert canonical["certificate"]["survivors"] == [{"offset_mode": "as_drawn"}]
    assert rotated["certificate"]["survivors"] == [{"offset_mode": "rotate_cw"}]


def test_real_racket_labels_and_demo_only_identification(proto):
    with RacketBridge(timeout=60) as bridge:
        for mode in ("as_drawn", "rotate_cw"):
            episode = proto.generate(23, {"offset_mode": mode}, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert proto.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]
            certificate = proto.certify(
                episode,
                execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge),
            )
            assert certificate["fit_scope"] == "demonstrations_only"
            assert certificate["survivors"] == [{"offset_mode": mode}]
            assert all(row["label_matches"] for row in certificate["queries"])


def test_fixed_origin_absolute_and_reflection_shortcuts_are_refuted(proto):
    episode = proto.generate(29, {"offset_mode": "rotate_cw"}, demos=3, queries=4)
    fixed_origin = _anchor(episode["train"][0]["input"])
    assert any(
        proto.fixed_origin_rival(pair["input"], fixed_origin, {"offset_mode": "rotate_cw"}) != pair["output"]
        for pair in episode["train"][1:]
    )
    assert any(proto.absolute_position_rival(pair["input"]) != pair["output"] for pair in episode["train"])
    assert any(proto.reflect_offsets_rival(pair["input"]) != pair["output"] for pair in episode["train"])


def test_first_query_prefix_and_public_projection_ignore_private_fields(proto):
    one = proto.generate(31, {"offset_mode": "as_drawn"}, demos=2, queries=1)
    many = proto.generate(31, {"offset_mode": "as_drawn"}, demos=6, queries=4)
    assert one["test"] == many["test"][:1]
    before = public_challenge_bytes(one)
    changed = copy.deepcopy(one)
    changed["settings"] = {"offset_mode": "rotate_cw"}
    changed["program_solution"] = proto.program(changed["settings"])
    changed["test"][0]["output"] = [[9]]
    changed["certificate"] = {"forged": True}
    assert public_challenge_bytes(changed) == before
    assert public_challenge_id(changed) == public_challenge_id(one)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": -1, "settings": {"offset_mode": "as_drawn"}, "demos": 3, "queries": 4},
        {"seed": True, "settings": {"offset_mode": "as_drawn"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"offset_mode": "unknown"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"offset_mode": "as_drawn"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"offset_mode": "as_drawn"}, "demos": 7, "queries": 4},
        {"seed": 0, "settings": {"offset_mode": "as_drawn"}, "demos": 3, "queries": 0},
        {"seed": 0, "settings": {"offset_mode": "as_drawn"}, "demos": 3, "queries": 5},
    ],
)
def test_invalid_requests_fail_closed(proto, kwargs):
    with pytest.raises(ValueError):
        proto.generate(**kwargs)


def test_corrupt_labels_and_duplicate_inputs_fail_closed(proto):
    episode = proto.generate(37, {"offset_mode": "rotate_cw"}, demos=3, queries=4)
    corrupt = copy.deepcopy(episode)
    corrupt["train"][0]["output"][0][0] = (corrupt["train"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label"):
        proto.certify(corrupt)
    duplicate = copy.deepcopy(episode)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(duplicate)

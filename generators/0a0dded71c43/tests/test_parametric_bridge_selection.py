"""Focused regressions for the native bridge-selection family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "0a0dded71c43"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
GENERATOR_PATH = HOME / "generator.py"


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
    return _load(GENERATOR_PATH, "_test_0a_base")


@pytest.fixture(scope="module")
def proto():
    return _load(PROTOTYPE_PATH, "_test_0a_parametric")


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_base_rule_hash_and_declared_degenerate_self_check(generator):
    assert generator.RULE_HASH == "c9b982c51cbf"
    grid = generator.generate(91, 0, texture="no_gaps")
    assert generator.self_check(grid, meta={"texture": "no_gaps"}) == []


def test_default_program_is_exact_canonical_and_alternative_is_composed(proto):
    canonical = _canonical_program()
    assert proto.program({"mode": "fill_only"}) == canonical
    alternative = proto.program({"mode": "select_most_bridges"})
    assert alternative != canonical
    assert "components67" in alternative
    assert "bridge-count" in alternative
    assert "argmax" in alternative


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_teaching_and_30x30_stress(proto, demos):
    canonical = proto.generate(17, {"mode": "fill_only"}, demos=demos, queries=4)
    composed = proto.generate(17, {"mode": "select_most_bridges"}, demos=demos, queries=4)
    assert len(canonical["train"]) == len(composed["train"]) == demos
    assert len(canonical["test"]) == len(composed["test"]) == 4
    assert _inputs(canonical) == _inputs(composed)
    assert len({proto.digest(grid) for grid in _inputs(canonical)}) == demos + 4
    stress = canonical["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    analysis = proto.analyze_input(stress)
    assert analysis["component_count"] >= 5
    assert analysis["bridge_count"] >= 15
    assert analysis["bbox_height"] >= 24
    assert analysis["bbox_width"] >= 20
    assert analysis["winner_bridge_count"] > 0
    assert analysis["largest_component_is_winner"] is False
    assert canonical["certificate"]["survivors"] == [{"mode": "fill_only"}]
    assert composed["certificate"]["survivors"] == [{"mode": "select_most_bridges"}]
    assert any(a["output"] != b["output"] for a, b in zip(canonical["train"], composed["train"]))
    winners = [proto.analyze_input(pair["input"])["winner_bbox"] for pair in composed["train"]]
    assert len(set(map(tuple, winners))) >= min(2, demos)


def test_real_racket_labels_and_demo_only_identification(proto):
    with RacketBridge(timeout=60) as bridge:
        for mode in ("fill_only", "select_most_bridges"):
            episode = proto.generate(23, {"mode": mode}, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert proto.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]
            certificate = proto.certify(
                episode,
                execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge),
            )
            assert certificate["fit_scope"] == "demonstrations_only"
            assert certificate["survivors"] == [{"mode": mode}]
            assert all(row["label_matches"] for row in certificate["queries"])


def test_largest_component_and_fixed_location_shortcuts_are_refuted(proto):
    episode = proto.generate(29, {"mode": "select_most_bridges"}, demos=3, queries=4)
    assert any(
        proto.largest_component_rival(pair["input"]) != pair["output"]
        for pair in episode["train"]
    )
    anchor = proto.analyze_input(episode["train"][0]["input"])["winner_bbox"]
    assert any(
        proto.fixed_location_rival(pair["input"], anchor) != pair["output"]
        for pair in episode["train"][1:]
    )
    assert proto.skip_a_rival(episode["test"][0]["input"]) != episode["test"][0]["output"]


def test_first_query_prefix_and_public_projection_ignore_private_fields(proto):
    one = proto.generate(31, {"mode": "fill_only"}, demos=2, queries=1)
    many = proto.generate(31, {"mode": "fill_only"}, demos=6, queries=4)
    assert one["test"] == many["test"][:1]
    before = public_challenge_bytes(one)
    changed = copy.deepcopy(one)
    changed["settings"] = {"mode": "select_most_bridges"}
    changed["program_solution"] = proto.program(changed["settings"])
    changed["test"][0]["output"] = [[9]]
    changed["certificate"] = {"forged": True}
    assert public_challenge_bytes(changed) == before
    assert public_challenge_id(changed) == public_challenge_id(one)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": -1, "settings": {"mode": "fill_only"}, "demos": 3, "queries": 4},
        {"seed": True, "settings": {"mode": "fill_only"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"mode": "unknown"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"mode": "fill_only"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"mode": "fill_only"}, "demos": 7, "queries": 4},
        {"seed": 0, "settings": {"mode": "fill_only"}, "demos": 3, "queries": 0},
        {"seed": 0, "settings": {"mode": "fill_only"}, "demos": 3, "queries": 5},
    ],
)
def test_invalid_requests_fail_closed(proto, kwargs):
    with pytest.raises(ValueError):
        proto.generate(**kwargs)


def test_corrupt_labels_and_duplicate_inputs_fail_closed(proto):
    episode = proto.generate(37, {"mode": "select_most_bridges"}, demos=3, queries=4)
    corrupt = copy.deepcopy(episode)
    corrupt["train"][0]["output"][0][0] = (corrupt["train"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label"):
        proto.certify(corrupt)
    duplicate = copy.deepcopy(episode)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(duplicate)

@pytest.mark.parametrize("texture", ["plain", "wide_gap", "filled_gap", "cross", "seven_decoy"])
@pytest.mark.parametrize("n_gaps", [1, 3, 6])
def test_base_exact_gap_override_is_recoverable(generator, texture, n_gaps):
    for seed in range(4):
        grid = generator.generate(
            seed,
            seed + 101,
            difficulty="hard",
            grid_h=8,
            grid_w=8,
            n_gaps=n_gaps,
            texture=texture,
        )
        observed = generator.observe_overrides(grid)
        assert observed == {"grid_h": 8, "grid_w": 8, "n_gaps": n_gaps}
        assert generator.self_check(
            grid,
            meta={"overrides": {"grid_h": 8, "grid_w": 8, "n_gaps": n_gaps}},
        ) == []


def test_base_rejects_unknown_and_incompatible_overrides(generator):
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, misspelled_axis=3)
    with pytest.raises(ValueError, match="n_gaps.*no_gaps|no_gaps.*n_gaps"):
        generator.generate(0, 0, texture="no_gaps", n_gaps=1)

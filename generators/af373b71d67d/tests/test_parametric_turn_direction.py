"""Behavioral and native-contract tests for the turn-direction family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "af373b71d67d"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
PARAMETRIC = HERE.parents[1] / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"
CW = {"turn_direction": "clockwise"}
CCW = {"turn_direction": "counterclockwise"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    assert PROTOTYPE.is_file(), f"missing prototype: {PROTOTYPE}"
    return _load(PROTOTYPE, "_test_af373b71d67d_parametric")


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def test_default_program_is_exact_canonical_and_alternative_is_distinct(family):
    canonical = _canonical_program()
    assert family.program(CW) == canonical
    assert family.CANONICAL_PROGRAM == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical
    alternative = family.program(CCW)
    assert alternative == (PARAMETRIC / "counterclockwise.rkt").read_text(encoding="utf-8")
    assert alternative != canonical


@pytest.mark.parametrize("bad", [None, [], {}, {"turn_direction": "half_turn"}, {"turn_direction": "clockwise", "x": 1}])
def test_settings_are_strict(family, bad):
    with pytest.raises(ValueError):
        family.program(bad)


def test_literal_scene_exposes_oriented_offsets_and_setting_difference(family):
    grid = family.build_scene(
        12,
        15,
        motif=((0, 0), (1, 0), (2, 0), (2, 1)),
        motif_top=1,
        motif_left=1,
        frame=(4, 6, 10, 13),
        frame_color=7,
    )
    cw_i = family.oriented_motif_intermediate(grid, CW)
    ccw_i = family.oriented_motif_intermediate(grid, CCW)
    assert cw_i["oriented_offsets"] != ccw_i["oriented_offsets"]
    assert cw_i["frame_anchor"] == ccw_i["frame_anchor"] == [5, 7]
    assert family.transform(grid, CW) != family.transform(grid, CCW)
    assert grid[1][1] == 3, "transform helpers must not mutate input"


def test_generation_is_matched_and_count_prefix_stable(family):
    cw = family.generate(1234, CW, demos=2, queries=1)
    ccw = family.generate(1234, CCW, demos=2, queries=1)
    extended = family.generate(1234, CW, demos=6, queries=4)
    for split in ("train", "test"):
        assert [p["input"] for p in cw[split]] == [p["input"] for p in ccw[split]]
    assert cw["train"] == extended["train"][:2]
    assert cw["test"] == extended["test"][:1]
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(cw[split], ccw[split])
    )
    inputs = [p["input"] for split in ("train", "test") for p in extended[split]]
    assert len({json.dumps(g, separators=(",", ":")) for g in inputs}) == 10


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
@pytest.mark.parametrize("settings", [CW, CCW])
def test_supported_counts_are_exact(family, demos, queries, settings):
    episode = family.generate(9000 + demos * 10 + queries, settings, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == family.program(settings)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5), (True, 4)])
def test_bad_counts_reject(family, demos, queries):
    with pytest.raises(ValueError):
        family.generate(0, CW, demos, queries)


def test_four_query_bank_contains_substantive_30_by_30_boundary_case(family):
    episode = family.generate(41, CCW, demos=3, queries=4)
    large = [p for p in episode["test"] if (len(p["input"]), len(p["input"][0])) == (30, 30)]
    assert len(large) == 1
    grid = large[0]["input"]
    facts = family.inspect_scene(grid)
    assert len(facts["frame_cells"]) >= 80
    assert any(grid[0][c] != 0 for c in range(30)) or any(grid[-1][c] != 0 for c in range(30))
    assert any(row[0] != 0 or row[-1] != 0 for row in grid)


@pytest.mark.parametrize("seed", [0, 17, 2718])
@pytest.mark.parametrize("settings", [CW, CCW])
def test_two_demos_identify_setting_and_reject_named_shortcuts(family, seed, settings):
    episode = family.generate(seed, settings, demos=2, queries=4)
    cert = family.lesson_certificate(episode["train"], [p["input"] for p in episode["test"]])
    assert cert["surviving_settings"] == [settings]
    assert cert["surviving_shortcuts"] == []
    assert cert["query_outputs_consulted"] is False


def test_public_projection_hashes_only_visible_bytes(family):
    private = family.generate(88, CCW, demos=3, queries=4)
    private = {**private, "settings": CCW, "seed": 88, "certificate": {"private": True}}
    visible = family.public_projection(private)
    assert set(visible) == {"train", "test"}
    assert all(set(p) == {"input"} for p in visible["test"])
    assert family.public_bytes(private) == public_challenge_bytes(private)
    assert family.public_id(private) == public_challenge_id(private)
    changed = json.loads(json.dumps(private))
    changed["settings"] = CW
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    assert family.public_bytes(changed) == family.public_bytes(private)
    assert family.visible_turn(changed, 0) == family.visible_turn(private, 0)


def test_adapter_and_promotion_contract(family):
    contract = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"turn_direction": ["clockwise", "counterclockwise"]}
    assert contract["default"] == CW
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2
    adapter = _load(ADAPTER, "_test_af373b71d67d_adapter")
    for settings in (CW, CCW):
        assert adapter.program(settings) == family.program(settings)
        assert adapter.generate(17, settings, 3, 4) == family.generate(17, settings, 3, 4)

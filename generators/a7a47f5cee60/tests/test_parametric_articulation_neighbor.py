"""Behavioral and native-contract tests for the articulation-neighbor family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "a7a47f5cee60"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
PARAMETRIC = HERE.parents[1] / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"
ART = {"target_role": "articulation"}
NEIGHBOR = {"target_role": "largest_articulation_neighbor"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    assert PROTOTYPE.is_file(), f"missing prototype: {PROTOTYPE}"
    return _load(PROTOTYPE, "_test_a7a47f5cee60_parametric")


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
    assert family.program(ART) == canonical
    assert family.CANONICAL_PROGRAM == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical
    alternative = family.program(NEIGHBOR)
    assert alternative == (PARAMETRIC / "largest-neighbor.rkt").read_text(encoding="utf-8")
    assert alternative != canonical


@pytest.mark.parametrize("bad", [None, [], {}, {"target_role": "degree"}, {"target_role": "articulation", "x": 1}])
def test_settings_are_strict(family, bad):
    with pytest.raises(ValueError):
        family.program(bad)


def test_literal_scene_requires_articulation_before_largest_neighbor_choice(family):
    grid = family.build_block_scene(
        18,
        22,
        top=6,
        left=5,
        sizes={"A": (2, 2), "T": (3, 4), "B": (3, 5), "C": (4, 9)},
        distractors=((0, 0, 2, 3), (15, 19, 3, 3)),
        colors=(1, 3, 4, 6, 7, 9),
    )
    info = family.graph_intermediate(grid)
    assert len(info["articulation_indices"]) == 1
    assert info["largest_neighbor_index"] in info["articulation_neighbors"]
    assert info["largest_neighbor_index"] != info["articulation_index"]
    art = family.transform(grid, ART)
    neighbor = family.transform(grid, NEIGHBOR)
    assert art != neighbor
    assert family.nonzero_cells(art) == info["component_areas"][info["articulation_index"]]
    assert family.nonzero_cells(neighbor) == info["component_areas"][info["largest_neighbor_index"]]


def test_generation_is_matched_and_count_prefix_stable(family):
    art = family.generate(1234, ART, demos=2, queries=1)
    neighbor = family.generate(1234, NEIGHBOR, demos=2, queries=1)
    extended = family.generate(1234, ART, demos=6, queries=4)
    for split in ("train", "test"):
        assert [p["input"] for p in art[split]] == [p["input"] for p in neighbor[split]]
    assert art["train"] == extended["train"][:2]
    assert art["test"] == extended["test"][:1]
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(art[split], neighbor[split])
    )
    inputs = [p["input"] for split in ("train", "test") for p in extended[split]]
    assert len({json.dumps(g, separators=(",", ":")) for g in inputs}) == 10


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
@pytest.mark.parametrize("settings", [ART, NEIGHBOR])
def test_supported_counts_are_exact(family, demos, queries, settings):
    episode = family.generate(5000 + demos * 10 + queries, settings, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == family.program(settings)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5), (True, 4)])
def test_bad_counts_reject(family, demos, queries):
    with pytest.raises(ValueError):
        family.generate(0, ART, demos, queries)


def test_four_query_bank_contains_dense_30_by_30_boundary_case(family):
    episode = family.generate(41, NEIGHBOR, demos=3, queries=4)
    large = [p for p in episode["test"] if (len(p["input"]), len(p["input"][0])) == (30, 30)]
    assert len(large) == 1
    grid = large[0]["input"]
    info = family.graph_intermediate(grid)
    assert family.nonzero_cells(grid) >= 150
    assert len(info["components"]) >= 6
    assert any(grid[0][c] != 0 for c in range(30))
    assert any(grid[-1][c] != 0 for c in range(30))
    assert any(row[0] != 0 for row in grid)
    assert any(row[-1] != 0 for row in grid)


@pytest.mark.parametrize("seed", [0, 17, 2718])
@pytest.mark.parametrize("settings", [ART, NEIGHBOR])
def test_two_demos_identify_setting_and_reject_named_shortcuts(family, seed, settings):
    episode = family.generate(seed, settings, demos=2, queries=4)
    cert = family.lesson_certificate(episode["train"], [p["input"] for p in episode["test"]])
    assert cert["surviving_settings"] == [settings]
    assert cert["surviving_shortcuts"] == []
    assert cert["query_outputs_consulted"] is False


def test_public_projection_hashes_only_visible_bytes(family):
    private = family.generate(88, NEIGHBOR, demos=3, queries=4)
    private = {**private, "settings": NEIGHBOR, "seed": 88, "certificate": {"private": True}}
    visible = family.public_projection(private)
    assert set(visible) == {"train", "test"}
    assert all(set(p) == {"input"} for p in visible["test"])
    assert family.public_bytes(private) == public_challenge_bytes(private)
    assert family.public_id(private) == public_challenge_id(private)
    changed = json.loads(json.dumps(private))
    changed["settings"] = ART
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    assert family.public_bytes(changed) == family.public_bytes(private)
    assert family.visible_turn(changed, 0) == family.visible_turn(private, 0)


def test_adapter_and_promotion_contract(family):
    contract = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"target_role": ["articulation", "largest_articulation_neighbor"]}
    assert contract["default"] == ART
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2
    adapter = _load(ADAPTER, "_test_a7a47f5cee60_adapter")
    for settings in (ART, NEIGHBOR):
        assert adapter.program(settings) == family.program(settings)
        assert adapter.generate(17, settings, 3, 4) == family.generate(17, settings, 3, 4)

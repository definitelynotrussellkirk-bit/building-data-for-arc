from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / "e2bc70324918" / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CONTRACT_PATH = PARAMETRIC / "promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing required source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "test_e2bc_stamp_prototype")


def _adapter():
    return _load(ADAPTER_PATH, "test_e2bc_stamp_adapter")


def _canonical_from_catalog() -> str:
    from arcpuzzles.catalog import Catalog

    catalog = Catalog(ROOT)
    selected = catalog.describe("e2bc70324918")
    rule_task_id = selected.get("rule_task_id", "e2bc70324918")
    sources = {
        row["program_solution"]
        for row in catalog._variants()[rule_task_id]
        if isinstance(row.get("program_solution"), str)
    }
    assert len(sources) == 1
    return sources.pop()


def _all_pairs(claims):
    return claims["train"] + claims["test"]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def test_programs_preserve_exact_default_and_expose_one_real_variant():
    prototype = _prototype()
    canonical = _canonical_from_catalog()
    assert prototype.program_for("copy", root=ROOT) == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    dilated = prototype.program_for("dilate4", root=ROOT)
    assert dilated != canonical
    assert "source-stamp-cells" in dilated
    assert "dilation-deltas" in dilated
    assert "remove-duplicates" in dilated

    for value in ("filled", "", 0, None, True):
        with pytest.raises(ValueError, match="stamp_mode"):
            prototype.program_for(value, root=ROOT)


def test_matched_inputs_are_distinct_and_every_pair_separates_modes():
    prototype = _prototype()
    copy_claims = prototype.generate_claims(
        17, stamp_mode="copy", demos=3, queries=4, root=ROOT
    )
    dilate_claims = prototype.generate_claims(
        17, stamp_mode="dilate4", demos=3, queries=4, root=ROOT
    )
    copy_pairs = _all_pairs(copy_claims)
    dilate_pairs = _all_pairs(dilate_claims)

    assert [pair["input"] for pair in copy_pairs] == [
        pair["input"] for pair in dilate_pairs
    ]
    assert len({_grid_key(pair["input"]) for pair in copy_pairs}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(copy_pairs, dilate_pairs))
    for mode, claims in (("copy", copy_claims), ("dilate4", dilate_claims)):
        assert all(
            pair["output"] == prototype.python_mirror(pair["input"], stamp_mode=mode)
            for pair in _all_pairs(claims)
        )


def test_demo_count_changes_only_training_prefix_and_queries_are_stable():
    prototype = _prototype()
    claims = {
        demos: prototype.generate_claims(
            29, stamp_mode="dilate4", demos=demos, queries=4, root=ROOT
        )
        for demos in (2, 3, 6)
    }
    assert [pair["input"] for pair in claims[2]["train"]] == [
        pair["input"] for pair in claims[6]["train"][:2]
    ]
    assert [pair["input"] for pair in claims[3]["train"]] == [
        pair["input"] for pair in claims[6]["train"][:3]
    ]
    assert claims[2]["test"] == claims[3]["test"] == claims[6]["test"]
    assert all(len(claims[demos]["test"]) == 4 for demos in claims)


def test_episode_is_deterministic_and_last_query_is_substantive_30_by_30():
    prototype = _prototype()
    first = prototype.generate_claims(
        31, stamp_mode="copy", demos=2, queries=4, root=ROOT
    )
    second = prototype.generate_claims(
        31, stamp_mode="copy", demos=2, queries=4, root=ROOT
    )
    assert first == second

    grid = first["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    non_bg = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 7]
    assert len(non_bg) >= 28
    rows = {r for r, _ in non_bg}
    cols = {c for _, c in non_bg}
    assert min(rows) <= 4 and max(rows) >= 25
    assert min(cols) <= 4 and max(cols) >= 25


def test_contract_adapter_and_validation_are_strict():
    prototype = _prototype()
    adapter = _adapter()
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/e2bc70324918/workspace/parametric/adapter.py",
        "parameters": {"stamp_mode": ["copy", "dilate4"]},
        "default": {"stamp_mode": "copy"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
    }
    assert adapter.program({"stamp_mode": "copy"}) == _canonical_from_catalog()
    assert adapter.program({"stamp_mode": "dilate4"}) == prototype.program_for(
        "dilate4", root=ROOT
    )
    claims = adapter.generate(53, {"stamp_mode": "dilate4"}, 3, 4)
    assert set(claims) == {"train", "test", "program_solution"}
    assert len(claims["train"]) == 3 and len(claims["test"]) == 4

    for settings in ({}, {"stamp_mode": "bad"}, {"extra": "copy"}, None):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for demos in (1, 7, True):
        with pytest.raises(ValueError, match="demos"):
            adapter.generate(1, {"stamp_mode": "copy"}, demos, 4)
    for queries in (3, 5, True):
        with pytest.raises(ValueError, match="queries"):
            adapter.generate(1, {"stamp_mode": "copy"}, 3, queries)
    for seed in (-1, True, 1.0):
        with pytest.raises(ValueError, match="seed"):
            adapter.generate(seed, {"stamp_mode": "copy"}, 3, 4)


def test_minimum_lesson_defeats_fixed_motif_and_bbox_only_shortcuts():
    prototype = _prototype()
    claims = prototype.generate_claims(
        17, stamp_mode="dilate4", demos=2, queries=4, root=ROOT
    )
    demo_inputs = [pair["input"] for pair in claims["train"]]
    source_templates = [
        tuple(prototype.extracted_intermediate(grid, stamp_mode="copy"))
        for grid in demo_inputs
    ]
    transformed = [
        tuple(prototype.extracted_intermediate(grid, stamp_mode="dilate4"))
        for grid in demo_inputs
    ]

    def dimensions(cells):
        r1, c1, r2, c2 = prototype._bbox(cells)
        return r2 - r1 + 1, c2 - c1 + 1

    assert len(set(source_templates)) == 2
    assert {dimensions(cells) for cells in source_templates} == {(3, 3)}
    assert len(set(transformed)) == 2
    assert all(after != before for before, after in zip(source_templates, transformed))
    assert all(dimensions(cells) == (5, 5) for cells in transformed)

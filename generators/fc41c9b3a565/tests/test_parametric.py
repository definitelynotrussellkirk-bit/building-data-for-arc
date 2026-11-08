from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
FAMILY_PATH = PARAMETRIC / "family.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
CANONICAL_PATH = PARAMETRIC / "canonical.rkt"
COMPOSED_PATH = PARAMETRIC / "largest_symmetric_highlight.rkt"
WRONG_ORDER_PATH = PARAMETRIC / "wrong_order.rkt"
AUDIT_PATH = PARAMETRIC / "audit.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing required source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _family():
    return _load(FAMILY_PATH, "_test_fc41_parametric_family")


def _adapter():
    return _load(ADAPTER_PATH, "_test_fc41_parametric_adapter")


def _flat_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_required_native_sources_exist():
    for path in (
        FAMILY_PATH,
        ADAPTER_PATH,
        PROMOTION_PATH,
        CANONICAL_PATH,
        COMPOSED_PATH,
        WRONG_ORDER_PATH,
    ):
        assert path.is_file(), path


def test_default_program_is_exact_catalog_canonical():
    from arcpuzzles import Catalog

    adapter = _adapter()
    root = HOME.parents[1]
    catalog = Catalog(root)
    row = catalog.describe("fc41c9b3a565")
    authority = row.get("rule_task_id", row["id"])
    programs = {
        variant["program_solution"]
        for variant in catalog._variants()[authority]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert CANONICAL_PATH.read_text(encoding="utf-8") == canonical
    assert adapter.program({"mode": "canonical"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest().startswith(row["rule_hash"])


def test_setting_and_count_contract_is_strict():
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.program({})
    with pytest.raises(ValueError):
        adapter.program({"mode": "unknown"})
    with pytest.raises(ValueError):
        adapter.program({"mode": "canonical", "extra": 1})
    for bad_seed in (True, -1, 2**63):
        with pytest.raises(ValueError):
            adapter.generate(bad_seed, {"mode": "canonical"}, 3, 4)
    for bad_demos in (True, 1, 7):
        with pytest.raises(ValueError):
            adapter.generate(0, {"mode": "canonical"}, bad_demos, 4)
    for bad_queries in (True, 0, 5):
        with pytest.raises(ValueError):
            adapter.generate(0, {"mode": "canonical"}, 3, bad_queries)


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_episode_counts_are_independent_deterministic_and_distinct(demos, queries):
    adapter = _adapter()
    canonical = adapter.generate(41, {"mode": "canonical"}, demos, queries)
    repeated = adapter.generate(41, {"mode": "canonical"}, demos, queries)
    highlighted = adapter.generate(
        41, {"mode": "largest_symmetric_highlight"}, demos, queries
    )
    assert canonical == repeated
    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == queries
    assert _flat_inputs(canonical) == _flat_inputs(highlighted)
    keys = [_grid_key(grid) for grid in _flat_inputs(canonical)]
    assert len(keys) == len(set(keys))
    assert all(
        a["output"] != b["output"]
        for a, b in zip(
            canonical["train"] + canonical["test"],
            highlighted["train"] + highlighted["test"],
        )
    )


def test_highlight_mode_consumes_filtered_intermediate_and_wrong_order_fails():
    family = _family()
    episode = family.generate_episode(
        17, mode="largest_symmetric_highlight", demos=6, queries=4
    )
    traces = []
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        trace = family.trace(grid)
        traces.append(trace)
        assert trace["largest_original_is_symmetric"] is False
        assert trace["survivor_count"] >= 2
        assert trace["winner_size"] < trace["largest_original_size"]
        assert family.solve(grid, "canonical") == trace["intermediate"]
        assert family.solve(grid, "largest_symmetric_highlight") == pair["output"]
        assert family.solve_wrong_order(grid) != pair["output"]
        assert all(
            cell != family.HIGHLIGHT_COLOR for row in grid for cell in row
        )
    assert len({item["winner_color"] for item in traces}) >= 3
    assert len({item["winner_original_rank"] for item in traces}) >= 2


def test_no_fixed_color_or_fixed_original_rank_explains_all_highlight_demos():
    family = _family()
    episode = family.generate_episode(
        9, mode="largest_symmetric_highlight", demos=6, queries=4
    )
    demos = episode["train"]
    colors = sorted(
        {
            value
            for pair in demos
            for row in pair["input"]
            for value in row
            if value not in (0, family.HIGHLIGHT_COLOR)
        }
    )
    assert all(
        any(family.solve_fixed_color(pair["input"], color) != pair["output"] for pair in demos)
        for color in colors
    )
    ranks = range(1, 6)
    assert all(
        any(family.solve_fixed_original_rank(pair["input"], rank) != pair["output"] for pair in demos)
        for rank in ranks
    )


def test_last_query_is_substantive_30_by_30_stress():
    family = _family()
    episode = family.generate_episode(5, mode="canonical", demos=3, queries=4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    trace = family.trace(grid)
    assert trace["object_count"] == 8
    assert trace["foreground_cells"] >= 80
    assert trace["survivor_count"] == 5
    assert family.solve_wrong_order(grid) != family.solve(
        grid, "largest_symmetric_highlight"
    )


def test_all_cells_are_exact_arc_integers():
    family = _family()
    for mode in family.MODES:
        episode = family.generate_episode(123, mode=mode, demos=6, queries=4)
        for pair in episode["train"] + episode["test"]:
            for grid in (pair["input"], pair["output"]):
                assert 1 <= len(grid) <= 30
                assert 1 <= len(grid[0]) <= 30
                assert all(
                    type(cell) is int and 0 <= cell <= 9
                    for row in grid
                    for cell in row
                )


def test_bounded_self_audit_reports_real_coverage_and_counterexample():
    audit = _load(AUDIT_PATH, "_test_fc41_parametric_audit")
    report = audit.run_audit(range(4))
    assert report["schema"] == "arcpuzzles-parametric-self-review-v1"
    assert report["task_id"] == "fc41c9b3a565"
    assert report["tested_seeds"] == [0, 1, 2, 3]
    assert report["settings"] == ["canonical", "largest_symmetric_highlight"]
    assert report["episode_count"] == 8
    assert report["pair_count"] == 80
    assert report["failures"] == []
    assert report["winner_color_count"] >= 4
    assert report["winner_rank_count"] >= 3
    assert report["wrong_order_disagreements"] == 40
    assert report["counterexample"]["expected"] != report["counterexample"]["wrong_order"]

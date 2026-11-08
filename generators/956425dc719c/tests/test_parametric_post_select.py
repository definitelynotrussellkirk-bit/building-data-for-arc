from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / "956425dc719c" / "workspace" / "parametric"
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
    return _load(PROTOTYPE_PATH, "test_956_post_select_prototype")


def _adapter():
    return _load(ADAPTER_PATH, "test_956_post_select_adapter")


def _canonical_from_catalog() -> str:
    from arcpuzzles.catalog import Catalog

    catalog = Catalog(ROOT)
    selected = catalog.describe("956425dc719c")
    rule_task_id = selected.get("rule_task_id", "956425dc719c")
    sources = {
        row["program_solution"]
        for row in catalog._variants()[rule_task_id]
        if isinstance(row.get("program_solution"), str)
    }
    assert len(sources) == 1
    return sources.pop()


def _pairs(claims):
    return claims["train"] + claims["test"]


def _key(grid):
    return tuple(tuple(row) for row in grid)


def test_programs_preserve_exact_default_and_materialize_three_settings():
    prototype = _prototype()
    canonical = _canonical_from_catalog()
    assert prototype.program_for("none", root=ROOT) == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical

    largest = prototype.program_for("largest", root=ROOT)
    smallest = prototype.program_for("smallest", root=ROOT)
    assert len({canonical, largest, smallest}) == 3
    assert "stage-a" in largest and "remaining" in largest and "obj-size" in largest
    assert "stage-a" in smallest and "remaining" in smallest and "obj-size" in smallest
    assert (PARAMETRIC / "wrong_order_largest.rkt").is_file()

    for value in ("all", "", 0, None, True):
        with pytest.raises(ValueError, match="post_select"):
            prototype.program_for(value, root=ROOT)


def test_matched_inputs_identify_all_settings_and_stage_a_changes_rank_pool():
    prototype = _prototype()
    claims = {
        mode: prototype.generate_claims(17, post_select=mode, demos=3, queries=4, root=ROOT)
        for mode in prototype.ALLOWED_MODES
    }
    visible = [pair["input"] for pair in _pairs(claims["none"])]
    assert len({_key(grid) for grid in visible}) == 7
    for mode in prototype.ALLOWED_MODES[1:]:
        assert [pair["input"] for pair in _pairs(claims[mode])] == visible

    for index, grid in enumerate(visible):
        outputs = [claims[mode]["train"] + claims[mode]["test"] for mode in prototype.ALLOWED_MODES]
        assert len({_key(pairs[index]["output"]) for pairs in outputs}) == 3
        analysis = prototype.analyze_input(grid)
        assert len(analysis["one_border_sizes"]) == 1
        assert len(analysis["remaining_sizes"]) == 3
        assert len(set(analysis["remaining_sizes"])) == 3
        assert analysis["one_border_sizes"][0] > max(analysis["remaining_sizes"])
        for mode in prototype.ALLOWED_MODES:
            assert _pairs(claims[mode])[index]["output"] == prototype.python_mirror(
                grid, post_select=mode
            )
        assert prototype.python_wrong_order_largest(grid) != prototype.python_mirror(
            grid, post_select="largest"
        )


def test_demo_count_changes_only_training_prefix_and_queries_are_stable():
    prototype = _prototype()
    claims = {
        demos: prototype.generate_claims(
            29, post_select="smallest", demos=demos, queries=4, root=ROOT
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


def test_determinism_and_last_query_is_substantive_30_by_30():
    prototype = _prototype()
    first = prototype.generate_claims(
        31, post_select="largest", demos=2, queries=4, root=ROOT
    )
    second = prototype.generate_claims(
        31, post_select="largest", demos=2, queries=4, root=ROOT
    )
    assert first == second

    grid = first["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(occupied) >= 30
    rows = {r for r, _ in occupied}
    cols = {c for _, c in occupied}
    assert min(rows) == 0 and max(rows) == 29
    assert min(cols) == 0 and max(cols) >= 25


def test_contract_adapter_and_validation_are_strict():
    prototype = _prototype()
    adapter = _adapter()
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/956425dc719c/workspace/parametric/adapter.py",
        "parameters": {"post_select": ["none", "largest", "smallest"]},
        "default": {"post_select": "none"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
    }
    assert adapter.program({"post_select": "none"}) == _canonical_from_catalog()
    assert adapter.program({"post_select": "largest"}) == prototype.program_for(
        "largest", root=ROOT
    )
    claims = adapter.generate(53, {"post_select": "smallest"}, 3, 4)
    assert set(claims) == {"train", "test", "program_solution"}
    assert len(claims["train"]) == 3 and len(claims["test"]) == 4

    for settings in ({}, {"post_select": "bad"}, {"extra": "none"}, None):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for demos in (1, 7, True):
        with pytest.raises(ValueError, match="demos"):
            adapter.generate(1, {"post_select": "none"}, demos, 4)
    for queries in (3, 5, True):
        with pytest.raises(ValueError, match="queries"):
            adapter.generate(1, {"post_select": "none"}, 3, queries)
    for seed in (-1, True, 1.0):
        with pytest.raises(ValueError, match="seed"):
            adapter.generate(seed, {"post_select": "none"}, 3, 4)


def test_minimum_lesson_varies_rank_sizes_to_defeat_fixed_size_shortcuts():
    prototype = _prototype()
    claims = {
        mode: prototype.generate_claims(17, post_select=mode, demos=2, queries=4, root=ROOT)
        for mode in prototype.ALLOWED_MODES
    }
    demo_inputs = [pair["input"] for pair in claims["none"]["train"]]
    analyses = [prototype.analyze_input(grid) for grid in demo_inputs]
    profiles = [tuple(row["remaining_sizes"]) for row in analyses]
    assert len(set(profiles)) == 2
    assert all(row["one_border_sizes"][0] > max(row["remaining_sizes"]) for row in analyses)

    def count_color(grid, color):
        return sum(value == color for row in grid for value in row)

    largest_sizes = [count_color(pair["output"], 1) for pair in claims["largest"]["train"]]
    smallest_sizes = [count_color(pair["output"], 1) for pair in claims["smallest"]["train"]]
    assert len(set(largest_sizes)) == 2
    assert len(set(smallest_sizes)) == 2


def test_six_demo_episode_has_no_train_query_collision_at_periodic_boundary():
    prototype = _prototype()
    claims = prototype.generate_claims(
        6, post_select="none", difficulty="medium", demos=6, queries=4, root=ROOT
    )
    inputs = [pair["input"] for pair in _pairs(claims)]
    assert len(inputs) == 10
    assert len({_key(grid) for grid in inputs}) == 10

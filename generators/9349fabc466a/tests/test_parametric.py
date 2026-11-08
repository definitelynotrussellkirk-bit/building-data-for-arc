"""Behavioral contract for the native 9349fabc466a parametric family."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "catalog").is_dir())
RUNTIME = ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))

PARAMETRIC = HERE.parents[1] / "workspace" / "parametric"


def _load(filename: str, module_name: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _family():
    return _load("family.py", "_test_9349_parametric_family")


def _adapter():
    return _load("adapter.py", "_test_9349_parametric_adapter")


def _hand_fixture():
    return [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 3, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 4, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def test_completion_frame_has_hand_checked_two_stage_output():
    """Catches skipped span completion, wrong winner scoring, and wrong frame bounds."""
    family = _family()
    source = _hand_fixture()
    before = copy.deepcopy(source)

    canonical = family.solve(source, "canonical")
    assert canonical == [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 3, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 2, 2, 2, 2, 2, 0, 0],
        [0, 0, 2, 0, 0, 0, 2, 0, 0],
        [0, 0, 2, 4, 4, 4, 2, 0, 0],
        [0, 0, 2, 0, 0, 0, 2, 0, 0],
        [0, 0, 2, 2, 2, 2, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    assert family.solve(source, "completion_frame") == [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 3, 9, 9, 9, 9, 9, 9, 0],
        [0, 9, 2, 2, 2, 2, 2, 9, 0],
        [0, 9, 2, 0, 0, 0, 2, 9, 0],
        [0, 9, 2, 4, 4, 4, 2, 9, 0],
        [0, 9, 2, 0, 0, 0, 2, 9, 0],
        [0, 9, 2, 2, 2, 2, 2, 9, 0],
        [0, 9, 9, 9, 9, 9, 9, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    assert source == before


def test_intermediate_is_completion_derived_not_largest_marker_bbox():
    """Catches a cheap largest-original-bbox shortcut in the claimed dependency."""
    family = _family()
    intermediate = family.completion_intermediate(_hand_fixture())
    assert intermediate == {
        "winner_color": 2,
        "new_cell_count": 12,
        "new_cells_bbox": [2, 6, 2, 6],
    }
    assert family.wrong_marker_bbox_intermediate(_hand_fixture())["winner_color"] == 3


def test_adapter_preserves_exact_default_and_rejects_untyped_contract_values():
    """Catches canonical drift and permissive/coercing adapter validation."""
    from arcpuzzles import Catalog

    adapter = _adapter()
    canonical = {
        variant["program_solution"]
        for variant in Catalog(ROOT).get("9349fabc466a")["variants"]
    }
    assert canonical == {adapter.program({"postprocess": "canonical"})}
    assert adapter.program({"postprocess": "completion_frame"}) != next(iter(canonical))

    with pytest.raises(ValueError, match="settings"):
        adapter.program({"postprocess": "unknown"})
    with pytest.raises(ValueError, match="settings"):
        adapter.program({"postprocess": True})
    with pytest.raises(ValueError, match="demos"):
        adapter.generate(0, {"postprocess": "canonical"}, 1, 4)
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(0, {"postprocess": "canonical"}, 3, 0)


def test_matched_inputs_identify_setting_and_counts_are_independent():
    """Catches setting-dependent inputs, coupled counts, duplicate pairs, and weak demos."""
    adapter = _adapter()
    canonical = adapter.generate(31, {"postprocess": "canonical"}, 2, 4)
    alternate = adapter.generate(31, {"postprocess": "completion_frame"}, 2, 4)
    expanded = adapter.generate(31, {"postprocess": "canonical"}, 6, 1)

    canonical_inputs = [p["input"] for p in canonical["train"] + canonical["test"]]
    alternate_inputs = [p["input"] for p in alternate["train"] + alternate["test"]]
    assert canonical_inputs == alternate_inputs
    assert len({repr(grid) for grid in canonical_inputs}) == 6
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], alternate["train"]))
    assert expanded["train"][:2] == canonical["train"]
    assert expanded["test"][0]["input"] == canonical["test"][0]["input"]


def test_complete_query_bank_is_shuffled_before_prefix_and_varies_by_seed():
    """Catches source-order leakage and query-prefix regeneration."""
    adapter = _adapter()
    full = adapter.generate(5, {"postprocess": "canonical"}, 3, 4)
    prefix = adapter.generate(5, {"postprocess": "canonical"}, 3, 1)
    other = adapter.generate(6, {"postprocess": "canonical"}, 3, 4)

    assert sorted(full["query_source_indices"]) == [6, 7, 8, 9]
    assert prefix["query_source_indices"] == full["query_source_indices"][:1]
    assert prefix["test"] == full["test"][:1]
    assert other["query_source_indices"] != full["query_source_indices"]


def test_bank_contains_substantive_30_by_30_case_and_fresh_deterministic_grids():
    """Catches small-grid padding and shared mutable output reuse."""
    family = _family()
    first = family.scene(77, 9)
    second = family.scene(77, 9)
    assert len(first) == 30 and len(first[0]) == 30
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert sum(value != 0 for row in first for value in row) >= 10
    solved = family.solve(first, "completion_frame")
    assert sum(value == 9 for row in solved for value in row) >= 40


def test_wrong_intermediate_changes_the_alternative_output():
    """Catches a causal witness whose authored ablation is output-equivalent."""
    family = _family()
    grid = family.scene(13, 0)
    assert family.solve(grid, "completion_frame") != family.solve_wrong_marker_bbox(grid)


def test_reusable_audit_sweeps_settings_counts_queries_and_counterfactuals():
    """Catches an evidence tool that merely inventories files without exercising behavior."""
    audit = _load("audit.py", "_test_9349_parametric_audit")
    report = audit.run_audit(range(3), protected=False)
    assert report["failures"] == []
    assert report["coverage"]["settings"] == ["canonical", "completion_frame"]
    assert report["coverage"]["demonstration_counts"] == [2, 3, 4, 5, 6]
    assert report["coverage"]["query_counts"] == [1, 2, 3, 4]
    assert report["coverage"]["max_shape"] == [30, 30]
    assert report["counterfactual_separations"] == 30
    assert report["labeled_pairs"] > 0

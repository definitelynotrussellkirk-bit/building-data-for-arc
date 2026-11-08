"""Native adapter contract for the blue-count-scope parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root

TASK_ID = "017f1406edaf"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_count_scope_programs_preserve_exact_row0_default():
    prototype = _load("count_scope_prototype", HOME / "prototype.py")
    assert prototype.COUNT_SCOPES == ("row0", "all_blue")
    assert prototype.program_for("row0") == _canonical_program()
    alternative = prototype.program_for("all_blue")
    assert alternative.startswith("(rule!")
    assert alternative != _canonical_program()
    assert "(append* g)" in alternative


def test_count_scope_adapter_builds_identifiable_episodes_at_all_supported_demo_counts():
    prototype = _load("count_scope_prototype_counts", HOME / "prototype.py")
    adapter = _load("count_scope_adapter", HOME / "adapter.py")
    for scope in prototype.COUNT_SCOPES:
        settings = {"count_scope": scope}
        other = "all_blue" if scope == "row0" else "row0"
        for demos in (2, 3, 6):
            episode = adapter.generate(17, settings, demos, 4)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == adapter.program(settings)
            pairs = [*episode["train"], *episode["test"]]
            serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
            assert len(serialized) == len(set(serialized))
            assert all(
                prototype.python_reference(pair["input"], count_scope=scope) == pair["output"]
                for pair in pairs
            )
            assert all(
                prototype.python_reference(pair["input"], count_scope=other) != pair["output"]
                for pair in episode["train"]
            )
            stress = episode["test"][-1]["input"]
            assert (len(stress), len(stress[0])) == (30, 30)
            row0_target = prototype.target_count(stress, "row0")
            all_target = prototype.target_count(stress, "all_blue")
            assert row0_target != all_target
            assert prototype.python_reference(stress, count_scope="row0") != prototype.python_reference(
                stress, count_scope="all_blue"
            )


def test_count_scope_changes_input_derived_target_not_object_location():
    prototype = _load("count_scope_prototype_causality", HOME / "prototype.py")
    seen_orderings = set()
    for pair_index in range(8):
        grid = prototype.build_input(5, pair_index)
        row_cells = prototype.selected_cells(grid, "row0")
        all_cells = prototype.selected_cells(grid, "all_blue")
        assert row_cells != all_cells
        row_first = min(row_cells)
        all_first = min(all_cells)
        seen_orderings.add(row_first < all_first)
    assert seen_orderings == {False, True}


def test_count_scope_adapter_is_strict_and_deterministic():
    adapter = _load("count_scope_adapter_validation", HOME / "adapter.py")
    settings = {"count_scope": "row0"}
    assert adapter.generate(9, settings, 2, 4) == adapter.generate(9, settings, 2, 4)
    with pytest.raises(ValueError, match="exactly"):
        adapter.program({})
    with pytest.raises(ValueError, match="count_scope"):
        adapter.program({"count_scope": "diagonal"})
    with pytest.raises(ValueError, match="demos"):
        adapter.generate(9, settings, 7, 4)
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(9, settings, 2, 5)
    with pytest.raises(TypeError, match="seed"):
        adapter.generate(True, settings, 2, 4)


def test_count_scope_promotion_binds_sources_and_replayable_audit():
    promotion = json.loads((HOME / "promotion.json").read_text())
    assert promotion["qualification_demos"] == 2
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert set(promotion["resources"]) == {
        f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        f"generators/{TASK_ID}/workspace/parametric/rules/count_row0.rkt",
        f"generators/{TASK_ID}/workspace/parametric/rules/count_all_blue.rkt",
    }
    assert (HOME / "self_audit.py").is_file()

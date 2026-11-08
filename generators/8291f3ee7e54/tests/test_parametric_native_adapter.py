"""Native promotion contract for the 8291f3ee7e54 ring-order family."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, normalize_grid

TASK_ID = "8291f3ee7e54"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
FAMILY_PATH = PARAMETRIC / "native_family.py"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
CONTRACT_PATH = PARAMETRIC / "promotion.json"
AUDIT_PATH = PARAMETRIC / "audit_native.py"
EXPECTED_CANONICAL_SHA256 = "79951c1fb8d60053930868df5a4f183a5ed50884fe0e479e954ea446b7b8b6bb"


def _load(path: Path, suffix: str):
    assert path.is_file(), f"required native source is missing: {path.name}"
    name = f"_native_{TASK_ID}_{suffix}_{hashlib.sha256(str(path).encode()).hexdigest()}"
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load(ADAPTER_PATH, "adapter")


@pytest.fixture(scope="module")
def family():
    return _load(FAMILY_PATH, "family")


@pytest.fixture(scope="module")
def prototype():
    return _load(PROTOTYPE_PATH, "prototype")


@pytest.fixture(scope="module")
def audit_module():
    return _load(AUDIT_PATH, "audit")


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        assert instance.runtime_identity["backend"] == "racket"
        assert instance.runtime_identity["protected"] is True
        yield instance


def _pairs(episode: dict[str, Any]) -> list[dict[str, list[list[int]]]]:
    return [*episode["train"], *episode["test"]]


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in _pairs(episode)]


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return normalize_grid(bridge.eval_text(f"({wrap_rule(program)} {_literal(grid)})"))


def test_promotion_contract_names_exact_adapter_and_supported_limits():
    assert CONTRACT_PATH.is_file(), "native promotion contract is missing"
    assert json.loads(CONTRACT_PATH.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"ring_order": ["largest_outside", "smallest_outside"]},
        "default": {"ring_order": "largest_outside"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }


def test_program_preserves_exact_canonical_default_and_one_tail_replacement(adapter, prototype):
    canonical = prototype.canonical_source(root=ROOT)
    largest = adapter.program({"ring_order": "largest_outside"})
    smallest = adapter.program({"ring_order": "smallest_outside"})
    assert largest == canonical
    assert hashlib.sha256(largest.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert smallest != largest
    assert smallest.count(prototype.ALTERNATIVE_TAIL) == 1
    assert smallest.replace(prototype.ALTERNATIVE_TAIL, prototype.CANONICAL_TAIL, 1) == canonical


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"ring_order": "largest_outside", "extra": 1},
        {"ring_order": "largest"},
        {"ring_order": True},
        {"ring_order": 1},
    ],
)
def test_program_rejects_noncontract_settings(adapter, settings):
    with pytest.raises(ValueError, match="settings|ring_order"):
        adapter.program(settings)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1])
def test_generate_rejects_invalid_seed_scalars(adapter, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        adapter.generate(bad, {"ring_order": "largest_outside"}, 3, 4)


@pytest.mark.parametrize(
    "name,bad",
    [
        ("demos", True),
        ("demos", 1),
        ("demos", 7),
        ("queries", False),
        ("queries", 0),
        ("queries", 5),
    ],
)
def test_generate_rejects_invalid_count_scalars(adapter, name, bad):
    kwargs = {
        "seed": 0,
        "settings": {"ring_order": "largest_outside"},
        "demos": 3,
        "queries": 4,
    }
    kwargs[name] = bad
    with pytest.raises((TypeError, ValueError), match=name):
        adapter.generate(**kwargs)


def test_minimum_and_maximum_counts_are_independent_deterministic_and_unique(adapter):
    settings = {"ring_order": "largest_outside"}
    minimum = adapter.generate(23, settings, 2, 1)
    maximum = adapter.generate(23, settings, 6, 4)
    repeated = adapter.generate(23, settings, 6, 4)
    four_queries = adapter.generate(23, settings, 2, 4)
    assert set(minimum) == {"train", "test", "program_solution"}
    assert len(minimum["train"]) == 2
    assert len(minimum["test"]) == 1
    assert len(maximum["train"]) == 6
    assert len(maximum["test"]) == 4
    assert maximum == repeated
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"][0] == four_queries["test"][0]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(maximum)]
    assert len(serialized) == len(set(serialized)) == 10


def test_inputs_are_setting_independent_and_every_label_changes(adapter):
    largest = adapter.generate(17, {"ring_order": "largest_outside"}, 6, 4)
    smallest = adapter.generate(17, {"ring_order": "smallest_outside"}, 6, 4)
    assert _inputs(largest) == _inputs(smallest)
    assert all(
        left["output"] != right["output"]
        for left, right in zip(_pairs(largest), _pairs(smallest), strict=True)
    )


def test_first_query_is_substantive_30x30_boundary_and_distractor_case(adapter, family):
    episode = adapter.generate(0, {"ring_order": "largest_outside"}, 2, 4)
    grid = episode["test"][0]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(cell != 0 for row in grid for cell in row) >= 100
    assert any(cell != 0 for cell in grid[0])
    assert any(cell != 0 for cell in grid[-1])
    assert any(row[0] != 0 for row in grid)
    assert any(row[-1] != 0 for row in grid)
    facts = family.analyze_input(grid)
    assert len(facts["layers"]) == 5
    assert facts["spans"] == [11, 9, 7, 5, 3]
    assert any(layer["component_count"] > 1 for layer in facts["layers"])
    assert any(layer["union_span"] > layer["selected_span"] for layer in facts["layers"])


def test_python_claimed_labels_match_both_programs_in_protected_racket(adapter, bridge):
    for order in ("largest_outside", "smallest_outside"):
        settings = {"ring_order": order}
        episode = adapter.generate(0, settings, 2, 4)
        program = adapter.program(settings)
        assert episode["program_solution"] == program
        for pair in _pairs(episode):
            assert _execute(bridge, program, pair["input"]) == pair["output"]


def test_bounded_self_audit_rejects_named_shortcuts_in_protected_racket(audit_module):
    report = audit_module.audit(0)
    assert report["status"] == "pass"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["scope"] == {
        "seed": 0,
        "demos": 2,
        "queries": 4,
        "settings": 2,
        "rivals_per_setting": 4,
    }
    for row in report["settings"]:
        assert row["chosen_labels_match_racket"] is True
        assert all(not rival["fits_demonstrations"] for rival in row["rivals"].values())
        assert all(rival["query_differs"] for rival in row["rivals"].values())

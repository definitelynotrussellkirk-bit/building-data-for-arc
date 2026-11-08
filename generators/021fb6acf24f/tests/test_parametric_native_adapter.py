"""Native promotion contract for the 021fb6acf24f color-order family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root

TASK_ID = "021fb6acf24f"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
FAMILY_PATH = PARAMETRIC / "native_family.py"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
CONTRACT_PATH = PARAMETRIC / "promotion.json"
AUDIT_PATH = PARAMETRIC / "audit_native.py"
EXPECTED_CANONICAL_SHA256 = "f7b49e9ffb4c0dcaa332d46e67bd1f4d5c9be35200705fc34f394548380bcbb3"


def _load(path: Path, suffix: str):
    assert path.is_file(), f"required native source is missing: {path.name}"
    name = f"_native_{TASK_ID}_{suffix}_{hashlib.sha256(str(path).encode()).hexdigest()}"
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
def bridge():
    with RacketBridge() as instance:
        assert instance.runtime_identity["backend"] == "racket"
        assert instance.runtime_identity["protected"] is True
        yield instance


def _pairs(episode: dict[str, Any]) -> list[dict[str, list[list[int]]]]:
    return [*episode["train"], *episode["test"]]


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in _pairs(episode)]


def _first_nonzero(grid: list[list[int]]) -> int:
    return next(cell for row in grid for cell in row if cell != 0)


def _colors(grid: list[list[int]]) -> list[int]:
    return sorted({cell for row in grid for cell in row if cell != 0})


def _shape(grid: list[list[int]]) -> tuple[int, int]:
    return len(grid), len(grid[0])


def test_promotion_contract_names_exact_native_adapter_and_supported_limits():
    assert CONTRACT_PATH.is_file(), "native promotion contract is missing"
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"color_order": ["ascending", "descending"]},
        "default": {"color_order": "ascending"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }


def test_program_preserves_exact_canonical_default_and_only_wraps_color_order(adapter, prototype):
    canonical = prototype.canonical_source(root=ROOT)
    ascending = adapter.program({"color_order": "ascending"})
    descending = adapter.program({"color_order": "descending"})
    assert ascending == canonical
    assert hashlib.sha256(ascending.encode()).hexdigest() == EXPECTED_CANONICAL_SHA256
    assert descending != ascending
    assert descending.count(prototype.DESCENDING_COLOR_EXPRESSION) == 1
    assert (
        descending.replace(
            prototype.DESCENDING_COLOR_EXPRESSION,
            prototype.CANONICAL_COLOR_EXPRESSION,
            1,
        )
        == canonical
    )


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"color_order": "ascending", "extra": 1},
        {"color_order": "ASC"},
        {"color_order": True},
        {"color_order": 1},
    ],
)
def test_program_rejects_noncontract_settings(adapter, settings):
    with pytest.raises(ValueError, match="settings|color_order"):
        adapter.program(settings)


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, -1])
def test_generate_rejects_invalid_seed_scalars(adapter, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        adapter.generate(bad, {"color_order": "ascending"}, 3, 4)


@pytest.mark.parametrize("name,bad", [("demos", True), ("demos", 1), ("demos", 7), ("queries", False), ("queries", 0), ("queries", 5)])
def test_generate_rejects_invalid_count_scalars(adapter, name, bad):
    kwargs = {"seed": 0, "settings": {"color_order": "ascending"}, "demos": 3, "queries": 4}
    kwargs[name] = bad
    with pytest.raises((TypeError, ValueError), match=name):
        adapter.generate(**kwargs)


def test_minimum_and_maximum_counts_are_independent_and_deterministic(adapter):
    settings = {"color_order": "ascending"}
    minimum = adapter.generate(23, settings, 2, 1)
    maximum = adapter.generate(23, settings, 6, 4)
    repeated = adapter.generate(23, settings, 6, 4)
    assert set(minimum) == {"train", "test", "program_solution"}
    assert len(minimum["train"]) == 2
    assert len(minimum["test"]) == 1
    assert len(maximum["train"]) == 6
    assert len(maximum["test"]) == 4
    assert maximum == repeated
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"][0] == adapter.generate(23, settings, 2, 4)["test"][0]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(maximum)]
    assert len(serialized) == len(set(serialized)) == 10


def test_inputs_are_setting_independent_but_overlap_labels_change(adapter):
    ascending = adapter.generate(17, {"color_order": "ascending"}, 6, 4)
    descending = adapter.generate(17, {"color_order": "descending"}, 6, 4)
    assert _inputs(ascending) == _inputs(descending)
    assert all(
        left["output"] != right["output"]
        for left, right in zip(_pairs(ascending), _pairs(descending), strict=True)
    )


def test_first_two_demonstrations_defeat_row_major_first_occurrence_shortcut(adapter):
    for order in ("ascending", "descending"):
        episode = adapter.generate(0, {"color_order": order}, 2, 4)
        first, second = episode["train"]
        first_colors = _colors(first["input"])
        second_colors = _colors(second["input"])
        assert len(first_colors) == len(second_colors) == 2
        assert _first_nonzero(first["input"]) == max(first_colors)
        assert _first_nonzero(second["input"]) == min(second_colors)
        assert first["output"] != second["output"]


def test_default_episode_has_four_distinct_queries_and_substantive_30x30_case(adapter):
    episode = adapter.generate(0, {"color_order": "ascending"}, 3, 4)
    assert len(episode["test"]) == 4
    large = [pair for pair in episode["test"] if _shape(pair["input"]) == (30, 30)]
    assert len(large) == 1
    pair = large[0]
    changed = sum(
        before != after
        for input_row, output_row in zip(pair["input"], pair["output"], strict=True)
        for before, after in zip(input_row, output_row, strict=True)
    )
    nonzero_rows = {r for r, row in enumerate(pair["output"]) if any(row)}
    nonzero_cols = {
        c
        for c in range(30)
        if any(pair["output"][r][c] != 0 for r in range(30))
    }
    assert changed >= 180
    assert len(nonzero_rows) >= 20
    assert len(nonzero_cols) >= 20
    assert any(pair["input"][r][c] != 0 for r, c in ((0, 0), (0, 29), (29, 0), (29, 29)))


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("order", ["ascending", "descending"])
def test_python_claims_match_protected_racket_for_all_default_pairs(adapter, prototype, bridge, seed, order):
    episode = adapter.generate(seed, {"color_order": order}, 3, 4)
    source = adapter.program({"color_order": order})
    for pair in _pairs(episode):
        assert prototype.execute_rule(source, copy.deepcopy(pair["input"]), bridge=bridge) == pair["output"]


def test_bounded_protected_racket_audit_refutes_plausible_two_demo_rivals():
    audit_module = _load(AUDIT_PATH, "audit")
    report = audit_module.audit(seed=0)
    assert report["schema"] == "arcpuzzles-parametric-self-audit-v1"
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
    assert {row["settings"]["color_order"] for row in report["settings"]} == {
        "ascending",
        "descending",
    }
    expected_rivals = {
        "opposite_numeric_order",
        "row_major_first_occurrence",
        "original_zero_late_overwrite",
        "identity",
    }
    for row in report["settings"]:
        assert row["chosen_labels_match_racket"] is True
        assert set(row["rivals"]) == expected_rivals
        for rival in row["rivals"].values():
            assert rival["fits_demonstrations"] is False
            assert rival["query_differs"] is True
            case = rival["counterexample"]
            assert case["chosen_output"] != case["rival_output"]
            assert 1 <= len(case["input"]) <= 30
    assert "finite" in report["limitation"].lower()

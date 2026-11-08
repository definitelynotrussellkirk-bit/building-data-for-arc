"""Native parametric-family contract for 0d5077971eea."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "generators/0d5077971eea/workspace/parametric"


def _load_adapter():
    path = HOME / "adapter.py"
    assert path.exists(), "parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_0d5077971eea", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row_local(grid):
    return [
        [
            row[0] if col > 0 and value == 8 and row[0] != 0 else value
            for col, value in enumerate(row)
        ]
        for row in grid
    ]


def _eligible_rows(grid):
    rows = []
    for index, row in enumerate(grid):
        count = sum(value == 8 for value in row[1:])
        if row[0] not in (0, 8) and count:
            rows.append((count, index, row[0]))
    return rows


def _densest_header(grid):
    rows = _eligible_rows(grid)
    assert rows
    peak = max(count for count, _, _ in rows)
    winners = [(index, color) for count, index, color in rows if count == peak]
    assert len(winners) == 1
    return winners[0]


def _densest_source(grid):
    _, color = _densest_header(grid)
    return [
        [color if col > 0 and value == 8 else value for col, value in enumerate(row)]
        for row in grid
    ]


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_default_program_is_exact_and_settings_are_strict():
    adapter = _load_adapter()
    canonical = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    assert adapter.program({"header_policy": "row_local"}) == canonical
    assert adapter.program({"header_policy": "densest_source"}) == (
        HOME / "densest_source.rkt"
    ).read_text(encoding="utf-8")

    for bad in (
        {},
        {"header_policy": "row_local", "extra": 1},
        {"header_policy": "unknown"},
        {"header_policy": 1},
        None,
    ):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_inputs_are_setting_matched_and_count_prefixes_are_independent():
    adapter = _load_adapter()
    local = adapter.generate(17, {"header_policy": "row_local"}, 3, 4)
    dense = adapter.generate(17, {"header_policy": "densest_source"}, 3, 4)
    assert _inputs(local, "train") == _inputs(dense, "train")
    assert _inputs(local, "test") == _inputs(dense, "test")

    two = adapter.generate(17, {"header_policy": "row_local"}, 2, 4)
    six = adapter.generate(17, {"header_policy": "row_local"}, 6, 4)
    one_query = adapter.generate(17, {"header_policy": "row_local"}, 3, 1)
    assert _inputs(two, "train") == _inputs(six, "train")[:2]
    assert _inputs(two, "test") == _inputs(six, "test")
    assert _inputs(one_query, "test") == _inputs(local, "test")[:1]

    all_inputs = _inputs(six, "train") + _inputs(six, "test")
    assert len({repr(grid) for grid in all_inputs}) == len(all_inputs)


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_labels_match_both_rules_and_two_demos_identify_the_setting(seed):
    adapter = _load_adapter()
    local = adapter.generate(seed, {"header_policy": "row_local"}, 2, 4)
    dense = adapter.generate(seed, {"header_policy": "densest_source"}, 2, 4)

    selected = set()
    for local_pair, dense_pair in zip(local["train"] + local["test"], dense["train"] + dense["test"]):
        assert local_pair["input"] == dense_pair["input"]
        assert local_pair["output"] == _row_local(deepcopy(local_pair["input"]))
        assert dense_pair["output"] == _densest_source(deepcopy(dense_pair["input"]))
        selected.add(_densest_header(local_pair["input"])[1])

    assert all(
        left["output"] != right["output"]
        for left, right in zip(local["train"], dense["train"])
    )
    assert len({_densest_header(pair["input"])[1] for pair in dense["train"]}) == 2
    assert len(selected) >= 4


@pytest.mark.parametrize("policy", ["row_local", "densest_source"])
def test_four_queries_include_substantive_30x30_content(policy):
    adapter = _load_adapter()
    episode = adapter.generate(42, {"header_policy": policy}, 3, 4)
    assert len(episode["test"]) == 4
    large = episode["test"][-1]
    grid = large["input"]
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    assert sum(value != 0 for row in grid for value in row) >= 120
    assert len(large["output"]) == 30
    assert all(len(row) == 30 for row in large["output"])
    assert _densest_header(grid)


def test_seed_and_counts_reject_bool_fraction_and_out_of_range_values():
    adapter = _load_adapter()
    settings = {"header_policy": "row_local"}
    for args in (
        (True, settings, 3, 4),
        (0, settings, 1, 4),
        (0, settings, 7, 4),
        (0, settings, 3, 0),
        (0, settings, 3, 5),
        (0, settings, 3.0, 4),
        (-1, settings, 3, 4),
    ):
        with pytest.raises(ValueError):
            adapter.generate(*args)


def test_self_audit_refutes_every_named_shortcut_at_minimum_demo_count():
    path = HOME / "audit.py"
    assert path.exists(), "parametric self-audit has not been implemented"
    spec = importlib.util.spec_from_file_location("audit_0d5077971eea", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run(seeds=(0, 17, 991))
    assert report["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert report["status"] == "passed"
    assert report["surviving_rivals"] == []
    assert report["episodes_checked"] == 6
    assert report["has_30x30"] is True

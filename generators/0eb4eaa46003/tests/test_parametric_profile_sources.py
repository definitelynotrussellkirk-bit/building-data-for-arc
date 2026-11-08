"""Focused contract tests for the native profile-source parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "0eb4eaa46003"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
CANONICAL = "blue_rows_red_cols"
SWAPPED = "red_rows_blue_cols"


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode: dict) -> list:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_adapter_contract_and_exact_canonical_default():
    adapter = _load("adapter")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"profile_sources": [CANONICAL, SWAPPED]},
        "default": {"profile_sources": CANONICAL},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/audit_lessons.py",
        ],
    }
    canonical = _canonical_program()
    assert adapter.program({"profile_sources": CANONICAL}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "bb6e25e7de935b4d6ad8a45e00c560421b23b59c7e436d9a6cb0b41ec6d96d5f"
    )
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    swapped = adapter.program({"profile_sources": SWAPPED})
    assert swapped != canonical
    assert "(row-profile red)" in swapped
    assert "(col-profile blue)" in swapped


def test_settings_counts_and_scalar_types_are_strict():
    adapter = _load("adapter")
    for bad in ({}, {"profile_sources": CANONICAL, "extra": 1}, {"profile_sources": "rows_only"}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for seed in (True, -1, 1.0, "1"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"profile_sources": CANONICAL}, 3, 4)
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3, 0), (3, 5), (3, True)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(1, {"profile_sources": CANONICAL}, demos, queries)


def test_inputs_are_setting_independent_distinct_and_every_pair_changes_label():
    adapter = _load("adapter")
    canonical = adapter.generate(23, {"profile_sources": CANONICAL}, 3, 4)
    swapped = adapter.generate(23, {"profile_sources": SWAPPED}, 3, 4)
    assert _inputs(canonical) == _inputs(swapped)
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(encoded) == len(set(encoded)) == 7
    for left, right in zip(
        canonical["train"] + canonical["test"],
        swapped["train"] + swapped["test"],
        strict=True,
    ):
        assert left["output"] != right["output"]


def test_demo_and_query_counts_are_independent_and_prefix_stable():
    adapter = _load("adapter")
    setting = {"profile_sources": CANONICAL}
    minimum = adapter.generate(41, setting, 2, 1)
    full_queries = adapter.generate(41, setting, 2, 4)
    full_demos = adapter.generate(41, setting, 6, 4)
    assert minimum["train"] == full_queries["train"] == full_demos["train"][:2]
    assert minimum["test"] == full_queries["test"][:1]
    assert full_queries["test"] == full_demos["test"]
    assert len(full_demos["train"]) == 6
    assert len(full_demos["test"]) == 4


def test_every_demonstration_constructively_identifies_the_setting():
    adapter = _load("adapter")
    prototype = _load("prototype")
    for selected, rival in ((CANONICAL, SWAPPED), (SWAPPED, CANONICAL)):
        episode = adapter.generate(57, {"profile_sources": selected}, 2, 4)
        for pair in episode["train"]:
            assert prototype.solve(pair["input"], selected) == pair["output"]
            assert prototype.solve(pair["input"], rival) != pair["output"]
        audit = prototype.audit_episode(episode, selected)
        assert audit["opposite_setting_survives"] is False
        assert audit["query_disagreements"] == 4
        assert audit["surviving_declared_shortcuts"] == []


def test_four_queries_cover_ordinary_geometry_boundary_and_30x30_stress():
    adapter = _load("adapter")
    prototype = _load("prototype")
    episode = adapter.generate(73, {"profile_sources": SWAPPED}, 3, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(12, 18), (18, 22), (24, 26), (30, 30)]
    metrics = [prototype.input_metrics(pair["input"]) for pair in episode["test"]]
    assert all(row["component_count"] >= 8 for row in metrics)
    assert metrics[-1]["occupied_cells"] >= 220
    assert metrics[-1]["boundary_sides"] == ["bottom", "left", "right", "top"]
    assert metrics[-1]["max_component_height"] >= 6
    assert metrics[-1]["max_component_width"] >= 6


def test_public_turn_hides_settings_program_answers_and_future_queries():
    adapter = _load("adapter")
    prototype = _load("prototype")
    episode = adapter.generate(89, {"profile_sources": CANONICAL}, 3, 4)
    public = {"train": episode["train"], "test": episode["test"]}
    raw = public_challenge_bytes(public)
    assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()
    parsed = json.loads(raw)
    assert all(set(pair) == {"input"} for pair in parsed["test"])
    assert b"profile_sources" not in raw
    assert b"program_solution" not in raw
    assert CANONICAL.encode() not in raw

    mutated = copy.deepcopy(public)
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(mutated) == public_challenge_id(public)

    first_turn = prototype.public_turn(episode, 0)
    assert public_challenge_bytes(first_turn) == public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][0]]}
    )
    assert len(first_turn["test"]) == 1 and set(first_turn["test"][0]) == {"input"}


def test_generation_is_deterministic_and_returns_fresh_data():
    adapter = _load("adapter")
    setting = {"profile_sources": SWAPPED}
    first = adapter.generate(101, setting, 3, 4)
    second = adapter.generate(101, setting, 3, 4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(101, setting, 3, 4) == second

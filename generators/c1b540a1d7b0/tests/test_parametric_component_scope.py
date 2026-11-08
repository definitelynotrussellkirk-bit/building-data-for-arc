"""Native-contract and teaching checks for the component-scope family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c1b540a1d7b0"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
HOME = HERE.parents[1] / "workspace" / "parametric"
PROTOTYPE = HOME / "prototype.py"
ADAPTER = HOME / "adapter.py"
PROMOTION = HOME / "promotion.json"
CANONICAL = {"component_scope": "all_components"}
SELECTED = {"component_scope": "largest_component"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    assert PROTOTYPE.is_file(), f"missing prototype: {PROTOTYPE}"
    return _load(PROTOTYPE, "_test_c1b540a1d7b0_parametric")


def _canonical_program() -> str:
    found = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                found.add(row["program_solution"])
    assert len(found) == 1
    return next(iter(found))


def test_default_program_is_exact_canonical_and_alternative_is_distinct(family):
    canonical = _canonical_program()
    assert family.program(CANONICAL) == canonical
    assert (HOME / "canonical.rkt").read_text(encoding="utf-8") == canonical
    alternative = family.program(SELECTED)
    assert alternative != canonical
    assert (HOME / "largest-component.rkt").read_text(encoding="utf-8") == alternative


@pytest.mark.parametrize("settings", [None, {}, [], {"component_scope": "bad"}, {"component_scope": "all_components", "x": 1}])
def test_settings_are_strict(family, settings):
    with pytest.raises(ValueError):
        family.program(settings)


def test_generation_is_matched_count_stable_and_prefix_stable(family):
    canonical = family.generate(123, CANONICAL, demos=2, queries=1)
    selected = family.generate(123, SELECTED, demos=2, queries=1)
    extended = family.generate(123, CANONICAL, demos=6, queries=4)
    assert [p["input"] for p in canonical["train"]] == [p["input"] for p in selected["train"]]
    assert [p["input"] for p in canonical["test"]] == [p["input"] for p in selected["test"]]
    assert canonical["train"] == extended["train"][:2]
    assert canonical["test"] == extended["test"][:1]
    assert all(a["output"] != b["output"] for split in ("train", "test") for a, b in zip(canonical[split], selected[split]))
    grids = [p["input"] for split in ("train", "test") for p in extended[split]]
    assert len({json.dumps(g, separators=(",", ":")) for g in grids}) == 10


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
@pytest.mark.parametrize("settings", [CANONICAL, SELECTED])
def test_supported_counts(family, demos, queries, settings):
    episode = family.generate(1000 + demos * 10 + queries, settings, demos, queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == family.program(settings)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5), (True, 4)])
def test_bad_counts_reject(family, demos, queries):
    with pytest.raises(ValueError):
        family.generate(0, CANONICAL, demos, queries)


def test_two_demos_identify_each_setting_and_reject_shortcuts(family):
    for seed in (0, 17, 2718):
        for settings in (CANONICAL, SELECTED):
            episode = family.generate(seed, settings, 2, 4)
            cert = family.lesson_certificate(episode["train"], [p["input"] for p in episode["test"]])
            assert cert["surviving_settings"] == [settings]
            assert cert["surviving_shortcuts"] == []
            assert cert["query_outputs_consulted"] is False


def test_fourth_query_is_substantive_30x30_and_selector_is_nontrivial(family):
    episode = family.generate(41, SELECTED, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    components = family.components5(grid)
    assert len(components) >= 3
    assert len({len(c) for c in components}) == len(components)
    assert max(len(c) for c in components) >= 50
    occupied = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    assert len(occupied) >= 75
    assert min(r for r, _ in occupied) == 0 or min(c for _, c in occupied) == 0
    assert max(r for r, _ in occupied) == 29 or max(c for _, c in occupied) == 29


def test_public_projection_hides_settings_program_answers_and_future_queries(family):
    episode = family.generate(88, SELECTED, 3, 4)
    private = {**copy.deepcopy(episode), "settings": SELECTED, "seed": 88}
    expected = public_challenge_bytes(private)
    assert family.public_bytes(private) == expected
    assert family.public_id(private) == public_challenge_id(private)
    changed = copy.deepcopy(private)
    changed["settings"] = CANONICAL
    changed["program_solution"] = "private"
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    assert family.public_bytes(changed) == expected
    assert family.visible_turn_bytes(changed, 0) == family.visible_turn_bytes(private, 0)


def test_adapter_contract(family):
    contract = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["adapter"] == f"generators/{TASK_ID}/workspace/parametric/adapter.py"
    assert contract["parameters"] == {"component_scope": ["all_components", "largest_component"]}
    assert contract["default"] == CANONICAL
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    adapter = _load(ADAPTER, "_test_c1b540a1d7b0_adapter")
    for settings in (CANONICAL, SELECTED):
        assert adapter.program(settings) == family.program(settings)
        assert adapter.generate(17, settings, 3, 4) == family.generate(17, settings, 3, 4)

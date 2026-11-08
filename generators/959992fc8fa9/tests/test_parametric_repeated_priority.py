"""Behavioral and native-contract tests for the repeated-color priority family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "959992fc8fa9"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
PARAMETRIC = HERE.parents[1] / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"
CANONICAL_SETTINGS = {"intersection_policy": "different_red"}
PRIORITY_SETTINGS = {"intersection_policy": "repeated_color_priority"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    assert PROTOTYPE.is_file(), f"missing prototype: {PROTOTYPE}"
    return _load(PROTOTYPE, "_test_959992fc8fa9_parametric")


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _literal_grid() -> list[list[int]]:
    grid = [[0] * 8 for _ in range(8)]
    # Row-major colors are [1, 4, 4, 8]. Rows and columns are all distinct.
    grid[1][1] = 1
    grid[3][5] = 4
    grid[5][2] = 4
    grid[7][6] = 8
    return grid


def _nonzero(grid: list[list[int]]) -> int:
    return sum(cell != 0 for row in grid for cell in row)


def test_default_program_is_exact_canonical_and_alternative_is_distinct(family):
    canonical = _canonical_program()
    assert family.program(CANONICAL_SETTINGS) == canonical
    assert family.CANONICAL_PROGRAM == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical

    alternative = family.program(PRIORITY_SETTINGS)
    assert isinstance(alternative, str) and alternative.strip()
    assert alternative != canonical
    assert (PARAMETRIC / "repeated-color-priority.rkt").read_text(encoding="utf-8") == alternative


@pytest.mark.parametrize(
    "settings",
    [
        None,
        [],
        {},
        {"intersection_policy": "unknown"},
        {"intersection_policy": "different_red", "extra": 1},
    ],
)
def test_program_rejects_malformed_or_undeclared_settings(family, settings):
    with pytest.raises(ValueError):
        family.program(settings)


def test_literal_input_exposes_input_derived_priority_and_three_collision_types(family):
    grid = _literal_grid()
    intermediate = family.repeated_color_intermediate(grid)
    assert intermediate == {
        "priority_color": 4,
        "counts": {1: 1, 4: 2, 8: 1},
        "source_count": 4,
    }

    canonical = family.transform(grid, CANONICAL_SETTINGS)
    priority = family.transform(grid, PRIORITY_SETTINGS)

    # Different-color crossing involving the repeated color: red vs priority.
    assert canonical[3][1] == 2
    assert priority[3][1] == 4
    # Same-color crossing remains the repeated color under both settings.
    assert canonical[3][2] == priority[3][2] == 4
    # Unique/unique crossing remains red under both settings.
    assert canonical[1][6] == priority[1][6] == 2
    assert grid == _literal_grid(), "transforms must not mutate inputs"


def test_generation_is_setting_neutral_count_stable_and_query_prefix_stable(family):
    canonical = family.generate(1234, CANONICAL_SETTINGS, demos=2, queries=1)
    priority = family.generate(1234, PRIORITY_SETTINGS, demos=2, queries=1)
    extended = family.generate(1234, CANONICAL_SETTINGS, demos=6, queries=4)

    for split in ("train", "test"):
        assert [pair["input"] for pair in canonical[split]] == [
            pair["input"] for pair in priority[split]
        ]
    assert canonical["train"] == extended["train"][:2]
    assert canonical["test"] == extended["test"][:1]
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(canonical[split], priority[split])
    )

    all_inputs = [
        pair["input"] for split in ("train", "test") for pair in extended[split]
    ]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}) == 10


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
@pytest.mark.parametrize("settings", [CANONICAL_SETTINGS, PRIORITY_SETTINGS])
def test_supported_counts_are_exact(family, demos, queries, settings):
    episode = family.generate(9000 + demos * 10 + queries, settings, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["program_solution"] == family.program(settings)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 0},
        {"demos": 3, "queries": 5},
        {"demos": True, "queries": 4},
    ],
)
def test_generate_rejects_unsupported_counts(family, kwargs):
    with pytest.raises(ValueError):
        family.generate(0, CANONICAL_SETTINGS, **kwargs)


def test_fourth_query_is_substantive_30_by_30_boundary_stress(family):
    episode = family.generate(41, PRIORITY_SETTINGS, demos=3, queries=4)
    query = episode["test"][3]
    grid = query["input"]
    output = query["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert len(family.source_pixels(grid)) == 5
    assert any(grid[0][c] != 0 for c in range(30))
    assert any(grid[-1][c] != 0 for c in range(30))
    assert any(row[0] != 0 for row in grid)
    assert any(row[-1] != 0 for row in grid)
    assert _nonzero(output) >= 250
    assert family.repeated_color_intermediate(grid)["priority_color"] not in {
        min(value for _, _, value in family.source_pixels(grid)),
        max(value for _, _, value in family.source_pixels(grid)),
    }


@pytest.mark.parametrize("seed", [0, 17, 2718])
@pytest.mark.parametrize("settings", [CANONICAL_SETTINGS, PRIORITY_SETTINGS])
def test_two_demos_identify_setting_and_reject_named_shortcuts_without_query_labels(
    family, seed, settings
):
    episode = family.generate(seed, settings, demos=2, queries=4)
    certificate = family.lesson_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]]
    )
    assert certificate["surviving_settings"] == [settings]
    assert certificate["surviving_shortcuts"] == []
    assert certificate["query_outputs_consulted"] is False
    assert certificate["scope"].startswith("finite")
    assert all(row["first_eliminating_demo"] is not None for row in certificate["shortcuts"].values())


def test_public_projection_and_first_turn_hide_private_fields_and_future_queries(family):
    episode = family.generate(88, PRIORITY_SETTINGS, demos=3, queries=4)
    private = {
        **copy.deepcopy(episode),
        "settings": copy.deepcopy(PRIORITY_SETTINGS),
        "seed": 88,
        "certificate": {"private": True},
    }
    visible = family.public_projection(private)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    assert all(set(pair) == {"input"} for pair in visible["test"])
    expected_bytes = public_challenge_bytes(private)
    assert family.public_bytes(private) == expected_bytes
    assert family.public_id(private) == public_challenge_id(private)

    changed = copy.deepcopy(private)
    changed["settings"] = copy.deepcopy(CANONICAL_SETTINGS)
    changed["program_solution"] = "private replacement"
    changed["certificate"] = {"changed": True}
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    assert family.public_bytes(changed) == expected_bytes
    assert family.public_id(changed) == family.public_id(private)

    first_turn = family.visible_turn(private, 0)
    assert len(first_turn["test"]) == 1
    assert first_turn["test"][0] == {"input": private["test"][0]["input"]}
    changed["test"][1]["input"][0][0] = 7
    assert family.visible_turn_bytes(changed, 0) == family.visible_turn_bytes(private, 0)


def test_native_adapter_and_promotion_contract_are_exact(family):
    contract = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {
            "intersection_policy": ["different_red", "repeated_color_priority"]
        },
        "default": CANONICAL_SETTINGS,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/repeated-color-priority.rkt",
            f"generators/{TASK_ID}/workspace/parametric/audit.py",
        ],
    }
    adapter = _load(ADAPTER, "_test_959992fc8fa9_adapter")
    for settings in (CANONICAL_SETTINGS, PRIORITY_SETTINGS):
        assert adapter.program(settings) == family.program(settings)
        assert adapter.generate(17, settings, 3, 4) == family.generate(17, settings, 3, 4)

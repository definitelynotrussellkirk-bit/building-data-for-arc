from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "14dacb3b518f"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC_HOME = TASK_HOME / "workspace" / "parametric"
DEFAULT = {"rule_mode": "hole_presence"}
ALTERNATE = {"rule_mode": "most_holed_size_threshold"}


def _load_module(filename: str, name: str):
    path = PARAMETRIC_HOME / filename
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load_module("adapter.py", "test_parametric_adapter_14dacb3b518f")


def _prototype():
    return _load_module("prototype.py", "test_parametric_prototype_14dacb3b518f")


def _grid(*rows: str) -> list[list[int]]:
    assert rows and len({len(row) for row in rows}) == 1
    return [[int(cell) for cell in row] for row in rows]


HAND_INPUT = _grid(
    "6666666000666600",
    "6006006000600600",
    "6006006000600600",
    "6006006000666600",
    "6666666000000000",
    "0000000000000000",
    "0000000000000000",
    "6666660000000000",
    "6666660000006600",
    "6666660000006600",
    "6666660000000000",
    "0000000000000000",
)

CANONICAL_OUTPUT = _grid(
    "8888888000888800",
    "8008008000800800",
    "8008008000800800",
    "8008008000888800",
    "8888888000000000",
    "0000000000000000",
    "0000000000000000",
    "2222220000000000",
    "2222220000002200",
    "2222220000002200",
    "2222220000000000",
    "0000000000000000",
)

ALTERNATE_OUTPUT = _grid(
    "8888888000222200",
    "8008008000200200",
    "8008008000200200",
    "8008008000222200",
    "8888888000000000",
    "0000000000000000",
    "0000000000000000",
    "8888880000000000",
    "8888880000002200",
    "8888880000002200",
    "8888880000000000",
    "0000000000000000",
)


def _canonical_program() -> str:
    catalog = Catalog(REPO_ROOT)
    row = catalog.describe(TASK_ID)
    authority = row.get("rule_task_id", TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in catalog._variants().get(authority, [])
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_authority_and_alternate_is_distinct():
    adapter = _adapter()
    canonical = adapter.program(DEFAULT)
    alternate = adapter.program(ALTERNATE)
    assert canonical == _canonical_program()
    assert hashlib.sha256(canonical.encode()).hexdigest() == "fe78a969401a4f718a8537ef8ea1a2a748a34cd2a3a8bcdd28b964d1654b1f9d"
    assert alternate != canonical
    assert alternate.strip().startswith("(rule!")


def test_hand_fixture_exposes_the_causal_intermediate_and_both_rule_outputs():
    prototype = _prototype()
    analysis = prototype.analyze_input(HAND_INPUT)
    assert analysis["errors"] == []
    assert sorted(component["hole_count"] for component in analysis["components"]) == [0, 0, 1, 2]
    assert sorted(component["size"] for component in analysis["components"]) == [4, 12, 23, 24]
    assert analysis["anchor"]["hole_count"] == 2
    assert analysis["anchor_size"] == 23
    assert prototype.solve(HAND_INPUT, DEFAULT) == CANONICAL_OUTPUT
    assert prototype.solve(HAND_INPUT, ALTERNATE) == ALTERNATE_OUTPUT


def test_inputs_are_setting_independent_count_independent_distinct_and_query_one_stable():
    adapter = _adapter()
    canonical = adapter.generate(23, DEFAULT, demos=3, queries=4)
    alternate = adapter.generate(23, ALTERNATE, demos=3, queries=4)
    short_queries = adapter.generate(23, DEFAULT, demos=3, queries=1)
    short_demos = adapter.generate(23, DEFAULT, demos=2, queries=4)

    assert _inputs(canonical) == _inputs(alternate)
    assert [pair["input"] for pair in canonical["train"][:2]] == [
        pair["input"] for pair in short_demos["train"]
    ]
    assert [pair["input"] for pair in canonical["test"]] == [
        pair["input"] for pair in short_demos["test"]
    ]
    assert canonical["test"][0]["input"] == short_queries["test"][0]["input"]

    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(serialized) == len(set(serialized)) == 7
    assert all(
        left["output"] != right["output"]
        for left, right in zip(canonical["train"], alternate["train"])
    )


def test_supported_counts_have_exact_distinct_pairs_and_selected_outputs():
    adapter = _adapter()
    prototype = _prototype()
    for demos in range(2, 7):
        for queries in range(1, 5):
            for settings in (DEFAULT, ALTERNATE):
                episode = adapter.generate(101, settings, demos=demos, queries=queries)
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == queries
                assert episode["program_solution"] == adapter.program(settings)
                inputs = _inputs(episode)
                assert len({json.dumps(grid) for grid in inputs}) == demos + queries
                for pair in [*episode["train"], *episode["test"]]:
                    assert pair["output"] == prototype.solve(pair["input"], settings)


def test_four_query_episode_includes_substantive_30x30_boundary_stress():
    adapter = _adapter()
    prototype = _prototype()
    episode = adapter.generate(17, ALTERNATE, demos=3, queries=4)
    query = episode["test"][3]["input"]
    analysis = prototype.analyze_input(query)
    assert (len(query), len(query[0])) == (30, 30)
    assert analysis["errors"] == []
    assert analysis["nonzero_cells"] >= 120
    assert analysis["outer_boundary_components"] >= 2
    assert len(analysis["components"]) == 5
    assert max(len(pair["input"]) for pair in episode["test"]) > max(
        len(pair["input"]) for pair in episode["train"]
    )


def test_public_projection_hides_settings_program_and_query_answers():
    adapter = _adapter()
    full = adapter.generate(7, ALTERNATE, demos=3, queries=4)
    one = adapter.generate(7, ALTERNATE, demos=3, queries=1)

    payload = public_challenge_bytes(full)
    public = json.loads(payload)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert b"rule_mode" not in payload
    assert b"program_solution" not in payload
    assert public_challenge_id(full) == hashlib.sha256(payload).hexdigest()

    first_turn_full = {"train": full["train"], "test": [full["test"][0]]}
    first_turn_one = {"train": one["train"], "test": one["test"]}
    assert public_challenge_bytes(first_turn_full) == public_challenge_bytes(first_turn_one)


def _paint_by_selected_components(grid, selected_indices):
    prototype = _prototype()
    analysis = prototype.analyze_input(grid)
    output = [[0 for _ in row] for row in grid]
    for component in analysis["components"]:
        color = 8 if component["index"] in selected_indices else 2
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _two_largest_rival(grid):
    prototype = _prototype()
    components = prototype.analyze_input(grid)["components"]
    selected = {
        component["index"]
        for component in sorted(components, key=lambda item: (item["size"], item["index"]))[-2:]
    }
    return _paint_by_selected_components(grid, selected)


def _bbox_gap_rival(grid):
    prototype = _prototype()
    components = prototype.analyze_input(grid)["components"]
    selected = set()
    for component in components:
        r0, c0, r1, c1 = component["bbox"]
        bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)
        if component["size"] < bbox_area:
            selected.add(component["index"])
    return _paint_by_selected_components(grid, selected)


def test_visible_demos_reject_size_rank_and_bbox_gap_shortcuts_that_fail_queries():
    adapter = _adapter()
    alternate = adapter.generate(23, ALTERNATE, demos=3, queries=4)
    canonical = adapter.generate(23, DEFAULT, demos=3, queries=4)

    assert any(pair["output"] != _two_largest_rival(pair["input"]) for pair in alternate["train"])
    assert any(pair["output"] != _two_largest_rival(pair["input"]) for pair in alternate["test"])
    assert any(pair["output"] != _bbox_gap_rival(pair["input"]) for pair in canonical["train"])
    assert any(pair["output"] != _bbox_gap_rival(pair["input"]) for pair in canonical["test"])


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"rule_mode": "unknown"},
        {"rule_mode": "hole_presence", "extra": 1},
    ],
)
def test_invalid_settings_are_rejected(settings):
    adapter = _adapter()
    with pytest.raises(ValueError, match="settings"):
        adapter.program(settings)
    with pytest.raises(ValueError, match="settings"):
        adapter.generate(0, settings, demos=3, queries=4)


@pytest.mark.parametrize(
    ("seed", "demos", "queries", "message"),
    [
        (True, 3, 4, "seed"),
        (-1, 3, 4, "seed"),
        (0, 1, 4, "demos"),
        (0, 7, 4, "demos"),
        (0, 3, 0, "queries"),
        (0, 3, 5, "queries"),
    ],
)
def test_invalid_request_bounds_are_rejected(seed, demos, queries, message):
    adapter = _adapter()
    with pytest.raises(ValueError, match=message):
        adapter.generate(seed, DEFAULT, demos=demos, queries=queries)

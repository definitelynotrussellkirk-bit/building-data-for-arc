"""Native row-fill / vertical-bridge family for 9da02d5e3ac0."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "9da02d5e3ac0"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HOME / "workspace" / "parametric"
SETTINGS = (
    {"finish_rule": "row_fill_only"},
    {"finish_rule": "row_fill_then_vertical_bridge"},
)


def _load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "the MAIN native adapter has not been built"
    spec = importlib.util.spec_from_file_location("_tested_9da02d5e3ac0_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for row in map(json.loads, handle):
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_byte_exact_and_alternate_is_distinct():
    adapter = _load_adapter()
    canonical = _canonical_program()
    assert adapter.program(SETTINGS[0]) == canonical
    assert adapter.program(SETTINGS[1]) != canonical
    assert adapter.program(SETTINGS[1]).startswith("(rule!")


@pytest.mark.parametrize("demos", (2, 3, 6))
@pytest.mark.parametrize("queries", (1, 4))
def test_counts_matched_inputs_stable_prefixes_and_distinctness(demos, queries):
    adapter = _load_adapter()
    canonical = adapter.generate(17, SETTINGS[0], demos=demos, queries=queries)
    bridged = adapter.generate(17, SETTINGS[1], demos=demos, queries=queries)
    full = adapter.generate(17, SETTINGS[0], demos=6, queries=4)

    assert len(canonical["train"]) == demos and len(canonical["test"]) == queries
    assert _inputs(canonical) == _inputs(bridged)
    assert canonical["train"] == full["train"][:demos]
    assert canonical["test"] == full["test"][:queries]
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(canonical[split], bridged[split], strict=True)
    )
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == demos + queries
    public_challenge_bytes(canonical)


def test_first_two_demonstrations_expose_row_fill_dependency_and_bridge_guard():
    adapter = _load_adapter()
    canonical = adapter.generate(0, SETTINGS[0], demos=2, queries=4)
    bridged = adapter.generate(0, SETTINGS[1], demos=2, queries=4)

    for plain, composed in zip(canonical["train"], bridged["train"], strict=True):
        analysis = adapter.analyze_input(plain["input"])
        assert analysis["completed_bridge_cells"]
        assert {tuple(cell) for cell in analysis["completed_bridge_cells"]} - {tuple(cell) for cell in analysis["raw_bridge_cells"]}
        assert analysis["mixed_signal_columns"]
        assert analysis["horizontal_same_color_gaps"]
        assert plain["output"] == adapter.claimed_output(plain["input"], SETTINGS[0])
        assert composed["output"] == adapter.claimed_output(composed["input"], SETTINGS[1])
        assert plain["output"] != composed["output"]


def test_maximum_query_is_substantive_30_by_30_and_hits_all_boundaries():
    adapter = _load_adapter()
    pair = adapter.generate(2**63 - 1, SETTINGS[1], demos=2, queries=4)["test"][-1]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 260
    assert any(value != 0 for value in grid[0])
    assert any(value != 0 for value in grid[-1])
    assert any(row[0] != 0 for row in grid)
    assert any(row[-1] != 0 for row in grid)
    assert len(adapter.analyze_input(grid)["completed_bridge_cells"]) >= 30


def test_public_turn_omits_private_answers_settings_program_and_future_queries():
    adapter = _load_adapter()
    episode = adapter.generate(23, SETTINGS[1], demos=3, queries=4)
    first = adapter.public_turn(episode, 0)
    one = adapter.generate(23, SETTINGS[1], demos=3, queries=1)
    assert first == adapter.public_turn(one, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}

    encoded = adapter.public_turn_bytes(episode, 0)
    assert encoded == public_challenge_bytes(first)
    assert adapter.public_turn_id(episode, 0) == hashlib.sha256(encoded).hexdigest()

    changed = deepcopy(episode)
    changed.update(settings=SETTINGS[0], seed=999, program_solution="PRIVATE PROGRAM", private_note="PRIVATE")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert adapter.public_turn_bytes(changed, 0) == encoded

    assert adapter.public_turn(episode, 3) == {
        "train": episode["train"],
        "test": [{"input": episode["test"][3]["input"]}],
    }
    for bad in (-1, 4, True, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError)):
            adapter.public_turn(episode, bad)


def test_protected_racket_labels_and_demo_only_identification():
    _load_adapter()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for seed, demos in ((0, 2), (17, 6))
        for setting in SETTINGS
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert [check["survivors"] for check in result["checks"]] == [
        [job["settings"]] for job in jobs
    ]
    assert [check["label_count"] for check in result["checks"]] == [
        job["demos"] + 4 for job in jobs
    ]


@pytest.mark.parametrize(
    "patch",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
        {"settings": None}, {"settings": {}},
        {"settings": {"finish_rule": True}},
        {"settings": {"finish_rule": "unknown"}},
        {"settings": {"finish_rule": "row_fill_only", "extra": 1}},
        {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
        {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
    ],
)
def test_invalid_controls_fail_closed(patch):
    adapter = _load_adapter()
    request = {"seed": 17, "settings": SETTINGS[0], "demos": 3, "queries": 4}
    request.update(patch)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**request)

@pytest.mark.parametrize("seed", (0, 17, 19, 2**63 - 1))
def test_each_minimum_demo_refutes_first_nonzero_row_key(seed):
    """Catch replacing the first non-5 row key with the first nonzero color."""
    adapter = _load_adapter()
    episode = adapter.generate(seed, SETTINGS[0], demos=2, queries=1)
    for pair in episode["train"]:
        witnesses = []
        for before, after in zip(pair["input"], pair["output"], strict=True):
            first_non5 = next((value for value in before if value != 5), None)
            first_nonzero = next((value for value in before if value not in (0, 5)), None)
            changed_fives = [
                column
                for column, value in enumerate(before)
                if value == 5 and after[column] == 0
            ]
            if first_non5 == 0 and first_nonzero not in (None, 0) and changed_fives:
                witnesses.append((first_nonzero, changed_fives))
        assert witnesses, "every two-demo lesson member must expose zero as a valid row key"

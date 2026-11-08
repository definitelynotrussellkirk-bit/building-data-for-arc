"""Native parametric family for the pairwise-intersection gallery."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "1216927d148b"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PARAMETRIC = HOME / "workspace" / "parametric"
SETTINGS = (
    {"gallery_order": "fixed_pairs"},
    {"gallery_order": "largest_overlap_first"},
)


def _load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "the MAIN native adapter has not been built"
    spec = importlib.util.spec_from_file_location("_tested_1216927d148b_adapter", path)
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
    fixed = adapter.generate(17, SETTINGS[0], demos=demos, queries=queries)
    ranked = adapter.generate(17, SETTINGS[1], demos=demos, queries=queries)
    full = adapter.generate(17, SETTINGS[0], demos=6, queries=4)

    assert len(fixed["train"]) == demos and len(fixed["test"]) == queries
    assert _inputs(fixed) == _inputs(ranked)
    assert fixed["train"] == full["train"][:demos]
    assert fixed["test"] == full["test"][:queries]
    assert any(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(fixed[split], ranked[split], strict=True)
    )

    fingerprints = {
        json.dumps(grid, separators=(",", ":")) for grid in _inputs(fixed)
    }
    assert len(fingerprints) == demos + queries
    public_challenge_bytes(fixed)


def test_first_two_demonstrations_teach_order_and_tie_breaking():
    adapter = _load_adapter()
    fixed = adapter.generate(0, SETTINGS[0], demos=2, queries=4)
    ranked = adapter.generate(0, SETTINGS[1], demos=2, queries=4)
    assert all(
        a["output"] != b["output"]
        for a, b in zip(fixed["train"], ranked["train"], strict=True)
    )

    analysis = [adapter.analyze_input(pair["input"]) for pair in ranked["train"]]
    assert len(set(analysis[0]["intersection_counts"])) == 3
    counts = analysis[1]["intersection_counts"]
    assert counts[1] == counts[2] > counts[0]
    assert analysis[1]["ranked_pair_names"][:2] == ["AC", "BC"]


def test_maximum_query_is_substantive_30_by_17_and_hits_all_boundaries():
    adapter = _load_adapter()
    grid = adapter.generate(2**63 - 1, SETTINGS[1], demos=2, queries=4)["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 17)
    assert sum(value != 0 for row in grid for value in row) >= 210
    assert any(grid[0][c] != 0 for c in range(17))
    assert any(grid[-1][c] != 0 for c in range(17))
    assert any(row[0] != 0 for row in grid)
    assert any(row[-1] != 0 for row in grid)
    assert all(row[5] == row[11] == 0 for row in grid)


def test_public_turn_omits_private_answers_settings_program_and_future_queries():
    adapter = _load_adapter()
    episode = adapter.generate(23, SETTINGS[1], demos=3, queries=4)
    first = adapter.public_turn(episode, 0)
    one = adapter.generate(23, SETTINGS[1], demos=3, queries=1)
    assert first == adapter.public_turn(one, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}

    encoded = adapter.public_turn_bytes(episode, 0)
    assert adapter.public_turn_id(episode, 0) == hashlib.sha256(encoded).hexdigest()
    changed = deepcopy(episode)
    changed.update(settings={"gallery_order": "fixed_pairs"}, seed=999,
                   program_solution="PRIVATE PROGRAM", private_note="PRIVATE")
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
        {"settings": {"gallery_order": True}},
        {"settings": {"gallery_order": "unknown"}},
        {"settings": {"gallery_order": "fixed_pairs", "extra": 1}},
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

"""Native parametric checks for prototype lookup followed by assembly-order inference."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "35368341e72e"
TASK_DIR = Path(__file__).resolve().parents[1]
PARAMETRIC_DIR = TASK_DIR / "workspace" / "parametric"
QUERY_ORDER = {"assembly": "query_order"}
FEWEST_FIRST = {"assembly": "fewest_cells_first"}


def _load(name: str):
    path = PARAMETRIC_DIR / f"{name}.py"
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    root = find_root(__file__)
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_contract_and_exact_canonical_default():
    adapter = _load("adapter")
    contract = json.loads((PARAMETRIC_DIR / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"assembly": ["query_order", "fewest_cells_first"]},
        "default": QUERY_ORDER,
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
    }
    canonical = _canonical_program()
    assert (PARAMETRIC_DIR / "canonical.rkt").read_bytes() == canonical.encode("utf-8")
    assert adapter.program(QUERY_ORDER) == canonical
    alternate = adapter.program(FEWEST_FIRST)
    assert alternate != canonical
    assert "active-cell-count" in alternate


def test_settings_seed_and_count_boundaries_are_strict():
    adapter = _load("adapter")
    for settings in (
        None,
        {},
        {"assembly": True},
        {"assembly": 0},
        {"assembly": "fewest"},
        {"assembly": "query_order", "extra": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
    for seed, demos, queries in (
        (True, 3, 4),
        (-1, 3, 4),
        (2**63, 3, 4),
        (1.0, 3, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, True, 4),
        (0, 3, 3),
        (0, 3, 5),
        (0, 3, True),
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, QUERY_ORDER, demos, queries)


def test_inputs_are_setting_independent_distinct_and_outputs_teach_the_setting():
    adapter = _load("adapter")
    canonical = adapter.generate(23, QUERY_ORDER, 3, 4)
    alternate = adapter.generate(23, FEWEST_FIRST, 3, 4)
    assert _inputs(canonical) == _inputs(alternate)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(serialized) == len(set(serialized)) == 7
    assert all(
        left["output"] != right["output"]
        for left, right in zip(
            canonical["train"] + canonical["test"],
            alternate["train"] + alternate["test"],
            strict=True,
        )
    )
    assert canonical["program_solution"] == adapter.program(QUERY_ORDER)
    assert alternate["program_solution"] == adapter.program(FEWEST_FIRST)


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
@pytest.mark.parametrize("settings", [QUERY_ORDER, FEWEST_FIRST])
def test_every_supported_demo_count_has_four_queries_and_no_tested_harmful_survivor(demos, settings):
    adapter = _load("adapter")
    prototype = _load("prototype")
    episode = adapter.generate(71 + demos, settings, demos, 4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert prototype.teaching_check(episode, settings)["survivors"] == [settings["assembly"]]
    assert prototype.teaching_check(episode, settings)["harmful_survivors"] == []
    for pair in episode["train"] + episode["test"]:
        assert prototype.validate_input(pair["input"]) == []
        assert pair["output"] == prototype.mirror(pair["input"], settings)
        assert 1 <= len(pair["output"]) <= 30
        assert 1 <= len(pair["output"][0]) <= 30


def test_minimum_and_maximum_counts_keep_fixed_query_prefix_and_substantive_thirty_canvas():
    adapter = _load("adapter")
    prototype = _load("prototype")
    minimum = adapter.generate(17, FEWEST_FIRST, 2, 4)
    maximum = adapter.generate(17, FEWEST_FIRST, 6, 4)
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"] == maximum["test"]
    assert [(len(p["input"]), len(p["input"][0])) for p in minimum["test"]] == [
        (9, 17),
        (14, 23),
        (22, 28),
        (30, 30),
    ]
    largest = minimum["test"][-1]
    metrics = prototype.input_metrics(largest["input"])
    assert metrics["input_shape"] == [30, 30]
    assert metrics["key_count"] == 5
    assert metrics["query_length"] == 7
    assert metrics["prototype_active_cells"] == [2, 3, 4, 5, 6]
    assert metrics["nonzero_cells"] >= 32
    assert metrics["content_row_span"] == 30
    assert metrics["content_col_span"] >= 28
    assert [len(largest["output"]), len(largest["output"][0])] == [3, 27]


def test_active_cell_intermediate_drives_stable_output_order_and_preserves_repeats():
    adapter = _load("adapter")
    prototype = _load("prototype")
    pair = adapter.generate(41, FEWEST_FIRST, 2, 4)["test"][-1]
    info = prototype.intermediate(pair["input"])
    counts = [row["active_cells"] for row in info["query_occurrences"]]
    sorted_counts = [row["active_cells"] for row in info["fewest_first_occurrences"]]
    assert counts != sorted_counts
    assert sorted_counts == sorted(counts)
    assert len(info["query_keys"]) > len(set(info["query_keys"]))
    assert len(info["fewest_first_keys"]) == len(info["query_keys"])
    assert pair["output"] == prototype.gallery(
        [row["prototype"] for row in info["fewest_first_occurrences"]]
    )


def test_public_turn_hides_private_state_future_queries_and_answers():
    adapter = _load("adapter")
    prototype = _load("prototype")
    episode = adapter.generate(5, FEWEST_FIRST, 3, 4)
    public = prototype.public_turn(episode, 0)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    assert public["test"][0]["input"] == episode["test"][0]["input"]
    assert public_challenge_bytes(public) == public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][0]]}
    )
    changed = deepcopy(episode)
    changed["settings"] = QUERY_ORDER
    changed["seed"] = -1
    changed["program_solution"] = "private rule text"
    changed["test"][0]["output"] = [[0]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_id(prototype.public_turn(changed, 0)) == public_challenge_id(public)
    public["train"][0]["input"][0][0] = 9
    assert prototype.public_turn(episode, 0)["train"][0]["input"][0][0] != 9
    for index in (-1, True, 4):
        with pytest.raises((TypeError, ValueError)):
            prototype.public_turn(episode, index)


def test_generation_is_deterministic_and_seed_changes_visible_inputs():
    adapter = _load("adapter")
    first = adapter.generate(101, QUERY_ORDER, 4, 4)
    second = adapter.generate(101, QUERY_ORDER, 4, 4)
    other = adapter.generate(102, QUERY_ORDER, 4, 4)
    assert first == second
    assert _inputs(first) != _inputs(other)
    assert hashlib.sha256(json.dumps(first, sort_keys=True).encode()).hexdigest() == hashlib.sha256(
        json.dumps(second, sort_keys=True).encode()
    ).hexdigest()

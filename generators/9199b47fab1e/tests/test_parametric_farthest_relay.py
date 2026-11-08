"""Behavioral checks for the native original-seed / farthest-relay family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CANONICAL = {"source_mode": "original_seeds"}
RELAY = {"source_mode": "farthest_relay"}


def adapter():
    assert ADAPTER_PATH.is_file(), "native farthest-relay adapter is missing"
    spec = importlib.util.spec_from_file_location(
        "test_9199b47fab1e_farthest_relay", ADAPTER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact(*rows: str) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


SINGLE_CHAMBER = compact(
    "000000000",
    "066666660",
    "060000060",
    "062000060",
    "060000060",
    "060000060",
    "060000060",
    "066666660",
    "000000000",
)


def test_default_program_is_byte_exact_canonical_authority():
    module = adapter()
    assert module.program(CANONICAL) == (PARAMETRIC / "canonical.rkt").read_text()
    assert module.program(CANONICAL).encode() == (PARAMETRIC / "canonical.rkt").read_bytes()


def test_farthest_relay_uses_primary_bfs_result_as_the_second_source():
    module = adapter()
    facts = module.analyze(SINGLE_CHAMBER)
    assert facts["relay"] == (6, 6)
    assert facts["primary_distances"][(6, 6)] == 7

    canonical = module.solve_python(SINGLE_CHAMBER, CANONICAL)
    relay = module.solve_python(SINGLE_CHAMBER, RELAY)
    wrong = module.solve_from_relay(SINGLE_CHAMBER, (3, 2))
    assert canonical[3][2] == 3 and canonical[6][6] == 4
    assert relay[6][6] == 3 and relay[3][2] == 4
    assert relay != canonical
    assert relay != wrong


@pytest.mark.parametrize("settings", [CANONICAL, RELAY])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_independent_counts_unique_inputs_prefix_stability_and_large_stress(settings, demos):
    module = adapter()
    episode = module.generate(17, settings, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == module.program(settings)

    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == demos + 4
    assert all(pair["output"] == module.solve_python(pair["input"], settings) for pair in pairs)
    assert all(1 <= len(pair["input"]) <= 30 and 1 <= len(pair["input"][0]) <= 30 for pair in pairs)

    stress = episode["test"][3]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    nonzero = sum(value != 0 for row in stress for value in row)
    assert 150 <= nonzero <= 500
    assert any(stress[r][c] != 0 for r in (0, 29) for c in range(30))
    assert any(stress[r][c] != 0 for c in (0, 29) for r in range(30))

    one = module.generate(17, settings, demos=demos, queries=1)
    assert one["train"] == episode["train"]
    assert one["test"][0] == episode["test"][0]


def test_input_stream_is_matched_across_settings_and_demonstrations_identify_the_rule():
    module = adapter()
    canonical = module.generate(23, CANONICAL, demos=3, queries=4)
    relay = module.generate(23, RELAY, demos=3, queries=4)
    assert [pair["input"] for pair in canonical["train"] + canonical["test"]] == [
        pair["input"] for pair in relay["train"] + relay["test"]
    ]
    assert module.teaching_check(canonical)["ok"] is True
    assert module.teaching_check(relay)["ok"] is True
    assert all(
        left["output"] != right["output"]
        for left, right in zip(canonical["train"], relay["train"])
    )


def test_public_turn_hides_private_fields_future_queries_and_total_count():
    module = adapter()
    four = module.generate(31, RELAY, demos=3, queries=4)
    four["settings"] = copy.deepcopy(RELAY)
    four["private_note"] = "must not leak"
    first = module.public_turn(four, 0)
    one = module.public_turn(module.generate(31, RELAY, demos=3, queries=1), 0)
    assert first == one
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    for index in range(4):
        turn = module.public_turn(four, index)
        assert turn["test"] == [{"input": four["test"][index]["input"]}]


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"source_mode": True},
        {"source_mode": "nearest_relay"},
        {"source_mode": "original_seeds", "extra": 1},
    ],
)
def test_undeclared_settings_fail_closed(settings):
    with pytest.raises(ValueError):
        adapter().program(settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 3, 4),
        (-1, 3, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, True, 4),
        (0, 3, 0),
        (0, 3, 5),
        (0, 3, True),
    ],
)
def test_invalid_request_bounds_fail_before_generation(seed, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, CANONICAL, demos=demos, queries=queries)


def test_solver_rejects_malformed_or_out_of_domain_grids():
    module = adapter()
    bad = [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(7)], [[10] * 7 for _ in range(7)]]
    for grid in bad:
        with pytest.raises(ValueError):
            module.solve_python(grid, RELAY)

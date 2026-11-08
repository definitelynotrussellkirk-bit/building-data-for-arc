"""Independent native continuation contract tests, authored before implementation."""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = ROOT / "generators/80271cb9b303/workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
POLICIES = ("repeat", "reverse_cycle", "bounce")
CANONICAL_SHA = "7278144d22eaa349ae7e24bf6ab2f771d19577b1f1fa66513c54d79861440c22"


def setting(policy):
    return {"continuation": policy}


@lru_cache(None)
def load_adjacent(filename):
    path = PARAMETRIC / filename
    name = "_native_test_80271cb9b303_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    assert Path(module.__file__).resolve() == path.resolve()
    return module


@pytest.fixture(scope="module")
def family():
    return load_adjacent("native_family.py")


@pytest.fixture(scope="module")
def adapter():
    return load_adjacent("adapter.py")


@pytest.fixture(scope="module")
def canonical():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    matches = [row for line in path.read_text().splitlines()
               if (row := json.loads(line))["task_id"] == "80271cb9b303"]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture(scope="module")
def racket():
    with _local_imports(RUNTIME, PARAMETRIC):
        apply_program, identity, bridge = _real_evaluator(RUNTIME)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply_program
        finally:
            bridge.close()


def literal_phase_fixture():
    """Distinct periods, partial phases, leading zeros, and trailing motif zeros.

    The p3 first row ends at phase1; the p4 second row ends at phase2.
    Tail expectations below are literal, not computed by a solver or family helper.
    """
    grid = [
        [2, 5, 7, 2, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 3, 6, 9, 0, 3, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [5, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    expected = {
        "repeat": [
            [2, 5, 7, 2, 5, 7, 2, 5, 7, 2, 5, 7, 2, 5, 7, 2],
            [0, 3, 6, 9, 0, 3, 6, 9, 0, 3, 6, 9, 0, 3, 6, 9],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [5, 0, 0, 5, 0, 0, 5, 0, 0, 5, 0, 0, 5, 0, 0, 5],
            [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        ],
        "reverse_cycle": [
            [2, 5, 7, 2, 5, 2, 7, 5, 2, 7, 5, 2, 7, 5, 2, 7],
            [0, 3, 6, 9, 0, 3, 6, 3, 0, 9, 6, 3, 0, 9, 6, 3],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [5, 0, 0, 5, 0, 0, 5, 0, 0, 5, 0, 0, 5, 0, 0, 5],
            [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        ],
        "bounce": [
            [2, 5, 7, 2, 5, 7, 5, 2, 5, 7, 5, 2, 5, 7, 5, 2],
            [0, 3, 6, 9, 0, 3, 6, 9, 6, 3, 0, 3, 6, 9, 6, 3],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [5, 0, 0, 5, 0, 0, 0, 5, 0, 0, 0, 5, 0, 0, 0, 5],
            [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        ],
    }
    return grid, expected


def literal_short_prefix_fixture():
    """A period5 with no repeated residue, period2, and R=0 constant row."""
    grid = [
        [2, 7, 2, 6, 9, 0, 0, 0, 0, 0, 0, 0],
        [0, 4, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0],
        [8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    expected = {
        "repeat": [
            [2, 7, 2, 6, 9, 2, 7, 2, 6, 9, 2, 7],
            [0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4],
            [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        ],
        "reverse_cycle": [
            [2, 7, 2, 6, 9, 6, 2, 7, 2, 9, 6, 2],
            [0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4],
            [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        ],
        "bounce": [
            [2, 7, 2, 6, 9, 6, 2, 7, 2, 7, 2, 6],
            [0, 4, 0, 4, 0, 4, 0, 4, 0, 4, 0, 4],
            [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8],
        ],
    }
    return grid, expected


def assert_grid(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    assert all(type(row) is list and len(row) == width
               and all(type(cell) is int and 0 <= cell <= 9 for cell in row) for row in grid)


def pairs(episode):
    return episode["train"] + episode["test"]


def inputs(episode):
    return [pair["input"] for pair in pairs(episode)]


def test_repeat_preserves_canonical_bytes_and_all_four_official_pairs(family, canonical, racket):
    source = family.program(setting("repeat"))
    assert source == canonical["program_solution"]
    assert hashlib.sha256(source.encode()).hexdigest() == CANONICAL_SHA
    official = canonical["train"] + canonical["test"]
    assert len(official) == 4
    for pair in official:
        assert family.apply_claim(pair["input"], setting("repeat")) == pair["output"]
        assert racket(source, pair["input"]) == pair["output"]


@pytest.mark.parametrize("policy", POLICIES)
def test_literal_phases_keep_leading_zeros_and_use_each_rows_minimal_period(family, racket, policy):
    grid, expected = literal_phase_fixture()
    before = copy.deepcopy(grid)
    assert family.apply_claim(grid, setting(policy)) == expected[policy]
    assert racket(family.program(setting(policy)), grid) == expected[policy]
    assert grid == before


@pytest.mark.parametrize("policy", POLICIES)
def test_short_prefix_period_two_and_rightmost_column_zero_are_supported(family, racket, policy):
    grid, expected = literal_short_prefix_fixture()
    assert family.apply_claim(grid, setting(policy)) == expected[policy]
    assert racket(family.program(setting(policy)), grid) == expected[policy]


@pytest.mark.parametrize("policy", POLICIES)
def test_blank_width_one_and_full_width_rows_are_preserved(family, racket, policy):
    for grid in ([[0]], [[7]], [[0], [6], [0]],
                 [[0, 0, 0, 0], [0, 2, 0, 3], [5, 0, 5, 2]]):
        assert family.apply_claim(grid, setting(policy)) == grid
        assert racket(family.program(setting(policy)), grid) == grid


@pytest.mark.parametrize("policy", POLICIES)
def test_known_prefix_and_shape_are_preserved_and_outputs_are_fresh(family, policy):
    grid, expected = literal_phase_fixture()
    before = copy.deepcopy(grid)
    result = family.apply_claim(grid, setting(policy))
    for old, new in zip(grid, result):
        if any(old):
            right = max(i for i, value in enumerate(old) if value)
            assert old[:right + 1] == new[:right + 1]
    result[0][0] = (result[0][0] + 1) % 10
    assert grid == before
    assert family.apply_claim(grid, setting(policy)) == expected[policy]
    description = family.describe(grid, setting(policy))
    assert description["input_shape"] == [5, 16]
    assert description["output_shape"] == [5, 16]


@pytest.mark.parametrize("bad", [None, "repeat", {}, {"continuation": "unknown"},
    {"continuation": True}, {"continuation": 1}, {"continuation": ["repeat"]},
    {"continuation": "repeat", "extra": 0}])
def test_settings_require_exact_key_and_declared_string(family, bad):
    with pytest.raises((TypeError, ValueError)):
        family.program(bad)
    with pytest.raises((TypeError, ValueError)):
        family.apply_claim([[0]], bad)
    with pytest.raises((TypeError, ValueError)):
        family.describe([[0]], bad)
    with pytest.raises((TypeError, ValueError)):
        family.generate(0, bad, 3, 1)


@pytest.mark.parametrize("bad", [-1, 2**63, True, False, 0.0, "0", None])
def test_seed_requires_literal_integer_in_supported_range(family, bad):
    with pytest.raises((TypeError, ValueError)):
        family.generate(bad, setting("repeat"), 3, 1)


@pytest.mark.parametrize("demos,queries", [(2, 1), (7, 1), (3, 0), (3, 5),
    (True, 1), (3, True), (3.0, 1), (3, 1.0), ("3", 1), (3, None)])
def test_demo_query_counts_are_independent_strict_bounds(family, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        family.generate(0, setting("repeat"), demos, queries)


@pytest.mark.parametrize("bad", [None, [], [[]], (), [(0, 1)], [[0], [0, 1]],
    [[True]], [[1.0]], [["1"]], [[-1]], [[10]], [[0] * 31], [[0] for _ in range(31)]])
def test_grid_rejects_nonliteral_cells_ragged_rows_and_oversize(family, bad):
    for policy in POLICIES:
        with pytest.raises((TypeError, ValueError)):
            family.apply_claim(bad, setting(policy))
        with pytest.raises((TypeError, ValueError)):
            family.describe(bad, setting(policy))


def test_generate_uses_local_rng_matched_banks_and_independent_prefixes(family):
    rng_before = random.getstate()
    banks = {policy: family.generate(17, setting(policy), 6, 4) for policy in POLICIES}
    assert all(len(ep["train"]) == 6 and len(ep["test"]) == 4 for ep in banks.values())
    base_inputs = inputs(banks["repeat"])
    for policy, bank in banks.items():
        assert inputs(bank) == base_inputs
        for demos in range(3, 7):
            for queries in range(1, 5):
                short = family.generate(17, setting(policy), demos, queries)
                assert short["train"] == bank["train"][:demos]
                assert short["test"] == bank["test"][:queries]
        for pair in pairs(bank):
            assert_grid(pair["input"])
            assert_grid(pair["output"])
            assert family.apply_claim(pair["input"], setting(policy)) == pair["output"]
    assert random.getstate() == rng_before


def test_generate_is_deterministic_fresh_and_accepts_maximum_seed(family):
    first = family.generate(0, setting("bounce"), 3, 1)
    second = family.generate(0, setting("bounce"), 3, 1)
    assert first == second
    preserved = copy.deepcopy(second)
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    first["test"][0]["output"][0][0] = (first["test"][0]["output"][0][0] + 1) % 10
    assert second == preserved
    assert family.generate(0, setting("bounce"), 3, 1) == preserved
    last = family.generate(2**63 - 1, setting("repeat"), 3, 1)
    assert len(last["train"]) == 3 and len(last["test"]) == 1


@pytest.mark.parametrize("seed", [0, 17])
def test_first_three_demonstrations_distinguish_all_declared_policies(family, seed):
    episodes = [family.generate(seed, setting(policy), 3, 1) for policy in POLICIES]
    assert all(inputs(ep) == inputs(episodes[0]) for ep in episodes)
    signatures = {json.dumps([pair["output"] for pair in ep["train"]]) for ep in episodes}
    assert len(signatures) == 3


@pytest.mark.parametrize("policy", POLICIES)
def test_generated_labels_and_substantive_thirty_by_thirty_query(family, racket, policy):
    episode = family.generate(0, setting(policy), 3, 4)
    for pair in episode["train"] + [episode["test"][0], episode["test"][3]]:
        assert racket(family.program(setting(policy)), pair["input"]) == pair["output"]
    stress = episode["test"][3]
    grid, output = stress["input"], stress["output"]
    assert len(grid) == len(grid[0]) == len(output) == len(output[0]) == 30
    assert sum(cell != 0 for row in grid for cell in row) >= 200
    assert sum(any(row) for row in grid) >= 20
    assert any(grid[0]) and any(grid[-1]) and any(row[0] for row in grid)
    assert any(old == 0 and new != 0 for a, b in zip(grid, output) for old, new in zip(a, b))
    assert family.describe(grid, setting(policy))["output_shape"] == [30, 30]


@pytest.mark.parametrize("policy", POLICIES)
def test_extra_rivals_are_executable_complete_programs(family, racket, policy):
    rivals = family.rivals(setting(policy))
    assert type(rivals) is dict and rivals
    grid = family.generate(0, setting(policy), 3, 1)["train"][0]["input"]
    for name, program in rivals.items():
        assert isinstance(name, str) and name and isinstance(program, str) and program
        assert_grid(racket(program, grid))


def test_adapter_exposes_literal_semantics_and_matched_generated_episode(adapter, family, canonical):
    grid, expected = literal_phase_fixture()
    assert adapter.program(setting("repeat")) == canonical["program_solution"]
    for policy in POLICIES:
        assert adapter.apply_claim(grid, setting(policy)) == expected[policy]
        assert adapter.generate(0, setting(policy), 3, 1) == family.generate(0, setting(policy), 3, 1)


def test_public_turn_contains_only_demonstrations_and_current_query_input(family):
    episode = family.generate(0, setting("bounce"), 3, 4)
    public = family.public_turn(episode, 0)
    expected = {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    assert public == expected
    hidden = copy.deepcopy(episode)
    hidden["seed"] = "PRIVATE-SEED"
    hidden["_private"] = {"secret": "PRIVATE-METADATA"}
    hidden["settings"] = {"secret": "PRIVATE-SETTINGS"}
    hidden["test"][0]["output"] = [[9]]
    hidden["test"][1:] = [{"input": [[8]], "output": [[7]]} for _ in range(3)]
    assert family.public_turn(hidden, 0) == public
    one_query = family.generate(0, setting("bounce"), 3, 1)
    assert family.public_turn(one_query, 0) == public
    snapshot = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = (public["train"][0]["input"][0][0] + 1) % 10
    public["test"][0]["input"][0][0] = (public["test"][0]["input"][0][0] + 1) % 10
    assert episode == snapshot
    for index in (1, 2, 3):
        current = family.public_turn(episode, index)
        assert current == {"train": episode["train"], "test": [{"input": episode["test"][index]["input"]}]}
    for bad in (-1, 4, True, 0.0, "0", None):
        with pytest.raises((TypeError, ValueError, IndexError)):
            family.public_turn(episode, bad)

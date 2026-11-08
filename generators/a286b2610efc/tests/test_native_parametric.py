"""Focused invariants for the opt-in repeated-completion family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PROTOTYPE = HOME / "workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


@pytest.fixture(scope="module")
def adapter():
    path = PROTOTYPE / "adapter.py"
    assert path.is_file(), "The native parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_a286b2610efc_native", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def settings(rounds: int = 1) -> dict[str, int]:
    return {"rounds": rounds}


def canonical() -> str:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == HOME.name:
            return row["program_solution"]
    raise AssertionError("canonical task row missing")


def fingerprint(grid):
    return tuple(map(tuple, grid))


def changed_cells(before, after):
    return {
        (r, c)
        for r, row in enumerate(before)
        for c, value in enumerate(row)
        if value != after[r][c]
    }


def test_native_contract_and_exact_canonical_default(adapter):
    contract = json.loads((PROTOTYPE / "promotion.json").read_text(encoding="utf-8"))
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"rounds": [1, 2]}
    assert contract["default"] == settings()
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3
    assert adapter.program(settings()) == canonical()
    assert (PROTOTYPE / "canonical.rkt").read_text(encoding="utf-8") == canonical()
    assert adapter.program(settings(2)) != canonical()


@pytest.mark.parametrize("rounds", [1, 2])
def test_every_program_uses_the_real_rule_wrapper(adapter, rounds):
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = wrap_rule(adapter.program(settings(rounds)))
    assert isinstance(wrapped, str) and wrapped.strip()


@pytest.mark.parametrize(
    "bad",
    [None, {}, {"rounds": 0}, {"rounds": 3}, {"rounds": True},
     {"rounds": 1.0}, {"rounds": "1"}, {"rounds": 1, "extra": 2}],
)
def test_invalid_settings_are_rejected(adapter, bad):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad, 3, 4)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "0"])
def test_seed_boundary_is_strict(adapter, seed):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, settings(), 3, 4)


@pytest.mark.parametrize(
    "demos,queries",
    [(1, 4), (7, 4), (True, 4), (3.0, 4), (3, 0), (3, 5),
     (3, True), (3, 4.0)],
)
def test_count_boundaries_are_strict(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings(), demos, queries)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_counts_are_prefix_stable_and_inputs_match_across_settings(adapter, seed):
    short = adapter.generate(seed, settings(), 2, 1)
    long = adapter.generate(seed, settings(), 6, 4)
    other = adapter.generate(seed, settings(2), 6, 4)

    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert len(long["train"]) == 6 and len(long["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in long[split]]
    assert len({fingerprint(grid) for grid in inputs}) == 10
    for split in ("train", "test"):
        assert [pair["input"] for pair in long[split]] == [pair["input"] for pair in other[split]]
    assert all(
        first["output"] != second["output"]
        for first, second in zip(long["train"][:2], other["train"][:2])
    )


@pytest.mark.parametrize("height,width", [(14, 14), (14, 30), (30, 14), (30, 30)])
def test_substantive_minimum_and_maximum_canvases(adapter, height, width):
    grid = adapter.sample_input(17, "test", 3, height=height, width=width)
    assert len(grid) == height and all(len(row) == width for row in grid)
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    assert min(r for r, _ in nonzero) == 0 and max(r for r, _ in nonzero) == height - 1
    assert min(c for _, c in nonzero) == 0 and max(c for _, c in nonzero) == width - 1
    assert {(int(r >= height / 2), int(c >= width / 2)) for r, c in nonzero} == {
        (0, 0), (0, 1), (1, 0), (1, 1)
    }
    assert len(nonzero) >= (28 if height == width == 30 else 12)

    once = adapter.transform(grid, settings())
    twice = adapter.transform(grid, settings(2))
    assert once != twice
    assert len(changed_cells(grid, once)) >= 6
    assert len(changed_cells(once, twice)) >= 6
    assert all(len(row) == width for row in once + twice)


def test_second_round_consumes_cells_created_by_the_first(adapter):
    grid = adapter.sample_input(23, "test", 3, height=30, width=30)
    original = copy.deepcopy(grid)
    intermediate = adapter.complete_once(grid)
    result = adapter.complete_once(intermediate)

    assert adapter.transform(grid, settings(2)) == result
    assert adapter.transform(grid, settings()) == intermediate
    assert result != intermediate != grid
    assert grid == original

    second_only = changed_cells(intermediate, result)
    assert second_only
    # At least one second-stage write is enabled by a cell that A created: the
    # same location is not writable from the original grid in a single pass.
    direct = adapter.complete_once(grid)
    assert any(direct[r][c] == grid[r][c] and result[r][c] != intermediate[r][c]
               for r, c in second_only)


def test_first_two_demonstrations_identify_round_count(adapter):
    for seed in (0, 17, 91):
        one = adapter.generate(seed, settings(), 2, 4)
        two = adapter.generate(seed, settings(2), 2, 4)
        assert [pair["input"] for pair in one["train"]] == [pair["input"] for pair in two["train"]]
        assert all(a["output"] != b["output"] for a, b in zip(one["train"], two["train"]))


def test_rng_and_returned_values_are_isolated(adapter):
    random.seed(512)
    before = random.getstate()
    first = adapter.generate(31, settings(2), 3, 4)
    assert random.getstate() == before
    expected = adapter.generate(31, settings(2), 3, 4)
    assert first == expected
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert adapter.generate(31, settings(2), 3, 4) == expected


def test_public_projection_has_one_query_and_content_only_id(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = adapter.generate(17, settings(2), 3, 4)
    view = {"train": episode["train"], "test": episode["test"][:1]}
    raw = public_challenge_bytes(view)
    public = json.loads(raw)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert raw == public_challenge_bytes(adapter.generate(17, settings(2), 3, 1))
    assert public_challenge_id(view) == hashlib.sha256(raw).hexdigest()
    view["settings"] = {"secret": 812}
    view["program_solution"] = "secret"
    view["test"][0]["output"] = [[0]]
    assert public_challenge_bytes(view) == raw


def test_finite_self_review_rivals_are_distinct_parseable_programs(adapter):
    path = PROTOTYPE / "audit.py"
    assert path.is_file(), "The bounded self-review audit has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_a286b2610efc_audit", path)
    assert spec is not None and spec.loader is not None
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)

    from puzzle_generators.rule_wrap import wrap_rule

    programs = audit.rivals(adapter)
    assert set(programs) == {
        "one_sided_completion",
        "one_round",
        "two_rounds",
        "three_rounds",
        "horizontal_second_round_only",
        "vertical_second_round_only",
    }
    assert len(set(programs.values())) == len(programs)
    for source in programs.values():
        assert wrap_rule(source).strip()

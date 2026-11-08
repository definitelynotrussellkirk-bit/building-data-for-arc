"""Focused invariants for the native half-fill relay family."""
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
PARAMETRIC = HOME / "workspace" / "parametric"
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


@pytest.fixture(scope="module")
def adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "native parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_1a92a12bac06_native", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def settings(mode: str = "half_only") -> dict[str, str]:
    return {"mode": mode}


def canonical() -> str:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == HOME.name:
            return row["program_solution"]
    raise AssertionError("canonical task row missing")


def fingerprint(grid):
    return tuple(map(tuple, grid))


def test_native_contract_and_exact_canonical_default(adapter):
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"mode": ["half_only", "largest_relay"]}
    assert contract["default"] == settings()
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3
    assert adapter.program(settings()) == canonical()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical()
    assert adapter.program(settings("largest_relay")) != canonical()


@pytest.mark.parametrize("mode", ["half_only", "largest_relay"])
def test_every_program_parses_through_the_real_rule_wrapper(adapter, mode):
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = wrap_rule(adapter.program(settings(mode)))
    assert isinstance(wrapped, str) and wrapped.strip()


@pytest.mark.parametrize(
    "bad",
    [None, {}, {"mode": "other"}, {"mode": 1}, {"mode": True},
     {"mode": "half_only", "extra": 1}],
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
    relay = adapter.generate(seed, settings("largest_relay"), 6, 4)

    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert len(long["train"]) == 6 and len(long["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in long[split]]
    assert len({fingerprint(grid) for grid in inputs}) == 10
    for split in ("train", "test"):
        assert [pair["input"] for pair in long[split]] == [pair["input"] for pair in relay[split]]
    assert all(
        first["output"] != second["output"]
        for first, second in zip(long["train"][:2], relay["train"][:2])
    )


def test_each_input_has_a_unique_post_half_relay_and_two_selected_bar_tops(adapter):
    for seed in (0, 17, 91):
        episode = adapter.generate(seed, settings("largest_relay"), 6, 4)
        for pair in episode["train"] + episode["test"]:
            state = adapter.relay_state(pair["input"])
            assert state["unique_largest"] is True
            assert len(state["target_red_components"]) == 2
            assert pair["output"] == adapter.transform(pair["input"], settings("largest_relay"))
            assert pair["output"] != adapter.transform(pair["input"], settings())


def test_wrong_intermediate_counterfactual_changes_the_rank_inversion_case(adapter):
    grid = adapter.sample_input(0, "train", 0)
    state = adapter.relay_state(grid)
    correct = adapter.transform(grid, settings("largest_relay"))
    wrong = adapter.wrong_order_transform(grid)

    assert state["pre_largest_cells"] != state["post_largest_cells"]
    assert state["post_largest_size"] > state["post_second_size"]
    assert correct != wrong
    assert sum(value == 4 for row in wrong for value in row) == 6
    assert correct != adapter.transform(grid, settings())


@pytest.mark.parametrize("height,width", [(13, 14), (13, 30), (30, 14), (30, 30)])
def test_minimum_and_maximum_canvases_are_substantive(adapter, height, width):
    grid = adapter.sample_input(17, "test", 3, height=height, width=width)
    assert len(grid) == height and all(len(row) == width for row in grid)
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    assert len(nonzero) >= (45 if height == width == 30 else 24)
    assert {value for row in grid for value in row} >= {0, 2, 8}
    state = adapter.relay_state(grid)
    assert state["unique_largest"] is True
    assert len(state["target_red_components"]) == 2
    assert adapter.transform(grid, settings()) != adapter.transform(grid, settings("largest_relay"))


def test_racket_labels_match_python_claims(adapter):
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
    from puzzle_generators.rule_wrap import wrap_rule

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])

    grids = [adapter.sample_input(23, "train", i) for i in range(2)]
    with RacketBridge(max_calls_before_restart=64) as bridge:
        for mode in ("half_only", "largest_relay"):
            source = wrap_rule(adapter.program(settings(mode)))
            for grid in grids:
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                actual = bridge.eval_text(f"({source} {literal})")
                assert actual == adapter.transform(grid, settings(mode))


def test_generation_is_deterministic_fresh_and_global_random_pure(adapter):
    random.seed(512)
    before = random.getstate()
    first = adapter.generate(31, settings("largest_relay"), 3, 4)
    assert random.getstate() == before
    expected = adapter.generate(31, settings("largest_relay"), 3, 4)
    assert first == expected
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert adapter.generate(31, settings("largest_relay"), 3, 4) == expected


def test_public_projection_has_one_query_and_content_only_id(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = adapter.generate(17, settings("largest_relay"), 3, 4)
    for index in range(4):
        public = adapter.public_turn(episode, index)
        raw = public_challenge_bytes(public)
        expected = {
            "train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(episode["test"][index]["input"])}],
        }
        assert raw == public_challenge_bytes(expected)
        assert set(public) == {"train", "test"}
        assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
        assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()

        perturbed = copy.deepcopy(episode)
        for future in perturbed["test"][index + 1:]:
            future["input"] = [[9]]
            future["output"] = [[9]]
        perturbed["settings"] = {"secret": "changed"}
        perturbed["program_solution"] = "changed"
        assert public_challenge_bytes(adapter.public_turn(perturbed, index)) == raw

    single = adapter.generate(17, settings("largest_relay"), 3, 1)
    assert public_challenge_bytes(adapter.public_turn(single, 0)) == public_challenge_bytes(
        adapter.public_turn(episode, 0)
    )

    with pytest.raises((TypeError, ValueError)):
        adapter.public_turn(episode, True)
    with pytest.raises((TypeError, ValueError)):
        adapter.public_turn(episode, 4)


def test_finite_self_review_rivals_are_distinct_parseable_programs(adapter):
    path = PARAMETRIC / "audit.py"
    assert path.is_file(), "bounded self-review audit has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_1a92a12bac06_audit", path)
    assert spec is not None and spec.loader is not None
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)

    from puzzle_generators.rule_wrap import wrap_rule

    for mode in ("half_only", "largest_relay"):
        programs = audit.rival_programs(adapter, mode)
        assert len(programs) >= 6
        assert "other_setting" in programs
        if mode == "largest_relay":
            assert "wrong_intermediate" in programs
            assert "largest_original_red_mass" in programs
            assert "smallest_original_relay" in programs
        selected = adapter.program(settings(mode))
        assert selected not in programs.values()
        assert len(set(programs.values())) == len(programs)
        for source in programs.values():
            assert wrap_rule(source).strip()


def test_first_two_demonstrations_force_opposite_physical_relay_sides(adapter):
    for seed in (0, 17, 91):
        sides = []
        for index in (0, 1):
            grid = adapter.sample_input(seed, "train", index)
            target_cells = [cell for component in adapter.relay_state(grid)["target_red_components"] for cell in component]
            midpoint = len(grid[0]) / 2
            assert target_cells
            side = "left" if max(col for _, col in target_cells) < midpoint else "right"
            assert all((col < midpoint) == (side == "left") for _, col in target_cells)
            sides.append(side)
        assert sides == ["left", "right"]

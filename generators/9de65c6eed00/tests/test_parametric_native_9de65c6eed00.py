from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "9de65c6eed00"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER = HOME / "adapter.py"
CANONICAL = {"normalization_anchor": "top_left"}
ALTERNATIVE = {"normalization_anchor": "relative_corner"}


def load_adapter():
    assert ADAPTER.is_file(), "native parametric adapter is missing"
    name = "_test_9de65c6eed00_adapter"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_source() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return next(iter(programs))


def all_inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_native_contract_exists_and_default_program_is_exact():
    adapter = load_adapter()
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert contract["parameters"] == {
        "normalization_anchor": ["top_left", "relative_corner"]
    }
    assert contract["default"] == CANONICAL
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3
    assert adapter.program(CANONICAL) == canonical_source()
    assert (HOME / "canonical.rkt").read_text(encoding="utf-8") == canonical_source()
    assert adapter.program(ALTERNATIVE) != canonical_source()


@pytest.mark.parametrize("seed", [0, 17, 41])
def test_prefix_stability_matched_inputs_and_unique_pairs(seed):
    adapter = load_adapter()
    short = adapter.generate(seed, CANONICAL, 2, 1)
    long = adapter.generate(seed, CANONICAL, 6, 4)
    alternate = adapter.generate(seed, ALTERNATIVE, 6, 4)

    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert [p["input"] for p in long["train"]] == [p["input"] for p in alternate["train"]]
    assert [p["input"] for p in long["test"]] == [p["input"] for p in alternate["test"]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs(long)}) == 10
    assert any(a["output"] != b["output"] for a, b in zip(long["train"], alternate["train"]))
    assert any(a["output"] != b["output"] for a, b in zip(long["test"], alternate["test"]))


@pytest.mark.parametrize("settings", [CANONICAL, ALTERNATIVE])
@pytest.mark.parametrize("seed", [0, 17])
def test_minimum_lesson_teaches_setting_and_claims_match_transform(settings, seed):
    adapter = load_adapter()
    episode = adapter.generate(seed, settings, 2, 4)
    for pair in episode["train"] + episode["test"]:
        facts = adapter.analyze(pair["input"])
        assert facts["relative_corner"] in adapter.CORNERS
        assert pair["output"] == adapter.transform(
            pair["input"], settings["normalization_anchor"]
        )
    certificate = adapter.lesson_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]]
    )
    assert certificate["surviving_settings"] == [settings]
    assert certificate["ambiguous_rivals"] == []
    assert certificate["query_count"] == 4


def test_corner_coverage_and_substantive_30x30_stress():
    adapter = load_adapter()
    episode = adapter.generate(17, ALTERNATIVE, 6, 4)
    demo_corners = [adapter.analyze(pair["input"])["relative_corner"] for pair in episode["train"]]
    query_corners = [adapter.analyze(pair["input"])["relative_corner"] for pair in episode["test"]]
    assert demo_corners[:2] == ["top_right", "bottom_left"]
    assert set(query_corners) == set(adapter.CORNERS)

    stress_pair = next(pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
    grid = stress_pair["input"]
    facts = adapter.analyze(grid)
    assert facts["object_count"] == 2
    assert facts["large_size"] >= 90
    assert facts["small_size"] >= 50
    assert sum(cell != 0 for row in grid for cell in row) >= 150
    occupied = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    assert {r for r, _ in occupied} & {0, 29}
    assert {c for _, c in occupied} & {0, 29}
    anchored = {
        tuple(tuple(row) for row in adapter.transform_with_anchor(grid, corner))
        for corner in adapter.CORNERS
    }
    assert len(anchored) == 4


def test_public_turn_hides_private_fields_and_first_turn_is_query_count_invariant():
    adapter = load_adapter()
    one = adapter.generate(5, ALTERNATIVE, 3, 1)
    four = adapter.generate(5, ALTERNATIVE, 3, 4)
    first_one = adapter.public_turn(one, 0)
    first_four = adapter.public_turn(four, 0)
    assert first_one == first_four
    assert set(first_one) == {"train", "test"}
    assert len(first_one["test"]) == 1
    assert set(first_one["test"][0]) == {"input"}
    assert hashlib.sha256(public_challenge_bytes(first_one)).hexdigest() == public_challenge_id(first_one)

    altered = copy.deepcopy(four)
    altered.update(seed=999, settings={"secret": True}, program_solution="private")
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [{"input": [[8]], "output": [[7]]}] * 3
    assert adapter.public_turn(altered, 0) == first_four
    encoded = json.dumps(first_four, sort_keys=True)
    for private_name in ("settings", "program_solution", "certificate", "seed", "sampling"):
        assert private_name not in encoded


@pytest.mark.parametrize(
    "args",
    [
        (True, CANONICAL, 3, 4),
        (-1, CANONICAL, 3, 4),
        (2**63, CANONICAL, 3, 4),
        (0, {}, 3, 4),
        (0, {"normalization_anchor": "bad"}, 3, 4),
        (0, {"normalization_anchor": "top_left", "extra": 1}, 3, 4),
        (0, CANONICAL, 1, 4),
        (0, CANONICAL, 7, 4),
        (0, CANONICAL, 3, 0),
        (0, CANONICAL, 3, 5),
    ],
)
def test_invalid_requests_are_rejected(args):
    adapter = load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    assert bridge.runtime_identity["backend"] == "racket"
    assert bridge.runtime_identity["protected"] is True

    def apply(program, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")

    yield apply
    bridge.close()


@pytest.mark.parametrize("seed", [0, 17])
def test_protected_racket_matches_python_claims(seed, racket):
    adapter = load_adapter()
    for settings in (CANONICAL, ALTERNATIVE):
        episode = adapter.generate(seed, settings, 2, 4)
        source = adapter.program(settings)
        for pair in episode["train"] + episode["test"]:
            assert racket(source, pair["input"]) == pair["output"]


def test_wrong_intermediate_corner_changes_final_output(racket):
    adapter = load_adapter()
    episode = adapter.generate(0, ALTERNATIVE, 2, 4)
    pair = next(
        pair
        for pair in episode["test"]
        if adapter.analyze(pair["input"])["relative_corner"] != "top_left"
    )
    actual_corner = adapter.analyze(pair["input"])["relative_corner"]
    wrong_corner = "top_left" if actual_corner != "top_left" else "bottom_right"
    intended = racket(adapter.program(ALTERNATIVE), pair["input"])
    wrong = racket(adapter.counterfactual_program(wrong_corner), pair["input"])
    assert intended == pair["output"]
    assert wrong != intended

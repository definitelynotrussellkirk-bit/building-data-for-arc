from __future__ import annotations
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _real_evaluator


def load_native():
    path = HOME / "workspace/parametric/native_family.py"
    spec = importlib.util.spec_from_file_location("test_public_eval_e376de54_native", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def official_pairs():
    challenges = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())
    solutions = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())
    task = challenges["e376de54"]
    pairs = [(p["input"], p["output"]) for p in task["train"]]
    pairs.extend((p["input"], out) for p, out in zip(task["test"], solutions["e376de54"]))
    return pairs


def test_python_and_racket_reproduce_every_official_pair():
    native = load_native()
    program = (HOME / "reference.rkt").read_text()
    apply, identity, bridge = _real_evaluator(RUNTIME)
    try:
        assert identity["protected"] is True
        for inp, expected in official_pairs():
            before = copy.deepcopy(inp)
            assert native.solve(inp, "middle") == expected
            assert apply(program, inp) == expected
            assert inp == before
    finally:
        bridge.close()


def _vertical_example():
    grid = [[7] * 11 for _ in range(10)]
    for c, color, length in [(2, 2, 2), (5, 4, 4), (8, 6, 6)]:
        for r in range(2, 2 + length):
            grid[r][c] = color
    return grid


def test_longest_setting_uses_longest_segment_not_positional_middle():
    native = load_native()
    grid = _vertical_example()
    middle = native.plan(grid, "middle")
    longest = native.plan(grid, "longest")
    assert middle["lengths"] == [2, 4, 6]
    assert middle["target_length"] == 4
    assert longest["target_length"] == 6
    assert native.solve(grid, "middle") != native.solve(grid, "longest")


def test_exact_canonical_resource_and_program_contract():
    native = load_native()
    canonical = (HOME / "reference.rkt").read_bytes()
    assert (HOME / "workspace/parametric/canonical.rkt").read_bytes() == canonical
    assert native.program({"target_mode": "middle"}).encode() == canonical
    assert native.program({"target_mode": "longest"}) != native.CANONICAL
    assert native.PARAMETERS == {"target_mode": ["middle", "longest"]}
    assert native.DEFAULT == {"target_mode": "middle"}
    assert native.LIMITS == {"demos": [2, 6], "queries": [1, 4]}


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_matched_inputs_prefixes_freshness_and_teaching(seed):
    native = load_native()
    middle = {"target_mode": "middle"}
    longest = {"target_mode": "longest"}
    full = native.generate(seed, middle, 6, 4)
    other = native.generate(seed, longest, 6, 4)
    assert full == native.generate(seed, middle, 6, 4)
    pairs = full["train"] + full["test"]
    assert [p["input"] for p in pairs] == [p["input"] for p in other["train"] + other["test"]]
    assert len({json.dumps(p["input"]) for p in pairs}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(full["train"][:2], other["train"][:2]))
    assert full["program_solution"] == native.program(middle)
    for demos, queries in ((2, 1), (3, 4), (6, 2)):
        short = native.generate(seed, middle, demos, queries)
        assert short["train"] == full["train"][:demos]
        assert short["test"] == full["test"][:queries]
    assert (len(native.generate(seed, middle)["train"]), len(native.generate(seed, middle)["test"])) == (3, 4)
    automatic = native.generate(seed)
    assert automatic == native.generate(seed)
    assert automatic["program_solution"] in {native.program(middle), native.program(longest)}
    pristine = copy.deepcopy(full)
    full["train"][0]["input"][0][0] = 99
    assert native.generate(seed, middle, 6, 4) == pristine


def test_profiles_cover_all_orientations_and_two_substantive_30x30_scenes():
    native = load_native()
    demos, queries = native.input_bank(17)
    states = [native.plan(grid) for grid in demos + queries]
    assert {tuple(state["direction"]) for state in states} == {(0, 1), (1, 0), (1, 1), (1, -1)}
    assert {state["anchor_side"] for state in states} == {"minimum", "maximum"}
    large = [grid for grid in demos + queries if len(grid) == len(grid[0]) == 30]
    assert len(large) == 2 and large[0] != large[1]
    for grid in large:
        state = native.plan(grid)
        assert len(state["segments"]) >= 7
        assert sum(state["lengths"]) >= 90
        assert state["target_length"] != max(state["lengths"])


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"demos": 1}, {"demos": 7}, {"demos": 2.0},
    {"queries": 0}, {"queries": 5}, {"queries": False},
    {"settings": {}}, {"settings": {"target_mode": True}},
])
def test_invalid_episode_boundaries(kwargs):
    native = load_native()
    with pytest.raises(ValueError):
        native.generate(**{"seed": 17, **kwargs})


def test_query_presentation_order_varies_without_changing_bank():
    native = load_native()
    orders = []
    for seed in range(8):
        _, queries = native.input_bank(seed)
        orders.append(tuple((len(g), len(g[0]), native.plan(g)["lengths"][0]) for g in queries))
    assert len(set(orders)) > 1


def selected_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("selected_e376de54_generator_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_root_generator_and_promotion_contract():
    native = load_native()
    module = selected_generator()
    tree = ast.parse((HOME / "generator.py").read_text())
    ids = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
           and any(isinstance(target, ast.Name) and target.id == "RULE_TASK_ID" for target in node.targets)
           and isinstance(node.value, ast.Constant)]
    assert ids == ["ee_e376de54"]
    normalized = " ".join((HOME / "reference.rkt").read_text().split())
    assert module.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    grid = module.generate(seed=17, sample_index=0, difficulty="hard")
    assert module.self_check(grid) == []
    assert grid == module.generate(seed=17, sample_index=0, difficulty="hard")
    assert grid != module.generate(seed=17, sample_index=1, difficulty="hard")
    with pytest.raises(ValueError):
        module.generate(seed=17, unknown=1)
    contract = json.loads((HOME / "workspace/parametric/promotion.json").read_text())
    assert contract["parameters"] == native.PARAMETERS
    assert contract["default"] == native.DEFAULT
    assert contract["limits"] == native.LIMITS
    assert contract["qualification_demos"] == 2
    for resource in contract["resources"]:
        path = (ROOT / resource).resolve()
        assert path.is_file() and path.is_relative_to((HOME / "workspace/parametric").resolve())

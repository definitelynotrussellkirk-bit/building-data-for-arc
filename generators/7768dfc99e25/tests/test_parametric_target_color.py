from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "7768dfc99e25"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
SOURCE = HOME / "workspace" / "parametric" / "prototype.py"
ADAPTER = HOME / "workspace" / "parametric" / "adapter.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing required prototype file: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prototype():
    return _load(SOURCE, "_target_color_prototype_test")


def adapter():
    return _load(ADAPTER, "_target_color_adapter_test")


def canonical_program() -> str:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task row missing")


def _racket_grid(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


@pytest.fixture(scope="module")
def racket_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge() as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True

        def apply(program: str, grid):
            return bridge.eval_text(f"({wrap_rule(program)} {_racket_grid(grid)})")

        yield apply


def test_default_program_is_exact_canonical_authority():
    assert prototype().program({"target_color": 2}) == canonical_program()


def test_literal_fixture_crops_the_selected_border_component():
    module = prototype()
    grid = [[0] * 8 for _ in range(8)]
    for row, col in [(0, 1), (1, 1), (1, 2), (2, 1)]:
        grid[row][col] = 2
    for row, col in [(5, 1), (5, 2)]:
        grid[row][col] = 2
    for row, col in [(5, 6), (6, 6), (7, 6), (7, 5)]:
        grid[row][col] = 3
    for row, col in [(2, 5), (2, 6)]:
        grid[row][col] = 3
    assert module.transform(grid, {"target_color": 2}) == [[2, 0], [2, 2], [2, 0]]
    assert module.transform(grid, {"target_color": 3}) == [[0, 3], [0, 3], [3, 3]]


def test_settings_share_inputs_and_demos_identify_target_color():
    module = prototype()
    red = module.generate(17, {"target_color": 2}, demos=3, queries=4)
    green = module.generate(17, {"target_color": 3}, demos=3, queries=4)
    inputs = lambda episode: [p["input"] for p in episode["train"] + episode["test"]]
    assert inputs(red) == inputs(green)
    assert module.fit_settings(red["train"]) == [{"target_color": 2}]
    assert module.fit_settings(green["train"]) == [{"target_color": 3}]
    assert all(a["output"] != b["output"] for a, b in zip(red["test"], green["test"]))


def test_counts_are_independent_and_four_queries_include_30x30_spread():
    module = prototype()
    short = module.generate(23, {"target_color": 2}, demos=2, queries=4)
    long = module.generate(23, {"target_color": 2}, demos=6, queries=4)
    assert short["test"] == long["test"]
    assert len(short["train"]) == 2 and len(long["train"]) == 6
    all_pairs = long["train"] + long["test"]
    serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in all_pairs]
    assert len(serial) == len(set(serial))
    assert [(len(p["input"]), len(p["input"][0])) for p in long["test"]] == [
        (12, 14),
        (18, 20),
        (24, 24),
        (30, 30),
    ]
    stress = long["test"][-1]["input"]
    points = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    rows = {r for r, _ in points}
    cols = {c for _, c in points}
    assert {0, 29} <= rows
    assert {0, 29} <= cols
    assert len(points) >= 18


def test_adapter_matches_prototype_and_rejects_bad_bounds():
    module = prototype()
    thin = adapter()
    settings = {"target_color": 3}
    assert thin.program(settings) == module.program(settings)
    assert thin.generate(5, settings, 2, 4) == module.generate(5, settings, 2, 4)
    for args in [(-1, settings, 2, 4), (0, settings, 1, 4), (0, settings, 2, 0), (0, settings, 2, 9)]:
        with pytest.raises(ValueError):
            thin.generate(*args)


def test_public_projection_is_private_metadata_and_answer_invariant():
    module = prototype()
    episode = module.generate(31, {"target_color": 3}, demos=3, queries=4)
    original = public_challenge_bytes(episode)
    original_id = public_challenge_id(episode)
    mutated = copy.deepcopy(episode)
    mutated["settings"] = {"private": "changed"}
    mutated["seed"] = 1000
    mutated["program_solution"] = "private changed"
    mutated["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(mutated) == original
    assert public_challenge_id(mutated) == original_id
    visible = json.loads(original)
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert hashlib.sha256(original).hexdigest() == original_id


def test_protected_racket_matches_every_label_for_both_settings(racket_apply):
    module = prototype()
    before = random.getstate()
    for setting in module.SETTINGS:
        episode = module.generate(7, setting, demos=2, queries=4)
        for pair in episode["train"] + episode["test"]:
            assert racket_apply(module.program(setting), pair["input"]) == pair["output"]
    assert random.getstate() == before


def test_invalid_settings_fail_loudly():
    module = prototype()
    for settings in [None, {}, {"target_color": 4}, {"target_color": True}, {"target_color": 2, "extra": 1}]:
        with pytest.raises((TypeError, ValueError)):
            module.generate(0, settings, demos=2, queries=4)

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "d2f8cb1c91b2"
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
    return _load(SOURCE, "_conflict_mode_prototype_test")


def adapter():
    return _load(ADAPTER, "_conflict_mode_adapter_test")


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


def literal_grid():
    return [
        [1, 2, 0, 5, 0, 0, 1, 5, 4, 0, 0, 5, 0, 0, 7],
        [0, 3, 0, 5, 0, 3, 2, 5, 0, 6, 0, 5, 8, 6, 0],
        [0, 0, 0, 5, 0, 0, 0, 5, 0, 0, 0, 5, 0, 0, 0],
    ]


def test_default_program_is_exact_canonical_authority():
    assert prototype().program({"conflict_mode": "marker"}) == canonical_program()


def test_literal_fixture_distinguishes_all_conflict_policies():
    module = prototype()
    grid = literal_grid()
    assert module.transform(grid, {"conflict_mode": "marker"}) == [
        [0, 0, 9], [8, 6, 0], [0, 0, 0]
    ]
    assert module.transform(grid, {"conflict_mode": "keep_x"}) == [
        [0, 0, 4], [8, 6, 0], [0, 0, 0]
    ]
    assert module.transform(grid, {"conflict_mode": "keep_y"}) == [
        [0, 0, 7], [8, 6, 0], [0, 0, 0]
    ]


def test_settings_share_inputs_and_demos_identify_conflict_mode():
    module = prototype()
    episodes = {
        setting["conflict_mode"]: module.generate(17, setting, demos=3, queries=4)
        for setting in module.SETTINGS
    }
    inputs = lambda episode: [p["input"] for p in episode["train"] + episode["test"]]
    assert len({json.dumps(inputs(episode), separators=(",", ":")) for episode in episodes.values()}) == 1
    for mode, episode in episodes.items():
        assert module.fit_settings(episode["train"]) == [{"conflict_mode": mode}]
    for index in range(4):
        outputs = {
            json.dumps(episode["test"][index]["output"], separators=(",", ":"))
            for episode in episodes.values()
        }
        assert len(outputs) == 3


def test_counts_are_independent_and_fixed_3x15_format_is_explicit():
    module = prototype()
    short = module.generate(23, {"conflict_mode": "marker"}, demos=2, queries=4)
    long = module.generate(23, {"conflict_mode": "marker"}, demos=6, queries=4)
    assert short["test"] == long["test"]
    assert len(short["train"]) == 2 and len(long["train"]) == 6
    pairs = long["train"] + long["test"]
    serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
    assert len(serial) == len(set(serial))
    assert all(len(pair["input"]) == 3 for pair in pairs)
    assert all(all(len(row) == 15 for row in pair["input"]) for pair in pairs)
    assert all(any(9 in row for row in pair["output"]) for pair in pairs)


def test_adapter_matches_prototype_and_rejects_bad_bounds():
    module = prototype()
    thin = adapter()
    settings = {"conflict_mode": "keep_y"}
    assert thin.program(settings) == module.program(settings)
    assert thin.generate(5, settings, 2, 4) == module.generate(5, settings, 2, 4)
    for args in [(-1, settings, 2, 4), (0, settings, 1, 4), (0, settings, 2, 0), (0, settings, 2, 9)]:
        with pytest.raises(ValueError):
            thin.generate(*args)


def test_public_projection_is_private_metadata_and_answer_invariant():
    module = prototype()
    episode = module.generate(31, {"conflict_mode": "keep_x"}, demos=3, queries=4)
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


def test_protected_racket_matches_every_label_for_all_settings(racket_apply):
    module = prototype()
    before = random.getstate()
    for setting in module.SETTINGS:
        episode = module.generate(7, setting, demos=2, queries=4)
        for pair in episode["train"] + episode["test"]:
            assert racket_apply(module.program(setting), pair["input"]) == pair["output"]
    assert random.getstate() == before


def test_invalid_settings_fail_loudly():
    module = prototype()
    bad = [
        None,
        {},
        {"conflict_mode": "first"},
        {"conflict_mode": 9},
        {"conflict_mode": "marker", "extra": 1},
    ]
    for settings in bad:
        with pytest.raises((TypeError, ValueError)):
            module.generate(0, settings, demos=2, queries=4)

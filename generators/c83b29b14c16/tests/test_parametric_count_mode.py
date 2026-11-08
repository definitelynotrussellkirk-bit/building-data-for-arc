from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c83b29b14c16"
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
    return _load(SOURCE, "_c83_count_mode_prototype_test")


def adapter():
    return _load(ADAPTER, "_c83_count_mode_adapter_test")


def canonical_program() -> str:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
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
    module = prototype()
    assert module.program({"required_count": 2}) == canonical_program()


def test_settings_share_inputs_and_demos_identify_required_count():
    module = prototype()
    two = module.generate(17, {"required_count": 2}, demos=3, queries=4)
    three = module.generate(17, {"required_count": 3}, demos=3, queries=4)
    visible_inputs = lambda episode: [p["input"] for p in episode["train"] + episode["test"]]
    assert visible_inputs(two) == visible_inputs(three)
    assert module.fit_settings(two["train"]) == [{"required_count": 2}]
    assert module.fit_settings(three["train"]) == [{"required_count": 3}]
    for left, right in zip(two["test"], three["test"]):
        assert left["output"] != right["output"]


def test_counts_are_independent_queries_are_distinct_and_include_real_30x30_stress():
    module = prototype()
    short = module.generate(23, {"required_count": 2}, demos=2, queries=4)
    long = module.generate(23, {"required_count": 2}, demos=6, queries=4)
    assert len(short["train"]) == 2 and len(long["train"]) == 6
    assert short["test"] == long["test"]
    all_pairs = long["train"] + long["test"]
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in all_pairs]
    assert len(serialized) == len(set(serialized))
    assert [(len(p["input"]), len(p["input"][0])) for p in long["test"]] == [
        (13, 17),
        (18, 18),
        (24, 20),
        (30, 30),
    ]
    stress = long["test"][-1]["input"]
    occupied_rows = {r for r, row in enumerate(stress) if any(row)}
    occupied_cols = {c for c in range(30) if any(stress[r][c] for r in range(30))}
    assert {0, 29} <= occupied_rows
    assert {0, 29} <= occupied_cols
    assert sum(value != 0 for row in stress for value in row) >= 14


def test_adapter_matches_prototype_and_enforces_request_bounds():
    module = prototype()
    thin = adapter()
    settings = {"required_count": 3}
    assert thin.program(settings) == module.program(settings)
    assert thin.generate(5, settings, 2, 4) == module.generate(5, settings, 2, 4)
    for args in [(-1, settings, 2, 4), (0, settings, 1, 4), (0, settings, 2, 0), (0, settings, 2, 9)]:
        with pytest.raises(ValueError):
            thin.generate(*args)


def test_public_projection_ignores_private_settings_program_and_query_answers():
    module = prototype()
    episode = module.generate(41, {"required_count": 3}, demos=3, queries=4)
    original = public_challenge_bytes(episode)
    original_id = public_challenge_id(episode)
    mutated = copy.deepcopy(episode)
    mutated["settings"] = {"private": "changed"}
    mutated["seed"] = 999999
    mutated["program_solution"] = "private program changed"
    mutated["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(mutated) == original
    assert public_challenge_id(mutated) == original_id
    visible = json.loads(original)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert hashlib.sha256(original).hexdigest() == original_id


def test_racket_executes_every_selected_label_for_both_settings(racket_apply):
    module = prototype()
    before = random.getstate()
    for setting in module.SETTINGS:
        episode = module.generate(7, setting, demos=2, queries=4)
        program = module.program(setting)
        for pair in episode["train"] + episode["test"]:
            assert racket_apply(program, pair["input"]) == pair["output"]
    assert random.getstate() == before


def test_invalid_settings_and_types_fail_loudly():
    module = prototype()
    bad = [
        None,
        {},
        {"required_count": 4},
        {"required_count": True},
        {"required_count": 2, "extra": 1},
    ]
    for settings in bad:
        with pytest.raises((TypeError, ValueError)):
            module.generate(0, settings, demos=2, queries=4)
    with pytest.raises(ValueError):
        module.generate(True, {"required_count": 2}, demos=2, queries=4)

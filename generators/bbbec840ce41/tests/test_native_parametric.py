"""Focused contracts for the native anti-diagonal relay family."""
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
    spec = importlib.util.spec_from_file_location("_test_bbbec840ce41_native", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def setting(finish: str = "copy_only") -> dict[str, str]:
    return {"finish": finish}


def canonical() -> str:
    from reviewer_support import find_root

    root = find_root(__file__)
    path = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    if not path.is_file():
        path = root / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == HOME.name:
            return row["program_solution"]
    raise AssertionError("canonical task row missing")


def fingerprint(grid):
    return tuple(map(tuple, grid))


def test_contract_and_exact_canonical_default(adapter):
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"finish": ["copy_only", "largest_after_copy"]}
    assert contract["default"] == setting()
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3
    assert adapter.program(setting()) == canonical()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical()
    assert adapter.program(setting("largest_after_copy")) != canonical()


@pytest.mark.parametrize("finish", ["copy_only", "largest_after_copy"])
def test_programs_parse_through_real_wrapper(adapter, finish):
    from puzzle_generators.rule_wrap import wrap_rule

    assert wrap_rule(adapter.program(setting(finish))).strip()


@pytest.mark.parametrize(
    "bad",
    [None, {}, {"finish": "other"}, {"finish": 1}, {"finish": True},
     {"finish": "copy_only", "extra": 1}],
)
def test_invalid_settings_are_rejected(adapter, bad):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad, 3, 4)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "0"])
def test_seed_boundary_is_strict(adapter, seed):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, setting(), 3, 4)


@pytest.mark.parametrize(
    "demos,queries",
    [(1, 4), (7, 4), (True, 4), (3.0, 4), (3, 0), (3, 5),
     (3, True), (3, 4.0)],
)
def test_count_boundaries_are_strict(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, setting(), demos, queries)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_counts_are_prefix_stable_distinct_and_matched(adapter, seed):
    short = adapter.generate(seed, setting(), 2, 1)
    long = adapter.generate(seed, setting(), 6, 4)
    relay = adapter.generate(seed, setting("largest_after_copy"), 6, 4)

    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert len(long["train"]) == 6 and len(long["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in long[split]]
    assert len({fingerprint(grid) for grid in inputs}) == 10
    for split in ("train", "test"):
        assert [p["input"] for p in long[split]] == [p["input"] for p in relay[split]]
    assert all(a["output"] != b["output"] for a, b in zip(long["train"], relay["train"]))


def test_constructed_rank_inversion_is_real_and_causal(adapter):
    for seed in (0, 17, 91):
        grid = adapter.sample_input(seed, "train", 0)
        state = adapter.relay_state(grid)
        correct = adapter.transform(grid, setting("largest_after_copy"))
        wrong = adapter.wrong_intermediate_transform(grid)

        assert state["pre_largest_size"] > state["relay_source_size"]
        assert state["post_largest_size"] == 2 * state["relay_source_size"]
        assert state["post_largest_size"] > state["post_second_size"]
        assert state["pre_largest_cells"] != state["post_largest_cells"]
        assert correct != wrong
        assert correct != adapter.transform(grid, setting())
        assert sum(cell == 4 for row in correct for cell in row) == state["post_largest_size"]


@pytest.mark.parametrize("n", [8, 10, 16, 20, 28, 30])
def test_minimum_and_maximum_scenes_are_substantive(adapter, n):
    grid = adapter.sample_input(23, "test", 3, n=n)
    assert len(grid) == n and all(len(row) == n for row in grid)
    nonzero = sum(cell != 0 for row in grid for cell in row)
    assert nonzero >= (26 if n == 30 else 8)
    state = adapter.relay_state(grid)
    assert state["unique_post_largest"] is True
    assert state["pre_largest_cells"] != state["post_largest_cells"]
    assert adapter.transform(grid, setting()) != adapter.transform(grid, setting("largest_after_copy"))


def test_racket_labels_match_python_claims(adapter):
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
    from puzzle_generators.rule_wrap import wrap_rule

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [adapter.sample_input(41, "train", i) for i in range(2)]
    with RacketBridge(max_calls_before_restart=64) as bridge:
        for finish in ("copy_only", "largest_after_copy"):
            source = wrap_rule(adapter.program(setting(finish)))
            for grid in grids:
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                assert bridge.eval_text(f"({source} {literal})") == adapter.transform(grid, setting(finish))


def test_generation_is_deterministic_fresh_and_global_random_pure(adapter):
    random.seed(512)
    before = random.getstate()
    first = adapter.generate(31, setting("largest_after_copy"), 3, 4)
    assert random.getstate() == before
    expected = adapter.generate(31, setting("largest_after_copy"), 3, 4)
    assert first == expected
    first["train"][0]["input"][0][0] = 4
    first["test"][0]["output"][0][0] = 4
    assert adapter.generate(31, setting("largest_after_copy"), 3, 4) == expected


def test_public_projection_is_one_query_and_content_only(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = adapter.generate(17, setting("largest_after_copy"), 3, 4)
    for index in range(4):
        public = adapter.public_turn(episode, index)
        raw = public_challenge_bytes(public)
        expected = {
            "train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(episode["test"][index]["input"])}],
        }
        assert raw == public_challenge_bytes(expected)
        assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
        assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()

        hidden = copy.deepcopy(episode)
        hidden["settings"] = {"secret": "changed"}
        hidden["program_solution"] = "changed"
        for future in hidden["test"][index + 1:]:
            future["input"] = [[9]]
            future["output"] = [[9]]
        assert public_challenge_bytes(adapter.public_turn(hidden, index)) == raw

    single = adapter.generate(17, setting("largest_after_copy"), 3, 1)
    assert public_challenge_bytes(adapter.public_turn(single, 0)) == public_challenge_bytes(
        adapter.public_turn(episode, 0)
    )


def test_audit_declares_parseable_distinct_rivals(adapter):
    path = PARAMETRIC / "audit.py"
    assert path.is_file(), "bounded self-review audit has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_bbbec840ce41_audit", path)
    assert spec is not None and spec.loader is not None
    audit = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = audit
    spec.loader.exec_module(audit)

    from puzzle_generators.rule_wrap import wrap_rule

    for finish in ("copy_only", "largest_after_copy"):
        programs = audit.rival_programs(adapter, finish)
        assert len(programs) >= 5
        assert "other_setting" in programs
        if finish == "largest_after_copy":
            assert "wrong_intermediate" in programs
            assert "four_connected" in programs
        selected = adapter.program(setting(finish))
        assert selected not in programs.values()
        assert len(programs) == len(set(programs.values()))
        for source in programs.values():
            assert wrap_rule(source).strip()

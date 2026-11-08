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
PARAM = HOME / "workspace" / "parametric"
RUNTIME = HOME.parents[1] / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_adapter():
    path = PARAM / "adapter.py"
    assert path.is_file(), "native adapter missing"
    name = "_test_dbe_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def settings(finish="fill_only"):
    return {"finish": finish}


def fingerprint(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_contract_and_exact_canonical_default():
    adapter = load_adapter()
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["parameters"] == {"finish": ["fill_only", "cue_selected_region"]}
    assert contract["default"] == settings()
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2
    from reviewer_support import canonical_path, find_root
    programs = set()
    ledger = canonical_path(find_root(__file__))
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == HOME.name and isinstance(row.get("program_solution"), str):
            programs.add(row["program_solution"])
    assert len(programs) == 1
    assert adapter.program(settings()) == next(iter(programs))
    assert (PARAM / "canonical.rkt").read_text() == adapter.program(settings())
    assert adapter.program(settings("cue_selected_region")) != adapter.program(settings())


@pytest.mark.parametrize("bad", [None, {}, {"finish": "bad"}, {"finish": True}, {"finish": "fill_only", "x": 1}])
def test_invalid_settings_rejected(bad):
    adapter = load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad, 2, 1)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "0"])
def test_seed_boundary_is_strict(seed):
    adapter = load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, settings(), 2, 1)


@pytest.mark.parametrize("demos,queries", [(1, 1), (7, 1), (True, 1), (2.0, 1), (2, 0), (2, 5), (2, True)])
def test_count_boundaries_are_strict(demos, queries):
    adapter = load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings(), demos, queries)


@pytest.mark.parametrize("seed", [0, 17, 91])
def test_counts_are_prefix_stable_distinct_and_matched(seed):
    adapter = load_adapter()
    short = adapter.generate(seed, settings(), 2, 1)
    long = adapter.generate(seed, settings(), 6, 4)
    relay = adapter.generate(seed, settings("cue_selected_region"), 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    all_inputs = [pair["input"] for split in ("train", "test") for pair in long[split]]
    assert len({fingerprint(grid) for grid in all_inputs}) == 10
    for split in ("train", "test"):
        assert [p["input"] for p in long[split]] == [p["input"] for p in relay[split]]
    assert all(a["output"] != b["output"] for a, b in zip(long["train"], relay["train"], strict=True))


def test_two_demos_reverse_first_last_and_size_shortcuts():
    adapter = load_adapter()
    episode = adapter.generate(0, settings("cue_selected_region"), 2, 4)
    selected = [adapter.dependency_trace(pair["input"]) for pair in episode["train"]]
    assert {row["selected_order"] for row in selected} == {0, 1}
    assert {row["selected_is_largest"] for row in selected} == {True, False}
    assert adapter.teaching_check(episode)["status"] == "identified"
    assert adapter.teaching_check(episode)["surviving_rivals"] == []


def test_every_scene_has_unique_cue_selected_post_fill_region_and_skip_fill_differs():
    adapter = load_adapter()
    for seed in (0, 17, 91):
        episode = adapter.generate(seed, settings("cue_selected_region"), 6, 4)
        for pair in episode["train"] + episode["test"]:
            trace = adapter.dependency_trace(pair["input"])
            assert trace["red_component_count"] == 2
            assert trace["cue_touching_component_count"] == 1
            assert pair["output"] == adapter.solve(pair["input"], settings("cue_selected_region"))
            assert pair["output"] != adapter.skip_fill_solve(pair["input"])
            assert any(cell == 8 for row in pair["output"] for cell in row)
            assert any(cell == 2 for row in pair["output"] for cell in row)


def test_fourth_query_is_substantive_exact_30x30():
    adapter = load_adapter()
    grid = adapter.sample_input(17, "test", 3)
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    output = adapter.solve(grid, settings("fill_only"))
    assert sum(cell != 0 for row in output for cell in row) >= 300
    trace = adapter.dependency_trace(grid)
    assert trace["selected_size"] >= 100
    assert trace["unselected_size"] >= 80


def test_python_claims_match_protected_racket_on_representative_pairs():
    adapter = load_adapter()
    from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
    from puzzle_generators.rule_wrap import wrap_rule
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [adapter.sample_input(23, "train", i) for i in range(2)] + [adapter.sample_input(23, "test", 3)]
    with RacketBridge(max_calls_before_restart=64) as bridge:
        for finish in ("fill_only", "cue_selected_region"):
            source = wrap_rule(adapter.program(settings(finish)))
            for grid in grids:
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                assert bridge.eval_text(f"({source} {literal})") == adapter.solve(grid, settings(finish))


def test_generation_is_deterministic_fresh_and_global_random_pure():
    adapter = load_adapter()
    random.seed(803)
    before = random.getstate()
    first = adapter.generate(31, settings("cue_selected_region"), 3, 4)
    assert random.getstate() == before
    expected = adapter.generate(31, settings("cue_selected_region"), 3, 4)
    assert first == expected
    first["train"][0]["input"][0][0] = 8
    first["test"][0]["output"][0][0] = 8
    assert adapter.generate(31, settings("cue_selected_region"), 3, 4) == expected


def test_public_projection_is_one_query_and_content_only():
    adapter = load_adapter()
    from reviewer_support import public_challenge_bytes, public_challenge_id
    episode = adapter.generate(17, settings("cue_selected_region"), 3, 4)
    single = adapter.generate(17, settings("cue_selected_region"), 3, 1)
    for index in range(4):
        public = adapter.public_turn(episode, index)
        assert set(public) == {"train", "test"}
        assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
        raw = public_challenge_bytes(public)
        assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()
        hidden = copy.deepcopy(episode)
        hidden["settings"] = {"secret": "changed"}
        hidden["program_solution"] = "changed"
        for future in hidden["test"][index + 1:]:
            future["input"] = [[8]]
            future["output"] = [[8]]
        assert public_challenge_bytes(adapter.public_turn(hidden, index)) == raw
    assert public_challenge_bytes(adapter.public_turn(episode, 0)) == public_challenge_bytes(adapter.public_turn(single, 0))


def test_audit_tool_reports_bounded_clean_sweep_without_racket():
    path = PARAM / "audit.py"
    assert path.is_file(), "future-agent audit tool missing"
    name = "_test_dbe_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    report = module.run(seeds=range(4), protected=False)
    assert report["schema"] == "arcpuzzles-parametric-self-review-v1"
    assert report["episodes"] == 8
    assert report["pairs"] == 80
    assert report["harmful_survivors"] == []
    assert report["cue_selection_failures"] == []
    assert report["public_projection_failures"] == []

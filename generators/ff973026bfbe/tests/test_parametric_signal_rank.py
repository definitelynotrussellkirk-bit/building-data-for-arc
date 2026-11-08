"""Focused native-parametric contract tests for ff973026bfbe."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "ff973026bfbe"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
CANONICAL = "all_top_markers"
ALTERNATE = "signal_ranked_marker"
CANONICAL_SHA256 = "929315c16ae8e6f66d204f11aaf83890c3456c0faa370fec842cbd67dce04b85"


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode: dict) -> list:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _racket(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))


def test_adapter_contract_and_exact_canonical_default():
    adapter = _load("adapter")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"column_policy": [CANONICAL, ALTERNATE]},
        "default": {"column_policy": CANONICAL},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/audit_lessons.py",
        ],
    }
    canonical = _canonical_program()
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert (PARAMETRIC / "canonical.rkt").read_bytes() == canonical.encode()
    assert adapter.program({"column_policy": CANONICAL}) == canonical
    alternate = adapter.program({"column_policy": ALTERNATE})
    assert alternate != canonical
    assert "signal-size" in alternate
    assert "selected-col" in alternate
    assert "(nth mark-cols (- signal-size 1))" in alternate


def test_settings_seed_and_counts_fail_closed():
    adapter = _load("adapter")
    for bad in (
        {},
        {"column_policy": CANONICAL, "extra": 1},
        {"column_policy": "all_red_cells"},
        {"column_policy": 1},
    ):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for seed in (True, -1, 1.0, "1", 2**63):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(seed, {"column_policy": CANONICAL}, 3, 4)
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3, 0), (3, 5), (3, True)):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(1, {"column_policy": CANONICAL}, demos, queries)


def test_inputs_are_matched_distinct_and_every_label_changes_between_settings():
    adapter = _load("adapter")
    canonical = adapter.generate(23, {"column_policy": CANONICAL}, 3, 4)
    alternate = adapter.generate(23, {"column_policy": ALTERNATE}, 3, 4)
    assert _inputs(canonical) == _inputs(alternate)
    signatures = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(signatures) == len(set(signatures)) == 7
    for left, right in zip(
        canonical["train"] + canonical["test"],
        alternate["train"] + alternate["test"],
        strict=True,
    ):
        assert left["output"] != right["output"]


def test_demo_and_query_counts_are_independent_prefixes():
    adapter = _load("adapter")
    setting = {"column_policy": ALTERNATE}
    minimum = adapter.generate(41, setting, 2, 1)
    full_queries = adapter.generate(41, setting, 2, 4)
    full_demos = adapter.generate(41, setting, 6, 4)
    assert minimum["train"] == full_queries["train"] == full_demos["train"][:2]
    assert minimum["test"] == full_queries["test"][:1]
    assert full_queries["test"] == full_demos["test"]
    assert len(full_demos["train"]) == 6
    assert len(full_demos["test"]) == 4


def test_two_demonstrations_identify_each_setting_and_refute_shortcuts():
    adapter = _load("adapter")
    prototype = _load("prototype")
    for selected in (CANONICAL, ALTERNATE):
        episode = adapter.generate(57, {"column_policy": selected}, 2, 4)
        audit = prototype.audit_episode(episode, selected)
        assert audit["surviving_declared_rules"] == [selected]
        assert audit["query_disagreements_against_other_setting"] == 4
        assert audit["harmful_shortcut_survivors"] == []
        ranks = [prototype.analyze_input(pair["input"])["signal_size"] for pair in episode["train"]]
        assert ranks == [2, 5]
        row_counts = [prototype.analyze_input(pair["input"])["active_row_count"] for pair in episode["train"]]
        assert all(rank != count for rank, count in zip(ranks, row_counts, strict=True))


def test_four_queries_cover_spread_boundaries_and_exact_30x30_stress():
    adapter = _load("adapter")
    prototype = _load("prototype")
    episode = adapter.generate(73, {"column_policy": ALTERNATE}, 3, 4)
    dims = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert dims == [(14, 18), (19, 23), (24, 27), (30, 30)]
    metrics = [prototype.input_metrics(pair["input"]) for pair in episode["test"]]
    assert [row["signal_size"] for row in metrics] == [3, 6, 4, 5]
    assert all(row["top_marker_count"] >= row["signal_size"] + 2 for row in metrics)
    stress = metrics[-1]
    assert stress["height"] == stress["width"] == 30
    assert stress["active_row_count"] == 12
    assert stress["top_marker_count"] == 14
    assert stress["occupied_cells"] >= 35
    assert stress["canonical_painted_cells"] >= 160
    assert stress["boundary_sides"] == ["bottom", "left", "right", "top"]


def test_public_turn_masks_answers_program_setting_and_future_queries():
    adapter = _load("adapter")
    prototype = _load("prototype")
    episode = adapter.generate(89, {"column_policy": ALTERNATE}, 3, 4)
    public = prototype.public_turn(episode, 0)
    raw = public_challenge_bytes(public)
    parsed = json.loads(raw)
    assert len(parsed["test"]) == 1
    assert all(set(pair) == {"input"} for pair in parsed["test"])
    assert b"column_policy" not in raw
    assert b"program_solution" not in raw
    assert ALTERNATE.encode() not in raw
    assert public_challenge_id(public) == hashlib.sha256(raw).hexdigest()

    mutated = copy.deepcopy(episode)
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    assert public_challenge_id(prototype.public_turn(mutated, 0)) == public_challenge_id(public)


def test_python_claims_match_both_exact_racket_programs_on_boundary_and_stress_cases():
    adapter = _load("adapter")
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=32) as bridge:
        for selected in (CANONICAL, ALTERNATE):
            episode = adapter.generate(101, {"column_policy": selected}, 2, 4)
            source = adapter.program({"column_policy": selected})
            for pair in episode["train"] + episode["test"]:
                assert _racket(bridge, source, pair["input"]) == pair["output"]
        assert bridge.runtime_identity["protected"] is True


def test_causal_witness_wrong_rank_changes_the_selected_column():
    prototype = _load("prototype")
    witness = prototype.causal_witness(101)
    assert witness["signal_size"] == 3
    assert witness["wrong_signal_size"] == 4
    assert witness["selected_col"] != witness["wrong_selected_col"]
    assert witness["output"] != witness["counterfactual_output"]
    assert witness["differing_cells"] >= 2

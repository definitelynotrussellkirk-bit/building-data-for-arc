from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "8e52225f35b8"
ROOT = find_root(__file__)
PROTOTYPE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"
SETTINGS = (
    {"closure_order": "row_then_column"},
    {"closure_order": "column_then_row"},
)


def _load_prototype():
    assert PROTOTYPE.is_file(), "task-local closure-order prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_8e52225f35b8_closure_order", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load_prototype()


def _canonical_program() -> str:
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError(TASK_ID)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _panel_count(grid):
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    groups = 0
    c = 0
    while c < w:
        while c < w and c in dividers:
            c += 1
        if c >= w:
            break
        groups += 1
        while c < w and c not in dividers:
            c += 1
    return groups


def test_base_ordinary_draws_have_three_or_more_panels_and_pass_self_check():
    generator, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)
    for difficulty in ("easy", None, "medium", "hard"):
        for seed in range(8):
            grid = generator.generate(seed, seed % 3, difficulty=difficulty)
            assert len(grid) <= 30 and len(grid[0]) <= 30
            assert _panel_count(grid) >= 3
            assert generator.self_check(grid, difficulty=difficulty) == []


def test_default_program_is_exact_canonical_and_alternate_only_swaps_closure_order(proto):
    canonical = _canonical_program()
    assert proto.program(SETTINGS[0]) == canonical
    alternate = proto.program(SETTINGS[1])
    assert alternate != canonical
    assert "(define (double-close cells) (col-close (row-close cells)))" in canonical
    assert "(define (double-close cells) (row-close (col-close cells)))" in alternate
    restored = alternate.replace(
        "(define (double-close cells) (row-close (col-close cells)))",
        "(define (double-close cells) (col-close (row-close cells)))",
    )
    assert restored == canonical


def test_matched_inputs_minimum_teaching_and_substantive_30x30_query(proto):
    episodes = [proto.generate(17, setting, demos=2, queries=4) for setting in SETTINGS]
    assert _inputs(episodes[0]) == _inputs(episodes[1])
    assert all(len(ep["train"]) == 2 and len(ep["test"]) == 4 for ep in episodes)
    assert len({proto.digest(grid) for grid in _inputs(episodes[0])}) == 6
    assert [ep["certificate"]["survivors"] for ep in episodes] == [[SETTINGS[0]], [SETTINGS[1]]]
    assert all(set(ep["certificate"]["extra_refutations"]) == set(proto.RIVAL_NAMES) for ep in episodes)
    assert any(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))

    stress = episodes[0]["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    analysis = proto.analyze_scene(stress)
    assert analysis["panel_count"] >= 3
    assert analysis["mark_count"] >= 24
    assert analysis["occupied_rows"] >= 20
    assert analysis["occupied_columns"] >= 24
    assert analysis["order_disagreement_cells"] >= 4
    assert analysis["row_then_column_exactly_two"] >= 1
    assert analysis["column_then_row_exactly_two"] >= 1


def test_supported_demo_boundaries_keep_four_queries_and_prefixes(proto):
    for demos in (2, 6):
        episode = proto.generate(5, SETTINGS[0], demos=demos, queries=4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["certificate"]["survivors"] == [SETTINGS[0]]
    small = proto.generate(13, SETTINGS[1], demos=2, queries=4)
    large = proto.generate(13, SETTINGS[1], demos=6, queries=4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"]


def test_first_turn_projection_ignores_private_and_future_query_fields(proto):
    episode = proto.generate(31, SETTINGS[0], demos=3, queries=4)
    first = proto.public_turn(episode, 0)
    before = public_challenge_bytes(first)
    before_id = public_challenge_id(first)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}

    changed = copy.deepcopy(episode)
    changed["settings"] = SETTINGS[1]
    changed["program_solution"] = "private mutation"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[7]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == before
    assert public_challenge_id(proto.public_turn(changed, 0)) == before_id

    visible = copy.deepcopy(episode)
    visible["test"][0]["input"][0][0] = 7
    assert public_challenge_id(proto.public_turn(visible, 0)) != before_id


def test_order_intermediate_is_input_dependent_and_changes_final_majority(proto):
    episode = proto.generate(23, SETTINGS[0], demos=2, queries=4)
    witnesses = []
    for pair in episode["train"] + episode["test"]:
        first_row = proto.intermediate(pair["input"], SETTINGS[0])
        first_col = proto.intermediate(pair["input"], SETTINGS[1])
        out_row = proto.transform(pair["input"], SETTINGS[0])
        out_col = proto.transform(pair["input"], SETTINGS[1])
        if first_row != first_col and out_row != out_col:
            witnesses.append((first_row, first_col, out_row, out_col))
    assert witnesses
    assert all(a != b and c != d for a, b, c, d in witnesses)


def test_real_racket_labels_and_demo_only_certificates(proto):
    with RacketBridge(timeout=60) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for setting in SETTINGS:
            episode = proto.generate(37, setting, demos=2, queries=4)
            for pair in episode["train"] + episode["test"]:
                got = proto.execute_rule(episode["program_solution"], pair["input"], bridge=bridge)
                assert got == pair["output"]
            certificate = proto.certify(
                episode,
                execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge),
            )
            assert certificate["survivors"] == [setting]
            assert certificate["racket_checked"] is True


def test_invalid_contracts_duplicate_inputs_and_forged_private_fields_fail_closed(proto):
    for kwargs in (
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 3},
        {"demos": True, "queries": 4},
    ):
        with pytest.raises((TypeError, ValueError)):
            proto.generate(0, SETTINGS[0], **kwargs)
    with pytest.raises(ValueError):
        proto.generate(0, {"closure_order": "bbox"}, demos=3, queries=4)
    with pytest.raises((TypeError, ValueError)):
        proto.transform([[True]], SETTINGS[0])

    episode = proto.generate(0, SETTINGS[0], demos=3, queries=4)
    corrupt = copy.deepcopy(episode)
    corrupt["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError, match="label"):
        proto.certify(corrupt)

    stale = copy.deepcopy(episode)
    stale["program_solution"] = proto.program(SETTINGS[1])
    with pytest.raises(ValueError, match="program"):
        proto.certify(stale)

    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(duplicate)


def test_full_size_stress_coverage_is_not_seed_dependent(proto):
    for seed in (0, 2, 17, 37, 2**31 - 1):
        episode = proto.generate(seed, SETTINGS[0], demos=2, queries=4)
        stress = episode["test"][-1]["input"]
        analysis = proto.analyze_scene(stress)
        assert analysis["occupied_columns"] >= 24, (seed, analysis)

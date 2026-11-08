from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


TASK = "e06cc4c752b2"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location(f"parametric_{TASK}", PARAMETRIC / "prototype.py")
PROTO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PROTO)

CANONICAL = """(rule! (let ((dummy 0)) (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))) (for*/fold ((out g)) ((r (in-range (rows g))) (c (in-range (cols g)))) (let ((v (at g r c))) (if (and (not (= v 0)) (all? (lambda (d) (let ((nr (+ r (first d))) (nc (+ c (second d)))) (not (and (in-bounds? nr nc (rows g) (cols g)) (not (= (at g nr nc) 0)))))) dirs4)) (let* ((left (if (and (>= (- c 1) 0) (= (at out r (- c 1)) 0)) (set-cell out r (- c 1) v) out)) (right (if (and (< (+ c 1) (cols g)) (= (at left r (+ c 1)) 0)) (set-cell left r (+ c 1) v) left))) right) out)))))"""
CANONICAL_SETTINGS = {"finish": "canonical"}
SEQUENTIAL_SETTINGS = {"finish": "fill_largest_bbox"}


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_exact_canonical_program_and_distinct_sequential_program():
    assert PROTO.program(CANONICAL_SETTINGS) == CANONICAL
    assert (PARAMETRIC / "canonical.rkt").read_text() == CANONICAL
    sequential = PROTO.program(SEQUENTIAL_SETTINGS)
    assert sequential != CANONICAL
    assert "define intermediate" in sequential
    assert "objects intermediate 0" in sequential
    assert "pick-max" in sequential and "obj-size" in sequential
    assert "draw-rect-filled" in sequential


def test_generation_is_count_independent_and_setting_blind():
    short = PROTO.generate(17, CANONICAL_SETTINGS, demos=2, queries=1)
    long = PROTO.generate(17, CANONICAL_SETTINGS, demos=6, queries=4)
    alternate = PROTO.generate(17, SEQUENTIAL_SETTINGS, demos=6, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert _inputs(long) == _inputs(alternate)
    assert len({PROTO.digest(grid) for grid in _inputs(long)}) == 10


def test_minimum_two_demos_identify_each_setting_and_queries_transfer():
    for seed in (0, 17, 91):
        episodes = {
            name: PROTO.generate(seed, {"finish": name}, demos=2, queries=4)
            for name in ("canonical", "fill_largest_bbox")
        }
        for chosen, episode in episodes.items():
            survivors = []
            for candidate in ("canonical", "fill_largest_bbox"):
                settings = {"finish": candidate}
                if all(
                    PROTO.transform(pair["input"], settings) == pair["output"]
                    for pair in episode["train"]
                ):
                    survivors.append(candidate)
            assert survivors == [chosen]
            assert all(
                PROTO.transform(pair["input"], {"finish": chosen}) == pair["output"]
                for pair in episode["test"]
            )


def test_stage_b_uses_input_dependent_component_created_by_stage_a():
    episode = PROTO.generate(31, SEQUENTIAL_SETTINGS, demos=4, queries=4)
    summaries = [PROTO.stage_summary(pair["input"]) for pair in episode["train"]]
    assert len({tuple(summary["largest_anchor"]) for summary in summaries}) >= 2
    assert len({summary["largest_size"] for summary in summaries}) >= 2
    assert all(summary["largest_size"] >= 9 for summary in summaries)
    for pair, summary in zip(episode["train"], summaries):
        intermediate = PROTO.transform(pair["input"], CANONICAL_SETTINGS)
        assert summary["intermediate"] == intermediate
        assert pair["output"] != intermediate
        r1, c1, r2, c2 = summary["largest_bbox"]
        changed = {
            (r, c)
            for r, row in enumerate(pair["output"])
            for c, value in enumerate(row)
            if value != intermediate[r][c]
        }
        assert changed == {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        }
        assert all(pair["output"][r][c] == 9 for r, c in changed)


def test_query_bank_contains_substantive_30_by_30_transfer_case():
    episode = PROTO.generate(5, SEQUENTIAL_SETTINGS, demos=2, queries=4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes[-1] == (30, 30)
    large = episode["test"][-1]["input"]
    assert sum(value != 0 for row in large for value in row) >= 16
    summary = PROTO.stage_summary(large)
    assert summary["component_count"] >= 6
    assert summary["largest_size"] >= 18
    r1, c1, r2, c2 = summary["largest_bbox"]
    assert (r2 - r1 + 1) >= 6 and (c2 - c1 + 1) >= 11


def test_validation_rejects_bad_settings_counts_and_grids_without_mutation():
    with pytest.raises(ValueError, match="exactly finish"):
        PROTO.program({})
    with pytest.raises(ValueError, match="finish"):
        PROTO.program({"finish": "unknown"})
    with pytest.raises(ValueError, match="demos"):
        PROTO.generate(0, CANONICAL_SETTINGS, demos=1, queries=4)
    with pytest.raises(ValueError, match="queries"):
        PROTO.generate(0, CANONICAL_SETTINGS, demos=2, queries=5)
    bad = [[0, True, 0, 0, 0], [0, 2, 0, 0, 0], [0, 0, 0, 0, 0]]
    before = copy.deepcopy(bad)
    with pytest.raises(ValueError, match="exact integer"):
        PROTO.transform(bad, CANONICAL_SETTINGS)
    assert bad == before
    with pytest.raises(ValueError, match="color 9"):
        PROTO.transform([[0, 0, 0, 0, 0], [0, 9, 0, 0, 0], [0, 0, 0, 0, 0]], CANONICAL_SETTINGS)

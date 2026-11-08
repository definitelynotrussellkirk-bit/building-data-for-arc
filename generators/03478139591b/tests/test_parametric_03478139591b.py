from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


TASK = "03478139591b"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location(f"parametric_{TASK}", PARAMETRIC / "prototype.py")
PROTO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PROTO)

CANONICAL = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((color (find-first (lambda (c) (!= c 0)) (grid-colors g)))
                  (nc (casev color (hash 3 1 5 4 8 2) color)))
             (cellmap g (r c v) (if (!= v 0) 0 nc))))))"""
CANONICAL_SETTINGS = {"finish": "canonical"}
SEQUENTIAL_SETTINGS = {"finish": "mark_largest_boundary"}


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_exact_canonical_program_and_distinct_sequential_program():
    assert PROTO.program(CANONICAL_SETTINGS) == CANONICAL
    assert (PARAMETRIC / "canonical.rkt").read_text() == CANONICAL
    sequential = PROTO.program(SEQUENTIAL_SETTINGS)
    assert sequential != CANONICAL
    assert "objects intermediate 0" in sequential
    assert "obj-boundary-cells" in sequential


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
            for name in ("canonical", "mark_largest_boundary")
        }
        for chosen, episode in episodes.items():
            survivors = []
            for candidate in ("canonical", "mark_largest_boundary"):
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


def test_sequential_stage_tracks_input_dependent_largest_region_not_a_fixed_location():
    episode = PROTO.generate(31, SEQUENTIAL_SETTINGS, demos=3, queries=4)
    summaries = [PROTO.stage_summary(pair["input"]) for pair in episode["train"]]
    assert len({tuple(summary["largest_anchor"]) for summary in summaries}) >= 2
    assert len({summary["largest_size"] for summary in summaries}) >= 2
    for pair, summary in zip(episode["train"], summaries):
        intermediate = PROTO.transform(pair["input"], CANONICAL_SETTINGS)
        assert summary["intermediate"] == intermediate
        assert pair["output"] != intermediate
        changed = {
            (r, c)
            for r, row in enumerate(pair["output"])
            for c, value in enumerate(row)
            if value != intermediate[r][c]
        }
        assert changed == {tuple(cell) for cell in summary["largest_boundary"]}


def test_query_bank_covers_boundaries_and_substantive_30_by_30_scene():
    episode = PROTO.generate(5, SEQUENTIAL_SETTINGS, demos=2, queries=4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes[-1] == (30, 30)
    large = episode["test"][-1]["input"]
    nonzero = sum(cell != 0 for row in large for cell in row)
    assert nonzero >= 90
    assert PROTO.stage_summary(large)["component_count"] >= 3


def test_validation_rejects_bad_settings_counts_and_grids_without_mutation():
    with pytest.raises(ValueError, match="exactly finish"):
        PROTO.program({})
    with pytest.raises(ValueError, match="finish"):
        PROTO.program({"finish": "unknown"})
    with pytest.raises(ValueError, match="demos"):
        PROTO.generate(0, CANONICAL_SETTINGS, demos=1, queries=4)
    with pytest.raises(ValueError, match="queries"):
        PROTO.generate(0, CANONICAL_SETTINGS, demos=2, queries=5)
    bad = [[0, True], [3, 0]]
    before = copy.deepcopy(bad)
    with pytest.raises(ValueError, match="exact integer"):
        PROTO.transform(bad, CANONICAL_SETTINGS)
    assert bad == before

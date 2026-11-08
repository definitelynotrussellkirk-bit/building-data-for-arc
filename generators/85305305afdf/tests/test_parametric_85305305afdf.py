from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK = "85305305afdf"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location(f"parametric_{TASK}", PARAMETRIC / "prototype.py")
PROTO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PROTO)

CANONICAL_SETTINGS = {"finish": "canonical"}
SEQUENTIAL_SETTINGS = {"finish": "fill_largest_bbox"}


def _canonical_program():
    import json
    with canonical_path(find_root(__file__)).open() as handle:
        rows = [json.loads(line) for line in handle]
    return next(row["program_solution"] for row in rows if row["task_id"] == TASK)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_exact_canonical_program_and_nontrivial_sequential_program():
    canonical = _canonical_program()
    assert PROTO.program(CANONICAL_SETTINGS) == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    sequential = PROTO.program(SEQUENTIAL_SETTINGS)
    assert sequential != canonical
    assert "intermediate" in sequential
    assert "objects intermediate 0" in sequential
    assert "draw-rect-filled" in sequential


def test_generation_is_count_independent_and_setting_blind():
    short = PROTO.generate(17, CANONICAL_SETTINGS, demos=2, queries=1)
    long = PROTO.generate(17, CANONICAL_SETTINGS, demos=6, queries=4)
    alternate = PROTO.generate(17, SEQUENTIAL_SETTINGS, demos=6, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert _inputs(long) == _inputs(alternate)
    assert len({PROTO.digest(grid) for grid in _inputs(long)}) == 10


def test_two_demos_identify_both_settings_and_queries_transfer():
    for seed in (0, 17, 91):
        episodes = {
            name: PROTO.generate(seed, {"finish": name}, demos=2, queries=4)
            for name in ("canonical", "fill_largest_bbox")
        }
        for chosen, episode in episodes.items():
            survivors = []
            for candidate in ("canonical", "fill_largest_bbox"):
                setting = {"finish": candidate}
                if all(PROTO.transform(pair["input"], setting) == pair["output"] for pair in episode["train"]):
                    survivors.append(candidate)
            assert survivors == [chosen]
            assert all(
                PROTO.transform(pair["input"], {"finish": chosen}) == pair["output"]
                for pair in episode["test"]
            )


def test_step_b_uses_the_largest_component_created_by_step_a():
    episode = PROTO.generate(31, SEQUENTIAL_SETTINGS, demos=4, queries=4)
    summaries = [PROTO.stage_summary(pair["input"]) for pair in episode["train"] + episode["test"]]
    assert len({tuple(summary["largest_anchor"]) for summary in summaries}) >= 3
    assert len({summary["largest_size"] for summary in summaries}) >= 3
    for pair, summary in zip(episode["train"] + episode["test"], summaries):
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
        assert changed
        assert all(r1 <= r <= r2 and c1 <= c <= c2 for r, c in changed)
        assert summary["skip_a_output"] != pair["output"]


def test_query_bank_has_real_boundary_and_30_by_30_stress():
    episode = PROTO.generate(5, SEQUENTIAL_SETTINGS, demos=2, queries=4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes[-1] == (30, 30)
    large = episode["test"][-1]["input"]
    assert sum(cell != 0 for row in large for cell in row) >= 70
    summary = PROTO.stage_summary(large)
    assert summary["component_count"] >= 3
    assert summary["largest_size"] >= 20


def test_validation_rejects_bad_settings_counts_and_cells_without_mutation():
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

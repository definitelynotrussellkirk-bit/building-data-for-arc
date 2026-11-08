from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root

TASK = "863627ccef26"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location(f"parametric_{TASK}", PARAMETRIC / "prototype.py")
PROTO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PROTO)

CANONICAL_SETTINGS = {"merge_mode": "union_conflict_9"}
SEQUENTIAL_SETTINGS = {"merge_mode": "intersection_only"}


def _canonical_program():
    with canonical_path(find_root(__file__)).open() as handle:
        rows = [json.loads(line) for line in handle]
    return next(row["program_solution"] for row in rows if row["task_id"] == TASK)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_exact_canonical_program_and_transform_then_intersection_program():
    canonical = _canonical_program()
    assert PROTO.program(CANONICAL_SETTINGS) == canonical
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    sequential = PROTO.program(SEQUENTIAL_SETTINGS)
    assert sequential != canonical
    assert "infer-transform-name" in sequential
    assert "tq" in sequential
    assert "(and (not (= a 0)) (not (= b 0)))" in sequential


def test_generation_is_count_independent_and_matched_across_settings():
    short = PROTO.generate(17, CANONICAL_SETTINGS, demos=2, queries=1)
    long = PROTO.generate(17, CANONICAL_SETTINGS, demos=6, queries=4)
    alternate = PROTO.generate(17, SEQUENTIAL_SETTINGS, demos=6, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert _inputs(long) == _inputs(alternate)
    assert len({PROTO.digest(grid) for grid in _inputs(long)}) == 10


def test_two_demos_identify_each_merge_mode_and_queries_transfer():
    for seed in (0, 17, 91):
        episodes = {
            name: PROTO.generate(seed, {"merge_mode": name}, demos=2, queries=4)
            for name in ("union_conflict_9", "intersection_only")
        }
        for chosen, episode in episodes.items():
            survivors = []
            for candidate in ("union_conflict_9", "intersection_only"):
                setting = {"merge_mode": candidate}
                if all(PROTO.transform(pair["input"], setting) == pair["output"] for pair in episode["train"]):
                    survivors.append(candidate)
            assert survivors == [chosen]
            assert all(
                PROTO.transform(pair["input"], {"merge_mode": chosen}) == pair["output"]
                for pair in episode["test"]
            )


def test_intermediate_is_the_input_derived_transform_of_query():
    episode = PROTO.generate(31, SEQUENTIAL_SETTINGS, demos=4, queries=4)
    transforms = set()
    for pair in episode["train"] + episode["test"]:
        summary = PROTO.stage_summary(pair["input"])
        transforms.add(summary["transform"])
        assert summary["transformed_query"] != summary["query"]
        assert summary["overlap_cells"] > 0
        assert summary["carry_cells"] > 0
        assert summary["skip_a_output"] != pair["output"]
        assert pair["output"] == PROTO.transform(pair["input"], SEQUENTIAL_SETTINGS)
    assert len(transforms) >= 3


def test_query_bank_reaches_lawful_maximum_with_substantive_content():
    episode = PROTO.generate(5, SEQUENTIAL_SETTINGS, demos=2, queries=4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes[-1] == (9, 29)
    large = episode["test"][-1]["input"]
    nonzero = sum(cell != 0 for row in large for cell in row)
    assert nonzero >= 70
    assert all(len(row) <= 30 for row in large)
    assert PROTO.stage_summary(large)["panel_size"] == 9


def test_validation_rejects_bad_settings_counts_and_cells_without_mutation():
    with pytest.raises(ValueError, match="exactly merge_mode"):
        PROTO.program({})
    with pytest.raises(ValueError, match="merge_mode"):
        PROTO.program({"merge_mode": "unknown"})
    with pytest.raises(ValueError, match="demos"):
        PROTO.generate(0, CANONICAL_SETTINGS, demos=1, queries=4)
    with pytest.raises(ValueError, match="queries"):
        PROTO.generate(0, CANONICAL_SETTINGS, demos=2, queries=5)
    bad = [[0, True], [3, 0]]
    before = copy.deepcopy(bad)
    with pytest.raises(ValueError, match="exact integer"):
        PROTO.transform(bad, CANONICAL_SETTINGS)
    assert bad == before

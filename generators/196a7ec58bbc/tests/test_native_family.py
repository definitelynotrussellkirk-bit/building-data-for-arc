"""Native object selection and quadrant-family contract, not production tests."""
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PATH = HOME / "workspace/parametric/native_family.py"
SPEC = importlib.util.spec_from_file_location("quadrant_native_test", PATH)
family = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(family)


def inputs(episode):
    return [p["input"] for split in ("train", "test") for p in episode[split]]


def test_exact_canonical_source_and_retained_handedness():
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    record = Catalog(find_root(HOME)).get("196a7ec58bbc")
    exact = {v["program_solution"] for v in record["variants"]}
    assert {family.program()} == exact
    assert family.python_apply([[1, 1], [1, 0]]) == [
        [1, 1, 1, 1], [1, 0, 0, 1],
        [1, 0, 0, 1], [1, 1, 1, 1]]


@pytest.mark.parametrize("bad", [True, -1, 2**63, 0.0, "0", None])
def test_exact_bounded_seed(bad):
    with pytest.raises(ValueError):
        family.generate(bad)


@pytest.mark.parametrize("kwargs", [
    {"demos": True}, {"demos": 1}, {"demos": 7}, {"demos": 3.0},
    {"queries": False}, {"queries": 0}, {"queries": 5}, {"queries": "4"},
])
def test_independent_count_limits(kwargs):
    with pytest.raises(ValueError):
        family.generate(0, **kwargs)


@pytest.mark.parametrize("settings", [
    {"source_mode": "crop"}, {"handedness": False}, {"unknown": "whole"},
    [], "clockwise", {"source_mode": None},
])
def test_strict_settings(settings):
    with pytest.raises(ValueError):
        family.generate(0, settings)


def test_selection_discards_interior_distractor_and_is_not_bbox_ranking():
    episode = family.generate(0, {"source_mode": "largest_component"}, 2, 4)
    info = family.analyze_scene(episode["train"][0]["input"])
    selected = info["selected"]
    assert selected["size"] == 21
    assert info["selected_bbox_side"] == 5
    assert max((c["bbox"][2]-c["bbox"][0]+1)*(c["bbox"][3]-c["bbox"][1]+1)
               for c in info["components"]) > 25
    assert sum(x != 0 for row in info["intermediate"] for x in row) == 21
    assert len({x for row in info["intermediate"] for x in row}) == 2
    r0,c0,r1,c1 = selected["bbox"]
    raw = [row[c0:c1+1] for row in episode["train"][0]["input"][r0:r1+1]]
    assert raw != info["intermediate"]


def test_small_dense_object_stays_four_connected():
    mask = family._dense_mask(4)
    grid = [[int((r,c) in mask) for c in range(4)] for r in range(4)]
    assert len(family.components(grid)) == 1
    assert family.analyze_scene(grid)["selected"]["size"] == 12


def test_counts_and_settings_leave_input_bank_unchanged():
    for seed in (0, 1, 17, 2**63-1):
        base = family.generate(seed, demos=6, queries=4)
        assert len({repr(g) for g in inputs(base)}) == 10
        for setting in family.SETTINGS:
            full = family.generate(seed, setting, demos=6, queries=4)
            short = family.generate(seed, setting, demos=2, queries=1)
            assert inputs(full) == inputs(base)
            assert short["train"] == full["train"][:2]
            assert short["test"] == full["test"][:1]
            assert full["program_solution"] == family.program(setting)
            assert full["meta"]["candidate_attempts"] == 10


def test_real_minimum_and_thirty_by_thirty_outputs():
    for setting in family.SETTINGS:
        episode = family.generate(17, setting, demos=6, queries=4)
        assert len(episode["train"][2]["input"]) == 2
        assert len(episode["train"][2]["output"]) == 4
        for pair in (episode["train"][5], episode["test"][3]):
            assert len(pair["input"]) == 15
            assert len(pair["output"]) == 30
            assert all(len(row) == 30 for row in pair["output"])
            assert sum(c != 0 for row in pair["output"] for c in row) >= 200
            assert all(any(pair["output"][r][c] for r in range(r0,r0+15)
                           for c in range(c0,c0+15))
                       for r0,c0 in ((0,0),(0,15),(15,0),(15,15)))


def test_first_two_demonstrations_teach_all_four_settings():
    for seed in range(8):
        for intended in family.SETTINGS:
            episode = family.generate(seed, intended, demos=2, queries=4)
            survivors = [s for s in family.SETTINGS if all(
                family.python_apply(p["input"], s) == p["output"]
                for p in episode["train"])]
            assert survivors == [intended]
            for p in episode["train"] + episode["test"]:
                assert family.python_apply(p["input"], intended) == p["output"]


def test_two_demo_core_refutes_fixed_five_by_five_source():
    episode = family.generate(0, {"source_mode":"largest_component"}, demos=2, queries=4)
    assert [family.analyze_scene(p["input"])["selected_bbox_side"]
            for p in episode["train"]] == [5,4]
    assert [len(p["output"]) for p in episode["train"]] == [10,8]


@pytest.mark.parametrize("grid", [[], [[0]], [[0]*16 for _ in range(16)],
    [[True,0],[1,1]], [[1,1],[1]], [[1,0,0],[0,1,0],[0,0,0]]])
def test_rejects_invalid_or_tied_component_domain(grid):
    with pytest.raises(ValueError):
        family.analyze_scene(grid)

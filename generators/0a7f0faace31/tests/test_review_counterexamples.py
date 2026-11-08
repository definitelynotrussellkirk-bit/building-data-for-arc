"""Counterexamples discovered by independent review after the initial repair."""
import pytest

import importlib.util
from pathlib import Path

_HELPER_SPEC = importlib.util.spec_from_file_location("review_test_geometry", Path(__file__).with_name("test_public_contract.py"))
_HELPER = importlib.util.module_from_spec(_HELPER_SPEC)
_HELPER_SPEC.loader.exec_module(_HELPER)
gen, geometry, bbox = _HELPER.gen, _HELPER.geometry, _HELPER.bbox
from reviewer_support import canonical_pairs, find_root

POLICIES = ("widest_eligible_bbox", "widest_aspect_eligible", "sparsest_eligible_bbox",
            "smallest_nonscalar", "smallest_nonsolid")


def shape_rival(grid, policy):
    eligible = geometry(grid)[2]
    def crop(cells):
        r0,c0,r1,c1 = bbox(cells)
        return [row[c0:c1+1] for row in grid[r0:r1+1]]
    def dims(cells):
        r0,c0,r1,c1 = bbox(cells)
        return r1-r0+1, c1-c0+1
    if policy == "smallest_nonscalar":
        eligible = [cells for cells in eligible if len(cells)>1]
    elif policy == "smallest_nonsolid":
        eligible = [cells for cells in eligible if len({v for row in crop(cells) for v in row})>1]
    if not eligible:
        return [[5]]
    if policy == "widest_eligible_bbox":
        chosen = max(eligible, key=lambda cells:dims(cells)[1])
    elif policy == "widest_aspect_eligible":
        chosen = max(eligible, key=lambda cells:dims(cells)[1]/dims(cells)[0])
    elif policy == "sparsest_eligible_bbox":
        chosen = min(eligible, key=lambda cells:len(cells)/(dims(cells)[0]*dims(cells)[1]))
    else:
        chosen = min(eligible, key=len)
    return crop(chosen)


@pytest.mark.parametrize("policy", POLICIES)
def test_additional_shape_rivals_fit_the_actual_canonical_pairs(policy):
    for pair in canonical_pairs(gen.TASK_ID, root=find_root(__file__)):
        assert shape_rival(pair["input"], policy) == pair["output"]


@pytest.mark.parametrize("policy", POLICIES)
def test_teaching_refutes_shape_rivals_found_by_independent_review(policy):
    for seed in (1,18):
        for index in (0,1,3):
            grid = gen.generate(seed,index)
            assert shape_rival(grid,policy) != geometry(grid)[-1], (policy,seed,index)


def test_declared_rivals_return_valid_grids_when_their_selection_set_is_empty():
    # The production census scores every rival on every pair, even when a prior
    # demonstration already refuted it. An abstention is not a grid prediction.
    for seed in range(10):
        for index in range(12):
            grid = gen.generate(seed,index)
            for name, rival in gen.LESSON_COMPETITORS.items():
                output = rival(grid)
                assert isinstance(output,list) and output and isinstance(output[0],list) and output[0], (name,seed,index,output)
                assert all(len(row)==len(output[0]) for row in output), (name,seed,index)
                assert all(type(value) is int and 0<=value<=9 for row in output for value in row)

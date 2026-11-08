"""Behavioral tests for the proposed reflection/component native family."""
from pathlib import Path
import importlib.util
import json
import random

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load(name):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"Native {name} implementation is missing"
    spec = importlib.util.spec_from_file_location(f"reflection_test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid(n, colored):
    result = [[0] * n for _ in range(n)]
    for color, cells in colored.items():
        for r, c in cells:
            result[r][c] = color
    return result


@pytest.mark.parametrize("selection,cells", [
    ("all", {2: [(0,1),(1,0),(1,1)], 3: [(3,4),(3,5),(4,3),(5,3)]}),
    ("largest", {2: [(0,1),(1,0),(1,1)]}),
    ("smallest", {3: [(3,4),(3,5),(4,3),(5,3)]}),
])
def test_completed_components_determine_rank_and_keep_every_tie(selection, cells):
    source = grid(6, {2: [(0,1),(1,1)], 3: [(3,4),(3,5)]})
    original = json.dumps(source)
    assert load("native_family").solve(source, {"selection": selection}) == grid(6, cells)
    assert json.dumps(source) == original


def test_same_color_disconnected_objects_are_not_aggregated():
    source = grid(7, {2: [(0,1),(1,1)], 3: [(4,5),(4,6)]})
    assert load("native_family").solve(source, {"selection":"largest"}) == grid(
        7, {2: [(0,1),(1,0),(1,1)]})


def test_diagonal_contact_does_not_merge_four_connected_components():
    source = grid(7, {2: [(0,0),(1,1)], 3: [(4,5),(5,5)]})
    assert load("native_family").solve(source, {"selection":"smallest"}) == grid(
        7, {2: [(0,0),(1,1)]})


def test_area_is_cell_count_not_bounding_box():
    source = grid(9, {2: [(0,1),(0,2),(0,3),(0,4)],
                      3: [(6,6),(6,7),(6,8),(7,7),(7,8),(8,8)]})
    assert load("native_family").solve(source, {"selection":"largest"}) == grid(
        9, {3: [(r,c) for r in (6,7,8) for c in (6,7,8)]})


def test_canonical_default_is_exact_catalog_string():
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    programs = {v["program_solution"] for v in Catalog(find_root(__file__)).get("17f92e205b34")["variants"]}
    assert {load("native_family").program({"selection":"all"})} == programs


@pytest.mark.parametrize("settings", [None,{},[],"largest",{"selection":True},
    {"selection":1},{"selection":"unknown"},{"selection":"all","extra":1}])
def test_program_rejects_invalid_settings(settings):
    with pytest.raises((TypeError,ValueError)):
        load("native_family").program(settings)


@pytest.mark.parametrize("bad", [[],[[0]],[[0,0],[0,0]],[[1,0],[0,2]],
    [[0,2],[3,0]],[[0,2],[2,0]],[[0,True],[0,0]],[[0,2.0],[0,0]],
    [[0,-1],[0,0]],[[0,10],[0,0]],[[0,1,0],[0,0,0]],((0,1),(0,0)),
    [[0]*31 for _ in range(31)], [None]])
def test_grid_domain_rejects_invalid_or_completed_inputs(bad):
    with pytest.raises((TypeError,ValueError)):
        load("native_family").validate_grid(bad)


def test_minimum_grid_and_matching_prefilled_partners_are_lawful():
    family=load("native_family")
    assert family.solve([[0,2],[0,0]],{"selection":"all"}) == [[0,2],[2,0]]
    source=grid(3,{2:[(0,1),(1,0)],3:[(1,2)]})
    assert family.solve(source,{"selection":"all"}) == grid(3,{2:[(0,1),(1,0)],3:[(1,2),(2,1)]})


@pytest.mark.parametrize("seed", [True,False,1.0,"1",-1,2**63])
def test_adapter_rejects_noninteger_or_out_of_range_seed(seed):
    with pytest.raises((TypeError,ValueError)):
        load("adapter").generate(seed,{"selection":"all"},3,4)


@pytest.mark.parametrize("demos,queries", [(2,4),(7,4),(3,0),(3,5),(True,4),(3,False),(3.0,4),(3,1.0)])
def test_adapter_count_boundaries(demos,queries):
    with pytest.raises((TypeError,ValueError)):
        load("adapter").generate(0,{"selection":"all"},demos,queries)


@pytest.mark.parametrize("seed", [0,17,2**63-1])
def test_matched_inputs_count_prefixes_and_private_seed_selection(seed):
    adapter=load("adapter")
    episodes=[adapter.generate(seed,{"selection":value},6,4) for value in ("all","largest","smallest")]
    inputs=lambda e:[[p["input"] for p in e[s]] for s in ("train","test")]
    assert inputs(episodes[0])==inputs(episodes[1])==inputs(episodes[2])
    for selection,episode in zip(("all","largest","smallest"),episodes):
        one=adapter.generate(seed,{"selection":selection},3,1)
        assert one["train"]==episode["train"][:3]
        assert one["test"]==episode["test"][:1]
        assert episode["program_solution"]==adapter.program({"selection":selection})
    assert adapter.generate(seed,None,3,4)["program_solution"] == adapter.program(
        {"selection":("all","largest","smallest")[seed%3]})


def test_generation_returns_fresh_data_without_touching_global_rng():
    adapter=load("adapter")
    state=random.getstate()
    first=adapter.generate(17,{"selection":"all"},3,4)
    original=json.dumps(first,sort_keys=True)
    first["train"][0]["input"][0][0]=99
    second=adapter.generate(17,{"selection":"all"},3,4)
    assert json.dumps(second,sort_keys=True)==original
    assert random.getstate()==state

"""Native prototype contract and geometric regressions; no production gate."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace/parametric"
spec = importlib.util.spec_from_file_location("rays_native_test", HOME / "native_family.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def grid(h, w, points, color=1):
    result = [[0] * w for _ in range(h)]
    for r, c in points:
        result[r][c] = color
    return result


def inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_default_program_is_exact_selected_canonical():
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    from puzzle_generators.rule_wrap import wrap_rule
    record = Catalog(find_root(__file__)).get("9ce2dcf587b8")
    expected = {v["program_solution"] for v in record["variants"]}
    assert expected == {native.program({"ray_rule": "both"})}
    for rule in native.RULES:
        assert wrap_rule(native.program({"ray_rule": rule})).startswith("(lambda")
    assert native.program({"ray_rule": "main_only"}) == native._prototype.program_for("main_only")


def test_literal_bounce_consumes_both_boundary_endpoints():
    source = grid(9, 11, [(2, 6), (6, 3)])
    assert set(native.main_endpoints(source)) == {(0, 4), (6, 10), (3, 0), (8, 5)}
    expected = {
        (0,4),(1,5),(2,6),(3,7),(4,8),(5,9),(6,10),
        (3,0),(4,1),(5,2),(6,3),(7,4),(8,5),
        (1,3),(2,2),(3,1),(4,0),(7,9),(8,8),
        (2,1),(1,2),(0,3),(7,6),(6,7),(5,8),(4,9),(3,10),
    }
    assert native.apply_python(source, "one_bounce") == grid(9, 11, expected)
    assert len(expected) == 27
    assert native.apply_python(source, "one_bounce") != native.apply_python(source, "both")
    assert native.apply_python(source, "one_bounce") != native.apply_python(source, "main_only")


def test_corner_endpoint_does_not_start_another_bounce():
    source = grid(7, 7, [(3, 3)], 8)
    assert set(native.main_endpoints(source)) == {(0, 0), (6, 6)}
    assert native.apply_python(source, "one_bounce") == native.apply_python(source, "main_only")
    assert native.apply_python(source, "both") != native.apply_python(source, "one_bounce")


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_request_prefixes_settings_and_determinism(seed):
    full = native.generate(seed, {"ray_rule": "both"}, 6, 4)
    assert full == native.generate(seed, {"ray_rule": "both"}, 6, 4)
    for rule in native.RULES:
        small = native.generate(seed, {"ray_rule": rule}, 2, 1)
        ordinary = native.generate(seed, {"ray_rule": rule})
        expanded = native.generate(seed, {"ray_rule": rule}, 6, 4)
        assert len(ordinary["train"]) == 3 and len(ordinary["test"]) == 4
        assert inputs(small, "train") == inputs(full, "train")[:2]
        assert inputs(small, "test") == inputs(full, "test")[:1]
        assert inputs(expanded, "train") == inputs(full, "train")
        assert inputs(expanded, "test") == inputs(full, "test")
        assert small["train"] == expanded["train"][:2]
        assert small["test"] == expanded["test"][:1]
        all_inputs = inputs(expanded, "train") + inputs(expanded, "test")
        assert len({json.dumps(g) for g in all_inputs}) == 10
        for pair in expanded["train"] + expanded["test"]:
            native.validate_grid(pair["input"])
            assert pair["output"] == native.apply_python(pair["input"], rule)
            assert all(type(v) is int for row in pair["output"] for v in row)


def test_full_bank_has_substantive_large_and_minimum_profiles():
    for rule in native.RULES:
        episode = native.generate(0, {"ray_rule": rule}, 6, 4)
        assert {tuple((len(p["input"]), len(p["input"][0]))) for p in episode["train"] + episode["test"]} >= {(7,7),(30,30)}
        large = [p for p in episode["train"] + episode["test"] if len(p["input"]) == len(p["input"][0]) == 30]
        assert sorted(sum(bool(v) for row in p["input"] for v in row) for p in large) == [8,10]
        for pair in large:
            points = [(r,c) for r,row in enumerate(pair["input"]) for c,v in enumerate(row) if v]
            assert max(r for r,c in points) - min(r for r,c in points) >= 19
            assert max(c for r,c in points) - min(c for r,c in points) >= 19
            changed = [(r,c) for r,row in enumerate(pair["output"]) for c,v in enumerate(row) if v != pair["input"][r][c]]
            assert len(changed) >= 100
            assert {(r >= 15, c >= 15) for r,c in changed} == {(False,False),(False,True),(True,False),(True,True)}


def test_first_two_demos_teach_rule_and_color_count_counterexamples():
    for seed in (0, 1, 17, 2**63-1):
        for rule in native.RULES:
            episode = native.generate(seed, {"ray_rule": rule}, 2, 4)
            for rival in native.RULES:
                if rival != rule:
                    assert any(native.apply_python(p["input"], rival) != p["output"] for p in episode["train"])
            for pair in episode["train"]:
                values = [v for row in pair["input"] for v in row if v]
                assert len(values) > 1 + (values[0]-1) % 3


@pytest.mark.parametrize("rule", native.RULES)
@pytest.mark.parametrize("mode", ["row", "column", "both"])
def test_first_two_refute_collinear_extremes_only(rule, mode):
    def rival(source):
        points = [(r,c) for r,row in enumerate(source) for c,v in enumerate(row) if v]
        kept = []
        for r,c in points:
            row_cols = [cc for rr,cc in points if rr == r]
            col_rows = [rr for rr,cc in points if cc == c]
            row_extreme = c in (min(row_cols),max(row_cols))
            col_extreme = r in (min(col_rows),max(col_rows))
            if (row_extreme if mode == "row" else col_extreme if mode == "column" else row_extreme and col_extreme):
                kept.append((r,c))
        color = source[points[0][0]][points[0][1]]
        result = native.apply_python(grid(len(source),len(source[0]),kept,color),rule)
        for r,c in points:
            result[r][c] = color
        return result
    for seed in (0,17,2**63-1):
        episode = native.generate(seed,{"ray_rule":rule},2,4)
        assert any(rival(p["input"]) != p["output"] for p in episode["train"])


@pytest.mark.parametrize("kwargs", [
    {"seed":True},{"seed":1.0},{"seed":-1},{"seed":2**63},
    {"demos":True},{"demos":1},{"demos":7},{"queries":0},{"queries":5},{"queries":2.0},
    {"settings":{}},{"settings":{"ray_rule":"unknown"}},
    {"settings":{"ray_rule":"both","extra":1}},
])
def test_invalid_request_is_rejected(kwargs):
    request = {"seed":0,"settings":{"ray_rule":"both"},"demos":3,"queries":4}
    request.update(kwargs)
    with pytest.raises((TypeError,ValueError)):
        native.generate(**request)


@pytest.mark.parametrize("source", [
    [[0]*7 for _ in range(7)],
    grid(7,7,[(0,3)]),
    grid(7,7,[(2,2),(4,4)]),
    grid(7,7,[(2,2),(2,3)]),
    grid(6,7,[(2,3)]),
    grid(31,7,[(2,3)]),
    grid(7,7,[(2,3)],True),
])
def test_invalid_grammar_is_rejected(source):
    with pytest.raises((TypeError,ValueError)):
        native.apply_python(source, "one_bounce")


def test_source_and_returned_pairs_do_not_alias():
    source = grid(9,11,[(2,6),(6,3)],2)
    before = deepcopy(source)
    native.apply_python(source,"one_bounce")
    assert source == before
    first = native.generate(17, {"ray_rule":"both"})
    original = deepcopy(first)
    first["train"][0]["input"][0][0] = 9
    assert native.generate(17, {"ray_rule":"both"}) == original

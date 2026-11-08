"""Focused proposed-family checks; canonical production is not changed."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("blocksort_parameters", HOME / "workspace/parametric/prototype.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def test_connectivity_is_topological_not_area():
    diagonal = [[1, 2, 2], [2, 1, 2], [2, 2, 1]]
    assert P.component_count(diagonal) == 3
    assert P.component_count(diagonal, connectivity=8) == 1
    assert P.component_count([[1, 1, 1], [2, 2, 2], [2, 2, 2]]) == 1


@pytest.mark.parametrize("basis", P.SETTINGS)
def test_episode_prefixes_distinct_inputs_and_no_mutation(basis):
    settings = {"rank_basis": basis}
    short = P.generate(17, settings, demos=2, queries=1)
    full = P.generate(17, settings, demos=6, queries=4)
    assert short["train"] == full["train"][:2]
    assert short["test"] == full["test"][:1]
    assert full == P.generate(17, settings, demos=6, queries=4)
    encoded = [str(p["input"]) for p in full["train"] + full["test"]]
    assert len(set(encoded)) == 10
    for pair in full["train"] + full["test"]:
        before = deepcopy(pair["input"])
        assert P.solve(pair["input"], rank_basis=basis) == pair["output"]
        assert pair["input"] == before
        assert sorted(map(str, P.extract_blocks(pair["input"]))) == sorted(map(str, P.extract_blocks(pair["output"])))


def test_shared_demonstrations_change_rule_and_large_stress_is_substantive():
    cells = P.generate(0, {"rank_basis": "cells"})
    components = P.generate(0, {"rank_basis": "components_then_cells"})
    assert [p["input"] for p in cells["train"]] == [p["input"] for p in components["train"]]
    assert all(a["output"] != b["output"] for a, b in zip(cells["train"], components["train"]))
    assert [len(p["input"]) for p in cells["test"]] == [11] * 4
    assert [len(p["input"]) for p in components["test"]] == [14, 20, 26, 30]
    large = components["test"][-1]["input"]
    assert sum(v != 0 for row in large for v in row) == 729
    assert [len(block) for block in P.extract_blocks(large)] == [9] * 9


def test_whole_block_lexicographic_ranking_with_ties():
    ep = P.generate(22, {"rank_basis": "components_then_cells"}, demos=2)
    for pair in ep["train"]:
        blocks = P.extract_blocks(pair["input"])
        keys = [(P.component_count(b), sum(v == 1 for row in b for v in row)) for b in blocks]
        assert len({key[0] for key in keys}) < 9
        expected = sorted(range(9), key=lambda i: keys[i])
        assert P.rank_order(pair["input"], "components_then_cells") == expected
        out = P.extract_blocks(pair["output"])
        assert [out[i] for i in (6, 7, 8, 3, 4, 5, 0, 1, 2)] == [blocks[i] for i in expected]


@pytest.mark.parametrize("settings", [{}, {"rank_basis": "other"}, {"rank_basis": True}, {"rank_basis": "cells", "extra": 1}, None])
def test_invalid_settings_fail(settings):
    with pytest.raises(ValueError):
        P.generate(0, settings)


@pytest.mark.parametrize("seed,demos,queries", [(-1, 3, 4), (True, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, False)])
def test_invalid_counts_and_seeds_fail(seed, demos, queries):
    with pytest.raises(ValueError):
        P.generate(seed, {"rank_basis": "cells"}, demos=demos, queries=queries)


def test_canonical_program_is_exact_catalog_text():
    from arcpuzzles import Catalog
    record = Catalog(str(HOME.parents[1])).get("3108da8bf9e8")
    texts = {v["program_solution"] for v in record["variants"] if isinstance(v.get("program_solution"), str)}
    assert texts == {P.program({"rank_basis": "cells"})}


def test_strict_geometry_and_canonical_boundary():
    ep = P.generate(0, {"rank_basis": "components_then_cells"})
    with pytest.raises(ValueError):
        P.solve(ep["test"][-1]["input"], rank_basis="cells")
    base = deepcopy(ep["train"][0]["input"])
    for r, c, value in [(0, 0, 0), (3, 0, 1), (0, 0, True), (0, 0, 3)]:
        bad = deepcopy(base)
        bad[r][c] = value
        with pytest.raises(ValueError):
            P.validate_grid(bad)


def test_first_two_demos_teach_connectivity_and_tie_break():
    ep = P.generate(8, {"rank_basis": "components_then_cells"}, demos=2)
    maps = []
    for pair in ep["train"]:
        blocks = P.extract_blocks(pair["input"])
        ones = [sum(v == 1 for row in b for v in row) for b in blocks]
        chosen = P.rank_order(pair["input"], "components_then_cells")
        count8 = [P.component_count(b, connectivity=8) for b in blocks]
        count4 = [P.component_count(b) for b in blocks]
        assert chosen != sorted(range(9), key=lambda i: (count8[i], ones[i]))
        assert chosen != sorted(range(9), key=lambda i: count4[i])
        assert chosen != sorted(range(9), key=lambda i: (count4[i], -ones[i]))
        maps.append(chosen)
    assert maps[0] != maps[1]


def test_native_wrapper_and_protected_racket_match_both_settings():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    runtime = HOME.parents[1] / "shared/runtime"
    with _local_imports(runtime, HOME / "workspace/parametric"):
        from puzzle_generators.rule_wrap import wrap_rule
        for basis in P.SETTINGS:
            assert wrap_rule(P.program({"rank_basis": basis}))
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            for basis in P.SETTINGS:
                episode = P.generate(17, {"rank_basis": basis}, demos=2, queries=4)
                for pair in (episode["train"][0], episode["test"][-1]):
                    assert apply(episode["program_solution"], pair["input"]) == pair["output"]
        finally:
            bridge.close()

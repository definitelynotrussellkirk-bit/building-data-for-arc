"""Portable sampler, reconstruction, and teaching-bank behavioral contracts."""

from collections import Counter
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import types

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared/runtime"


@pytest.fixture(autouse=True)
def runtime(monkeypatch):
    monkeypatch.syspath_prepend(str(RUNTIME))


def load(relative, name):
    path = HOME / relative
    assert path.is_file(), f"Required implementation missing: {relative}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules():
    return (load("generator.py", "rooms_sampler_generator_test"),
            load("workspace/parametric/sampler.py", "rooms_sampler_native_test"))


def frozen(grid):
    return tuple(map(tuple, grid))


def wall_points(ob):
    top, left, _, _ = ob["bbox"]
    return {(top + r, left + c) for r, row in enumerate(ob["walls"])
            for c, value in enumerate(row) if value}


def add_frame(grid, color, box, hs=(), vs=()):
    t, l, b, r = box
    for c in range(l, r + 1):
        grid[t][c] = grid[b][c] = color
    for y in range(t, b + 1):
        grid[y][l] = grid[y][r] = color
    for y, a, z in hs:
        for c in range(a, z + 1):
            grid[y][c] = color
    for c, a, z in vs:
        for y in range(a, z + 1):
            grid[y][c] = color


def fixture():
    grid = [[0] * 23 for _ in range(18)]
    add_frame(grid, 1, (2, 1, 10, 9), [(6, 1, 5)], [(5, 2, 10)])
    add_frame(grid, 3, (8, 11, 15, 21), vs=[(16, 8, 15)])
    for r, c in ((0, 0), (17, 22), (4, 18), (12, 3), (4, 5), (2, 4), (8, 15)):
        grid[r][c] = 8
    return grid


def test_parser_recovers_partial_t_fixture_without_mutating_input():
    gen, _ = modules()
    grid = fixture()
    before = [row[:] for row in grid]
    info = gen.analyze(grid)
    assert grid == before and info["noise_color"] == 8
    assert {ob["color"]: ob["rooms"] for ob in info["objects"]} == {1: 3, 3: 2}
    first = next(ob for ob in info["objects"] if ob["color"] == 1)
    assert first["bbox"] == [2, 1, 10, 9]
    assert first["rows"] == [2, 6, 10] and first["cols"] == [1, 5, 9]
    assert sorted(first["room_areas"]) == [9, 9, 21]
    assert all(type(v) is int and v in (0, 1) for row in first["walls"] for v in row)


def test_original_inputs_have_exact_counts_and_self_check_accepts():
    gen, _ = modules()
    parent = json.loads((REPO / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["89565ca0"]
    expected = [(5, {1: 1, 2: 4, 3: 2}), (5, {1: 2, 2: 3, 3: 4, 4: 3, 8: 1}),
                (7, {1: 2, 2: 3, 4: 4, 8: 1}), (9, {1: 1, 2: 3, 3: 6, 4: 5, 8: 2})]
    for pair, (noise, counts) in zip(parent["train"] + parent["test"], expected):
        info = gen.analyze(pair["input"])
        assert info["noise_color"] == noise
        assert {ob["color"]: ob["rooms"] for ob in info["objects"]} == counts
        assert gen.self_check(pair["input"], difficulty=None, meta={}) == []


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
def test_all_banks_are_distinct_lawful_and_have_fixed_cardinality(seed):
    gen, sampler = modules()
    train, query = sampler.sample_banks(seed)
    assert (len(train), len(query)) == (6, 4)
    assert len({frozen(g) for g in train + query}) == 10
    for grid in train + query:
        assert gen.self_check(grid) == []
        info = gen.analyze(grid)
        assert 2 <= len(info["objects"]) <= 8
        assert all(1 <= ob["rooms"] <= 30 for ob in info["objects"])
        assert any(grid[r][c] == info["noise_color"]
                   for ob in info["objects"] for r, c in wall_points(ob))
        assert any(grid[r][c] not in (ob["color"], info["noise_color"])
                   for ob in info["objects"] for r, c in wall_points(ob))


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
def test_first_two_demos_teach_both_spatial_ties_partial_walls_and_noise_role(seed):
    gen, sampler = modules()
    train, _ = sampler.sample_banks(seed)
    first, second = [gen.analyze(grid) for grid in train[:2]]
    assert sorted(ob["rooms"] for ob in first["objects"]) == [1, 3, 3]
    tied = sorted((ob for ob in first["objects"] if ob["rooms"] == 3), key=lambda ob: ob["bbox"][1])
    assert tied[0]["bbox"][1] < tied[1]["bbox"][1]
    assert tied[0]["bbox"][0] > tied[1]["bbox"][0]
    assert tied[0]["color"] > tied[1]["color"]
    assert any(ob["rooms"] < (len(ob["rows"]) - 1) * (len(ob["cols"]) - 1)
               for ob in first["objects"])
    mass = Counter(v for row in train[0] for v in row)
    assert mass[first["noise_color"]] > min(mass[ob["color"]] for ob in first["objects"])
    assert mass[first["noise_color"]] < max(mass[ob["color"]] for ob in first["objects"])
    assert sorted(ob["rooms"] for ob in second["objects"]) == [2, 4, 4]
    tied = sorted((ob for ob in second["objects"] if ob["rooms"] == 4), key=lambda ob: ob["bbox"][0])
    assert tied[0]["bbox"][1] == tied[1]["bbox"][1]
    assert tied[0]["bbox"][0] < tied[1]["bbox"][0]
    assert tied[0]["color"] > tied[1]["color"]


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_second_demo_contains_a_foreign_nonzero_bridge_across_an_absent_wall(seed):
    gen, sampler = modules()
    grid = sampler.sample_banks(seed)[0][1]
    info = gen.analyze(grid)
    found = False
    for ob in info["objects"]:
        t, l, b, r = ob["bbox"]
        walls = wall_points(ob)
        for y in ob["rows"][1:-1]:
            for a, z in zip(ob["cols"], ob["cols"][1:]):
                if ((y, a) in walls and (y, z) in walls
                        and any((y, c) not in walls for c in range(a + 1, z))
                        and all(grid[y][c] != 0 for c in range(a, z + 1))):
                    found = True
    assert found, "The teaching prefix must refute borrowing continuous foreign walls"


def test_queries_cover_novel_sizes_and_a_substantive_30_room_profile():
    gen, sampler = modules()
    train, query = sampler.sample_banks(17)
    sizes = {(len(grid), len(grid[0])) for grid in query}
    assert sizes == {(12, 15), (19, 23), (26, 29), (30, 30)}
    assert sizes.isdisjoint({(len(grid), len(grid[0])) for grid in train})
    largest = next(grid for grid in query if len(grid) == len(grid[0]) == 30)
    info = gen.analyze(largest)
    big = max(info["objects"], key=lambda ob: ob["rooms"])
    assert big["rooms"] == 30
    assert (len(big["rows"]), len(big["cols"])) == (6, 7)
    assert sum(map(sum, big["walls"])) >= 250
    assert any(largest[r][c] not in (big["color"], info["noise_color"]) for r, c in wall_points(big))


def test_query_order_is_independently_shuffled_after_completing_bank():
    _, sampler = modules()
    orders = {tuple((len(g), len(g[0])) for g in sampler.sample_banks(seed)[1]) for seed in range(12)}
    assert len(orders) >= 4 and len({order[0] for order in orders}) >= 3


def test_repeatability_stream_isolation_and_mutable_return_independence():
    gen, sampler = modules()
    state = random.getstate()
    first = sampler.sample_banks(17)
    gen.generate(2**63 - 1, 2**71 + 3)
    assert sampler.sample_banks(17) == first
    assert random.getstate() == state
    assert sampler.sample_banks(18) != first
    rows = [row for bank in first for grid in bank for row in grid]
    assert len({id(row) for row in rows}) == len(rows)
    first[0][0][0][0] = (first[0][0][0][0] + 1) % 10
    assert sampler.sample_banks(17) != first


@pytest.mark.parametrize("bad", [-1, 2**63, True, False, 1.0, "1", None])
def test_invalid_seeds_rejected_by_both_entry_points(bad):
    gen, sampler = modules()
    for function in (lambda: gen.generate(bad, 0), lambda: sampler.sample_banks(bad)):
        with pytest.raises((TypeError, ValueError)):
            function()


@pytest.mark.parametrize("bad", [-1, True, 1.0, "0", None])
def test_invalid_sample_indices_rejected(bad):
    gen, _ = modules()
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, bad)


@pytest.mark.parametrize("index", [6, 37, 99, 104, 2**71 + 3])
def test_arbitrary_nonnegative_sample_index_is_stable_and_lawful(index):
    gen, _ = modules()
    grid = gen.generate(17, index)
    assert gen.self_check(grid) == [] and grid == gen.generate(17, index)


@pytest.mark.parametrize("bad", [7, 33, True, False, 8.0, "8", None])
def test_noise_axis_rejects_invalid_values_without_coercion(bad):
    gen, _ = modules()
    with pytest.raises((TypeError, ValueError)):
        gen.generate(17, 0, noise_budget=bad)


def test_noise_axis_is_real_and_records_shared_context_provenance():
    from puzzle_generators.base import set_ctx_observer

    gen, _ = modules()
    captures = []
    set_ctx_observer(captures.append)
    try:
        low = gen.generate(17, 103, noise_budget=8)
        high = gen.generate(17, 103, noise_budget=32)
    finally:
        set_ctx_observer(None)
    assert captures[-1].overrides_used()["noise_budget"] == 32
    assert captures[-1].draw_bounds("noise_budget") == (8, 32)
    infos = [gen.analyze(g) for g in (low, high)]
    assert [{ob["color"]: (ob["bbox"], ob["rooms"]) for ob in x["objects"]} for x in infos][0] == {
        ob["color"]: (ob["bbox"], ob["rooms"]) for ob in infos[1]["objects"]}
    for grid, info, budget in zip((low, high), infos, (8, 32)):
        assert sum(v == info["noise_color"] for row in grid for v in row) == budget
    assert low != high


def test_actual_static_linter_and_axis_domain_parser(monkeypatch):
    gen, _ = modules()
    package = types.ModuleType("scripts")
    package.__path__ = [str(REPO / "shared/tools")]
    monkeypatch.setitem(sys.modules, "scripts", package)
    from scripts.lint_generator import lint_generator
    from scripts.check_generator_override_contract import axis_domain_report

    report = lint_generator(HOME / "generator.py")
    assert report.errors == [] and report.warnings == [], (report.errors, report.warnings)
    domains = axis_domain_report(gen.AXES)
    assert len(domains) == 1 and domains[0].name == "noise_budget" and domains[0].probed
    assert min(domains[0].values) == 8 and max(domains[0].values) == 32


def test_real_exact_axis_contract_requires_and_verifies_noise_observer(monkeypatch):
    gen, _ = modules()
    package = types.ModuleType("scripts")
    package.__path__ = [str(REPO / "shared/tools")]
    monkeypatch.setitem(sys.modules, "scripts", package)
    from scripts.check_generator_override_contract import _required_observer_axes, _observed_override_errors

    required = _required_observer_axes(gen.AXES)
    assert required == {"noise_budget"}
    assert callable(getattr(gen, "observe_overrides", None)), "An exact noise axis needs a realized-value observer"
    for budget in (8, 32):
        for index in (0, 100, 103):
            grid = gen.generate(17, index, noise_budget=budget)
            assert gen.observe_overrides(grid) == {"noise_budget": budget}
            assert _observed_override_errors(gen, grid, {"noise_budget": budget}, "noise-boundary", required) == []


def test_generator_relocates_without_any_task_workspace(tmp_path):
    gen, _ = modules()
    destination = tmp_path / "isolated_generator.py"
    destination.write_bytes((HOME / "generator.py").read_bytes())
    program = """
import importlib.util, json, sys
sys.path.insert(0, sys.argv[1])
s=importlib.util.spec_from_file_location('isolated_rooms', sys.argv[2])
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
print(json.dumps(m.generate(17, 103)))
"""
    process = subprocess.run([sys.executable, "-I", "-c", program, str(RUNTIME), str(destination)],
                             cwd=tmp_path, check=True, capture_output=True, text=True)
    assert json.loads(process.stdout) == gen.generate(17, 103)


@pytest.mark.parametrize("bad", [[], [[]], [[True]], [[1.0]], [[10]], [[1], [1, 2]],
                                     ((1, 2), (3, 4)), [[0] * 31] * 2])
def test_parser_strict_grid_types_and_bounds(bad):
    gen, _ = modules()
    with pytest.raises((TypeError, ValueError)):
        gen.analyze(bad)
    assert gen.self_check(bad)


def test_parser_rejects_erased_walls_missing_noise_and_single_structure():
    gen, _ = modules()
    grid = fixture()
    grid[2][6] = 0
    assert gen.self_check(grid)
    grid = fixture()
    grid = [[0 if value == 8 else value for value in row] for row in grid]
    assert gen.self_check(grid)
    grid = [[0] * 12 for _ in range(12)]
    add_frame(grid, 1, (2, 2, 9, 9))
    for r, c in ((0, 0), (11, 11), (1, 8)):
        grid[r][c] = 8
    assert gen.self_check(grid)


def test_parser_rejects_more_than_30_rooms_and_nonrectangular_regions():
    gen, _ = modules()
    grid = [[0] * 30 for _ in range(30)]
    add_frame(grid, 1, (1, 1, 25, 25),
              [(r, 1, 25) for r in (5, 9, 13, 17, 21)],
              [(c, 1, 25) for c in (5, 9, 13, 17, 21)])
    add_frame(grid, 2, (26, 26, 28, 28))
    for r, c in ((0, 0), (29, 29), (27, 2)):
        grid[r][c] = 8
    assert gen.self_check(grid)
    grid = [[0] * 20 for _ in range(17)]
    add_frame(grid, 1, (1, 1, 12, 12), [(6, 6, 12)], [(6, 1, 6)])
    add_frame(grid, 2, (13, 14, 15, 18))
    for r, c in ((0, 0), (16, 19), (14, 2)):
        grid[r][c] = 8
    assert gen.self_check(grid)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_difficulty_size_bands_remain_lawful(difficulty):
    gen, _ = modules()
    grid = gen.generate(17, 6, difficulty=difficulty)
    assert gen.self_check(grid) == []
    if difficulty == "easy":
        assert (len(grid), len(grid[0])) == (12, 15)
    if difficulty == "hard":
        assert (len(grid), len(grid[0])) == (30, 30)


def test_unknown_overrides_and_bad_difficulties_are_rejected():
    gen, _ = modules()
    with pytest.raises(TypeError):
        gen.generate(17, 0, unsupported=1)
    for bad in (True, 1, "HARD", [], {}):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(17, 0, difficulty=bad)

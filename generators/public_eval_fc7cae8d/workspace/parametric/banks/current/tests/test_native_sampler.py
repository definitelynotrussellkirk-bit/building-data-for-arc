"""Behavioral sampler checks independent of its scene-building helpers.

These tests catch missing role coverage, ambiguous side labels, damaged crop
geometry, leaked RNG state, and returns that share mutable grid storage.
Reference-label execution is covered separately by the task's Racket checks.
"""

from collections import Counter
import importlib.util
import json
import random
from pathlib import Path
import subprocess
import sys
import types

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared/runtime"


@pytest.fixture(autouse=True)
def _same_checkout_runtime(monkeypatch):
    monkeypatch.syspath_prepend(str(RUNTIME))


def _load(relative, name):
    path = HOME / relative
    assert path.is_file(), f"The required implementation is missing: {relative}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _modules():
    return (
        _load("generator.py", "fc7cae8d_sampler_test_generator"),
        _load("workspace/parametric/sampler.py", "fc7cae8d_sampler_test_native"),
    )


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _transforms(grid):
    for reflected in (False, True):
        value = [row[::-1] for row in grid] if reflected else [row[:] for row in grid]
        for turns in range(4):
            yield reflected, turns, _frozen(value)
            value = [list(row) for row in zip(*value[::-1])]


def _describe(grid):
    """Recover structural facts from values, without generator metadata."""
    assert type(grid) is list and 1 <= len(grid) <= 30
    height, width = len(grid), len(grid[0])
    assert 1 <= width <= 30
    assert all(type(row) is list and len(row) == width for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)

    seen, interior = set(), []
    for row in range(height):
        for col in range(width):
            if not grid[row][col] or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            for r, c in todo:
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= rr < height and 0 <= cc < width
                        and grid[rr][cc] and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        todo.append((rr, cc))
            if all(0 < r < height - 1 and 0 < c < width - 1 for r, c in todo):
                interior.append(todo)
    assert len(interior) == 1, "Exactly one nonzero component must be separated from the frame"
    component = interior[0]
    r0, r1 = min(r for r, _ in component), max(r for r, _ in component)
    c0, c1 = min(c for _, c in component), max(c for _, c in component)
    edges = (
        grid[0][1:-1], [row[-1] for row in grid[1:-1]],
        grid[-1][1:-1], [row[0] for row in grid[1:-1]],
    )
    boundary_colors = {v for edge in edges for v in edge if v}
    assert len(boundary_colors) == 3
    component_colors = {grid[r][c] for r, c in component}
    markers = component_colors & boundary_colors
    assert len(markers) == 2

    inner, outer = {}, {}
    for color in markers:
        points = {(r, c) for r, c in component if grid[r][c] == color}
        rows, cols = {r for r, _ in points}, {c for _, c in points}
        candidates = []
        if rows == {r0}:
            candidates.append(0)
        if cols == {c1}:
            candidates.append(1)
        if rows == {r1}:
            candidates.append(2)
        if cols == {c0}:
            candidates.append(3)
        assert len(candidates) == 1
        inner[color] = candidates[0]
        counts = [edge.count(color) for edge in edges]
        assert counts.count(max(counts)) == 1
        outer[color] = counts.index(max(counts))
        assert max(counts) > len(edges[outer[color]]) // 2

    assert (max(inner.values()) - min(inner.values())) % 2 == 1
    assert (max(outer.values()) - min(outer.values())) % 2 == 1
    crop_r0 = r0 + (0 in inner.values())
    crop_r1 = r1 - (2 in inner.values())
    crop_c0 = c0 + (3 in inner.values())
    crop_c1 = c1 - (1 in inner.values())
    picture = [row[crop_c0:crop_c1 + 1] for row in grid[crop_r0:crop_r1 + 1]]
    ph, pw = len(picture), len(picture[0])
    assert ph >= 3 and pw >= 3
    assert not ({cell for row in picture for cell in row} & boundary_colors)
    for color, side in inner.items():
        if side in (0, 2):
            expected = {(r0 if side == 0 else r1, c) for c in range(crop_c0, crop_c1 + 1)}
        else:
            expected = {(r, c1 if side == 1 else c0) for r in range(crop_r0, crop_r1 + 1)}
        assert {(r, c) for r, c in component if grid[r][c] == color} == expected
    shared_corner = (
        r0 if 0 in inner.values() else r1,
        c0 if 3 in inner.values() else c1,
    )
    assert grid[shared_corner[0]][shared_corner[1]] == 0
    assert any(cell == 0 for row in picture for cell in row)
    assert len({value for _, _, value in _transforms(picture)}) == 8

    valid = [
        (reflected, turns)
        for reflected in (False, True) for turns in range(4)
        if all(((-side if reflected else side) + turns) % 4 == outer[color]
               for color, side in inner.items())
    ]
    assert len(valid) == 1
    distractor = (boundary_colors - markers).pop()
    assert all(any(edge) for edge in edges)
    assert all(distractor in edges[side] for side in range(4) if side not in outer.values())
    assert any(0 in edges[side] for side in range(4) if side not in outer.values())
    counts = Counter(cell for row in picture for cell in row)
    return {
        "canvas": (height, width), "picture_size": (ph, pw),
        "inner": frozenset(inner.values()), "outer": frozenset(outer.values()),
        "transform": valid[0], "picture_counts": counts,
        "marker_sides": {color: (inner[color], outer[color]) for color in markers},
        "edges": edges, "picture": picture,
        "picture_bbox": (crop_r0, crop_r1, crop_c0, crop_c1),
        "component_bbox": (r0, r1, c0, c1), "shared_corner": shared_corner,
    }


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
def test_all_bank_members_obey_unambiguous_parent_geometry(seed):
    _, sampler = _modules()
    train, query = sampler.sample_banks(seed)
    assert (len(train), len(query)) == (6, 4)
    assert len({_frozen(grid) for grid in train + query}) == 10
    for grid in train + query:
        _describe(grid)


@pytest.mark.parametrize("seed", [0, 1, 17, 2**63 - 1])
def test_first_two_demos_teach_both_chiralities_and_distinct_placements(seed):
    _, sampler = _modules()
    train, _ = sampler.sample_banks(seed)
    first, second = map(_describe, train[:2])
    assert first["transform"][0] is True
    assert first["transform"][1] in (0, 2)
    assert second["transform"][0] is False and second["transform"][1] in (1, 3)
    assert first["canvas"] == second["canvas"] == (16, 19)
    assert first["picture_size"] == second["picture_size"] == (7, 10)
    assert first["inner"] != second["inner"]
    assert first["outer"] != second["outer"]
    assert all(info["picture_size"][0] != info["picture_size"][1] for info in (first, second))


def test_query_bank_has_small_intermediate_large_and_substantive_30_by_30_roles():
    _, sampler = _modules()
    _, query = sampler.sample_banks(17)
    descriptions = {_describe(grid)["canvas"]: _describe(grid) for grid in query}
    assert set(descriptions) == {(9, 10), (17, 22), (24, 29), (30, 30)}
    stress = descriptions[(30, 30)]
    assert stress["picture_size"] == (23, 23)
    assert len(stress["picture_counts"]) >= 6
    assert sum(stress["picture_counts"].values()) - max(stress["picture_counts"].values()) >= 70


def test_completed_query_bank_is_shuffled_before_prefix_selection():
    _, sampler = _modules()
    orders = {
        tuple((len(grid), len(grid[0])) for grid in sampler.sample_banks(seed)[1])
        for seed in range(12)
    }
    assert len(orders) >= 4
    assert len({order[0] for order in orders}) >= 3


def test_seeded_banks_are_repeatable_without_global_random_mutation():
    generator, sampler = _modules()
    state = random.getstate()
    first = sampler.sample_banks(17)
    generator.generate(2**63 - 1, 2**71 + 3)
    second = sampler.sample_banks(17)
    assert random.getstate() == state
    assert first == second
    assert first != sampler.sample_banks(18)


def test_no_grids_or_rows_are_aliased_between_returns():
    _, sampler = _modules()
    train, query = sampler.sample_banks(17)
    expected = sampler.sample_banks(17)
    rows = [row for grid in train + query for row in grid]
    assert len({id(row) for row in rows}) == len(rows)
    train[0][0][0] = (train[0][0][0] + 1) % 10
    query[0][0][0] = (query[0][0][0] + 1) % 10
    assert sampler.sample_banks(17) == expected


@pytest.mark.parametrize("bad", [-1, 2**63, True, False, 1.0, "1", None])
def test_seed_rejection_is_strict_and_shared_by_both_entry_points(bad):
    generator, sampler = _modules()
    with pytest.raises((TypeError, ValueError)):
        generator.generate(bad, 0)
    with pytest.raises((TypeError, ValueError)):
        sampler.sample_banks(bad)


@pytest.mark.parametrize("bad", [-1, True, 1.0, "0"])
def test_sample_index_rejects_nonintegers_and_negative_values(bad):
    generator, _ = _modules()
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, bad)


@pytest.mark.parametrize("sample_index", [6, 37, 99, 104, 2**71 + 3])
def test_unbounded_nonnegative_sample_indices_remain_lawful(sample_index):
    generator, _ = _modules()
    value = generator.generate(17, sample_index)
    _describe(value)
    assert value == generator.generate(17, sample_index)


def test_generator_file_runs_without_its_task_workspace(tmp_path):
    generator, _ = _modules()
    path = tmp_path / "isolated_generator.py"
    path.write_bytes((HOME / "generator.py").read_bytes())
    code = """
import importlib.util, json, sys
sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location('relocated_generator', sys.argv[2])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(json.dumps(module.generate(17, 103)))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(RUNTIME), str(path)],
        cwd=tmp_path, check=True, text=True, capture_output=True,
    )
    assert json.loads(result.stdout) == generator.generate(17, 103)


def test_small_scenes_do_not_isolate_corner_pixels_or_erase_distractor_gaps():
    generator, _ = _modules()
    for seed in range(128):
        _describe(generator.generate(seed, 100))
        _describe(generator.generate(seed, 6))


@pytest.mark.parametrize("seed", [0, 9, 17, 43, 2**63 - 1])
def test_first_two_demos_refute_total_first_last_and_middle_edge_selectors(seed):
    """An adjacent wrong sampled pair must disagree, not trigger fallback."""
    _, sampler = _modules()
    train, _ = sampler.sample_banks(seed)
    for sample in ("first", "last", "middle"):
        refuted = False
        for grid in train[:2]:
            info = _describe(grid)
            colors = sorted(info["marker_sides"])
            true_sides = tuple(info["marker_sides"][color][1] for color in colors)
            def sample_at(side):
                edge = info["edges"][side]
                index = 0 if sample == "first" else -1 if sample == "last" else len(edge) // 2
                return edge[index]

            sampled = tuple(max(range(4), key=lambda side: int(sample_at(side) == color)) for color in colors)
            if (sampled[0] - sampled[1]) % 2 == 1 and sampled != true_sides:
                # _describe already proves every D4 image differs.  An adjacent
                # changed pair changes the output under either color pairing.
                refuted = True
        assert refuted, f"{sample} sample remains consistent with both demonstrations"


def test_base_generator_passes_the_actual_static_contract(monkeypatch):
    package = types.ModuleType("scripts")
    package.__path__ = [str(REPO / "shared/tools")]
    monkeypatch.setitem(sys.modules, "scripts", package)
    from scripts.lint_generator import lint_generator

    report = lint_generator(HOME / "generator.py")
    assert report.errors == [], report.errors
    assert report.warnings == [], report.warnings


def test_depth_axis_is_probeable_through_the_real_override_domain_parser(monkeypatch):
    generator, _ = _modules()
    package = types.ModuleType("scripts")
    package.__path__ = [str(REPO / "shared/tools")]
    monkeypatch.setitem(sys.modules, "scripts", package)
    from scripts.check_generator_override_contract import axis_domain_report

    domains = axis_domain_report(generator.AXES)
    assert len(domains) == 1 and domains[0].name == "max_frame_depth"
    assert domains[0].probed and domains[0].values == [1, 2, 3]


def test_depth_override_changes_only_frame_extent_and_records_shared_context_provenance():
    from puzzle_generators.base import set_ctx_observer

    generator, _ = _modules()
    captures = []
    set_ctx_observer(captures.append)
    try:
        shallow = generator.generate(17, 103, max_frame_depth=1)
        deep = generator.generate(17, 103, max_frame_depth=3)
    finally:
        set_ctx_observer(None)
    assert captures, "Generation must use the shared keyed context"
    assert captures[-1].overrides_used()["max_frame_depth"] == 3
    assert captures[-1].draw_bounds("max_frame_depth") == (1, 3)
    info = _describe(shallow)
    deeper = _describe(deep)
    assert info["picture"] == deeper["picture"]
    assert info["picture_bbox"] == deeper["picture_bbox"]

    def outside_depths(grid, description):
        r0, r1, c0, c1 = description["component_bbox"]
        height, width = len(grid), len(grid[0])
        return [
            min(r, c, height - 1 - r, width - 1 - c) + 1
            for r, row in enumerate(grid) for c, color in enumerate(row)
            if color and not (r0 <= r <= r1 and c0 <= c <= c1)
        ]

    assert max(outside_depths(shallow, info)) == 1
    assert 1 < max(outside_depths(deep, deeper)) <= 3
    assert len(outside_depths(deep, deeper)) > len(outside_depths(shallow, info))


@pytest.mark.parametrize("bad", [0, 4, True, False, 1.0, "2", None])
def test_depth_override_rejects_invalid_values_without_coercion(bad):
    generator, _ = _modules()
    with pytest.raises((TypeError, ValueError)):
        generator.generate(17, 0, max_frame_depth=bad)


def test_self_check_accepts_all_original_inputs_and_generated_depth_endpoints():
    generator, _ = _modules()
    assert callable(getattr(generator, "self_check", None)), "self_check is required"
    parent = json.loads((REPO / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["fc7cae8d"]
    for pair in parent["train"] + parent["test"]:
        assert generator.self_check(pair["input"]) == []
    for depth in (1, 2, 3):
        for index in (0, 1, 100, 103):
            grid = generator.generate(17, index, max_frame_depth=depth)
            assert generator.self_check(grid, difficulty=None, meta={"sample": index}) == []


def test_self_check_rejects_malformed_shapes_partial_bars_islands_and_reserved_colors():
    generator, _ = _modules()
    assert callable(getattr(generator, "self_check", None)), "self_check is required"
    grid = generator.generate(17, 0)
    info = _describe(grid)
    color = sorted(info["marker_sides"])[0]
    r0, r1, c0, c1 = info["component_bbox"]
    marker_cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if grid[r][c] == color]
    malformed = [[], [[0], [0, 1]], [[True]], [[10]], [[0] * 31]]

    def changed(row, col, value):
        result = [cells[:] for cells in grid]
        result[row][col] = value
        return result

    malformed.append(changed(*marker_cells[len(marker_cells) // 2], 0))
    malformed.append(changed(*info["shared_corner"], color))
    pr0, pr1, pc0, pc1 = info["picture_bbox"]
    malformed.append(changed(pr0 + 1, pc0 + 1, color))
    island = next(
        (r, c) for r in range(1, len(grid) - 1) for c in range(1, len(grid[0]) - 1)
        if not (r0 <= r <= r1 and c0 <= c <= c1)
        and all(grid[rr][cc] == 0 for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
    )
    malformed.append(changed(*island, info["picture"][1][1]))
    symmetric = [row[:] for row in grid]
    for r in range(pr0, pr1 + 1):
        for c in range(pc0, pc1 + 1):
            symmetric[r][c] = info["picture"][1][1]
    malformed.append(symmetric)
    for broken in malformed:
        violations = generator.self_check(broken)
        assert type(violations) is list and violations
        assert all(type(message) is str and message for message in violations)

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO / "generators" / "9c75b1456763" / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_9c75b1456763_under_test", GENERATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_inputs():
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "9c75b1456763":
                return [pair["input"] for pair in row["train"] + row["test"]]
    raise AssertionError("canonical task missing")


def components4(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r0, c0 = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (r0 + dr, c0 + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] != 0
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(cells)
    return components


def fillable_cells(grid, component):
    height, width = len(grid), len(grid[0])
    return {
        (row, col)
        for row, col in component
        if 0 < row < height - 1
        and 0 < col < width - 1
        and all(
            grid[row + dr][col + dc] != 0
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if dr or dc
        )
    }


def component_count(cells):
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
    return count


def test_rule_hash_and_unknown_override_contract():
    generator = load_generator()
    assert generator.RULE_HASH == "58004efe7e78"
    with pytest.raises((TypeError, ValueError, KeyError)):
        generator.generate(1, 2, __unknown_axis__=7)


@pytest.mark.parametrize(
    ("profile", "expected"),
    [
        ("p18_5", (18, 18, 5)),
        ("p20_5", (20, 20, 5)),
        ("p30_4", (30, 30, 4)),
        ("p30_5", (30, 30, 5)),
    ],
)
def test_exact_profile_and_semantic_axes_round_trip(profile, expected):
    generator = load_generator()
    for nodes in (2, 3, 4):
        for layout in ("straight", "bent"):
            grid = generator.generate(
                1200 + nodes,
                nodes,
                difficulty="medium",
                profile=profile,
                nodes_per_network=nodes,
                layout=layout,
            )
            palette = len({value for row in grid for value in row})
            assert (len(grid), len(grid[0]), palette) == expected
            assert generator.self_check(grid) == []
            assert generator.observe_overrides(grid) == {
                "profile": profile,
                "nodes_per_network": nodes,
                "layout": layout,
            }


def test_generated_components_require_marker_propagation_between_nodes():
    generator = load_generator()
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            grid = generator.generate(5000 + index, index, difficulty=band)
            components = components4(grid)
            assert len(components) in (2, 3)
            for component in components:
                markers = [
                    (row, col)
                    for row, col in component
                    if grid[row][col] not in (0, 1)
                ]
                assert len(markers) == 1
                interiors = fillable_cells(grid, component)
                assert len(interiors) >= 2
                assert component_count(interiors) >= 2
                marker = markers[0]
                assert any(
                    max(abs(row - marker[0]), abs(col - marker[1])) >= 4
                    for row, col in interiors
                )


def test_self_check_rejects_sealed_hole_and_markerless_component():
    generator = load_generator()
    hole = [[0] * 10 for _ in range(10)]
    for row in range(2, 8):
        for col in range(2, 8):
            hole[row][col] = 1
    hole[6][6] = 5
    hole[3][3] = 0
    assert any("hole" in finding for finding in generator.self_check(hole))

    markerless = copy.deepcopy(hole)
    markerless[3][3] = 1
    markerless[6][6] = 1
    markerless[0][0] = 1
    assert any("marker" in finding for finding in generator.self_check(markerless))


def test_canonical_inputs_remain_in_domain():
    generator = load_generator()
    for grid in canonical_inputs():
        assert generator.self_check(grid) == []
        assert generator.strict_canonical_like(grid) == []


def test_declared_witnesses_have_verified_rival_disagreements():
    generator = load_generator()
    assert generator.SEMANTIC_WITNESSES
    assert generator.SEMANTIC_RIVALS
    assert generator.WITNESS_RIVALS
    fired = {name: 0 for name in generator.SEMANTIC_WITNESSES}
    for index in range(18):
        grid = generator.generate(8000 + index, index, difficulty="medium")
        authoritative = generator.rule_mirror(grid)
        for name, witness in generator.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            fired[name] += 1
            rivals = generator.WITNESS_RIVALS[name]
            if isinstance(rivals, str):
                rivals = [rivals]
            assert any(
                generator.SEMANTIC_RIVALS[rival](grid) != authoritative
                for rival in rivals
            )
    assert all(count > 0 for count in fired.values())


def test_default_census_demonstrates_nontrivial_transformation_density():
    generator = load_generator()
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            grid = generator.generate(9100 + index, index, difficulty=band)
            output = generator.rule_mirror(grid)
            changed = sum(
                before != after
                for before_row, after_row in zip(grid, output)
                for before, after in zip(before_row, after_row)
            )
            assert changed * 100 >= len(grid) * len(grid[0])


def test_default_census_spans_canonical_component_scale():
    generator = load_generator()
    max_component_sizes = []
    for index in range(24):
        grid = generator.generate(9300 + index, index, difficulty="medium")
        max_component_sizes.append(max(map(len, components4(grid))))
    assert min(max_component_sizes) <= 61 <= max(max_component_sizes)

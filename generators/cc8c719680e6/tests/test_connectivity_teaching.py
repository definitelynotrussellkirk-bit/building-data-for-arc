"""A lesson must teach color-aware four-connectivity, not merely framing."""
from __future__ import annotations

import pytest

from puzzle_generators.per_puzzle.cc8c719680e6 import generator as gen


def _rival_outline(grid, *, diagonal=False, ignore_color=False):
    """Independent rival implementation; row-major source color breaks ties."""
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    remaining = {
        (r, c) for r in range(height) for c in range(width) if grid[r][c]
    }
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    while remaining:
        first = min(remaining)
        color = grid[first[0]][first[1]]
        remaining.remove(first)
        component, pending = {first}, [first]
        while pending:
            r, c = pending.pop()
            for dr, dc in steps:
                neighbor = r + dr, c + dc
                if neighbor in remaining and (
                    ignore_color or grid[neighbor[0]][neighbor[1]] == color
                ):
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        top = min(r for r, _ in component)
        bottom = max(r for r, _ in component)
        left = min(c for _, c in component)
        right = max(c for _, c in component)
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if r in (top, bottom) or c in (left, right):
                    output[r][c] = color
    return output


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize("rival", ("same_color_8_connected", "color_blind_4_connected"))
def test_every_four_demo_window_teaches_connectivity(difficulty, rival):
    # Regresses rare-contact sampling: aggregate witness existence is insufficient.
    for seed in range(16):
        grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(7)]
        for start in range(4):
            assert any(
                _rival_outline(
                    grid,
                    diagonal=rival == "same_color_8_connected",
                    ignore_color=rival == "color_blind_4_connected",
                ) != gen.rule_mirror(grid)
                for grid in grids[start:start + 4]
            ), (rival, difficulty, seed, start)


def test_generated_connectivity_rivals_are_declared_for_production_census():
    # Without these bindings the shared semantic gate can miss the regression.
    for name, kwargs in (
        ("same_color_8_connected", {"diagonal": True}),
        ("color_blind_4_connected", {"ignore_color": True}),
    ):
        rival = gen.LESSON_COMPETITORS.get(name)
        assert callable(rival), name
        for index in range(4):
            grid = gen.generate(29, index, difficulty="medium")
            assert rival(grid) == _rival_outline(grid, **kwargs)

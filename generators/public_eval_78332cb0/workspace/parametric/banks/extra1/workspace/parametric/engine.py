"""Separator-bounded path panels reordered into one contact-matched chain."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import random
from typing import NamedTuple

TASK_ID = "public_eval_78332cb0"
PARAMETERS = {"finish": ["chain_only", "highlight_chain_center"]}
DEFAULT = {"finish": "chain_only"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}


class Panel(NamedTuple):
    source_index: int
    grid: list[list[int]]
    color: int
    north: int | None
    south: int | None
    west: int | None
    east: int | None


def _integer(value: object, lo: int, hi: int, label: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{label} must be an exact integer in {lo}..{hi}")
    return value


def _grid(value: object) -> list[list[int]]:
    if (type(value) is not list or not 5 <= len(value) <= 30 or type(value[0]) is not list
            or not 5 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0]) for row in value)
            or any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row)):
        raise ValueError("need a rectangular exact-integer ARC grid, dimensions 5..30")
    return [row[:] for row in value]


def _bands(length: int, separators: list[int]) -> list[tuple[int, int]]:
    bands: list[tuple[int, int]] = []
    cursor = 0
    for separator in separators:
        if cursor < separator:
            bands.append((cursor, separator))
        cursor = separator + 1
    if cursor < length:
        bands.append((cursor, length))
    return bands


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        r, c = todo.pop()
        for dr, dc in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            q = (r + dr, c + dc)
            if q in cells and q not in seen:
                seen.add(q)
                todo.append(q)
    return seen == cells


def _one(values: list[int], label: str) -> int | None:
    if not values:
        return None
    if len(values) != 1:
        raise ValueError(f"panel must have at most one {label} edge contact")
    return values[0]


def _panel(source_index: int, panel: list[list[int]]) -> Panel | None:
    if len(panel) != 5 or any(len(row) != 5 for row in panel):
        raise ValueError("every nonseparator band must be exactly 5x5")
    cells = {(r, c) for r in range(5) for c in range(5) if panel[r][c] != 7}
    if not cells:
        return None
    colors = {panel[r][c] for r, c in cells}
    if len(colors) != 1 or colors & {6, 7}:
        raise ValueError("each occupied panel needs one monochrome path distinct from 6 and 7")
    if not _connected(cells):
        raise ValueError("panel foreground must be one 4-connected path")
    return Panel(
        source_index,
        [row[:] for row in panel],
        next(iter(colors)),
        _one([c for r, c in cells if r == 0], "north"),
        _one([c for r, c in cells if r == 4], "south"),
        _one([r for r, c in cells if c == 0], "west"),
        _one([r for r, c in cells if c == 4], "east"),
    )


def _orders(panels: list[Panel], orientation: str) -> list[list[Panel]]:
    entry = (lambda p: p.north) if orientation == "vertical" else (lambda p: p.west)
    exit_ = (lambda p: p.south) if orientation == "vertical" else (lambda p: p.east)
    starts = [p for p in panels if entry(p) is None and exit_(p) is not None]
    solutions: list[list[Panel]] = []

    def extend(order: list[Panel], remaining: list[Panel]) -> None:
        current = order[-1]
        if not remaining:
            if exit_(current) is None:
                solutions.append(order[:])
            return
        wanted = exit_(current)
        if wanted is None:
            return
        for panel in remaining:
            if entry(panel) == wanted:
                extend(order + [panel], [p for p in remaining if p is not panel])

    for start in starts:
        extend([start], [p for p in panels if p is not start])
    return solutions


def analyze(grid: list[list[int]]) -> dict:
    grid = _grid(grid)
    h, w = len(grid), len(grid[0])
    separator_rows = [r for r, row in enumerate(grid) if all(value == 6 for value in row)]
    separator_cols = [c for c in range(w) if all(grid[r][c] == 6 for r in range(h))]
    row_bands = _bands(h, separator_rows)
    col_bands = _bands(w, separator_cols)
    if not row_bands or not col_bands:
        raise ValueError("need a complete color-6 separator lattice")
    panels: list[Panel] = []
    source_index = 0
    for r0, r1 in row_bands:
        for c0, c1 in col_bands:
            raw = [row[c0:c1] for row in grid[r0:r1]]
            parsed = _panel(source_index, raw)
            if parsed is not None:
                panels.append(parsed)
                source_index += 1
    if len(panels) < 2:
        raise ValueError("need at least two occupied panels")
    vertical = all(p.west is None and p.east is None for p in panels)
    horizontal = all(p.north is None and p.south is None for p in panels)
    if vertical == horizontal:
        raise ValueError("panels must form exactly one vertical or horizontal contact grammar")
    orientation = "vertical" if vertical else "horizontal"
    orders = _orders(panels, orientation)
    if len(orders) != 1:
        raise ValueError("panel contacts must determine one complete chain")
    return {
        "grid": grid,
        "separator_rows": separator_rows,
        "separator_cols": separator_cols,
        "panels": panels,
        "ordered": orders[0],
        "orientation": orientation,
    }


def _render_panel(panel: Panel, highlight: bool) -> list[list[int]]:
    if not highlight:
        return [row[:] for row in panel.grid]
    return [[9 if value != 7 else 7 for value in row] for row in panel.grid]


def _assemble(ordered: list[Panel], orientation: str, chosen_source: int | None) -> list[list[int]]:
    rendered = [_render_panel(panel, panel.source_index == chosen_source) for panel in ordered]
    if orientation == "vertical":
        output: list[list[int]] = []
        for index, panel in enumerate(rendered):
            output.extend([row[:] for row in panel])
            if index + 1 < len(rendered):
                output.append([6] * 5)
        return output
    output = []
    for r in range(5):
        row: list[int] = []
        for index, panel in enumerate(rendered):
            row.extend(panel[r])
            if index + 1 < len(rendered):
                row.append(6)
        output.append(row)
    return output


def solve(grid: list[list[int]], finish: str = "chain_only") -> list[list[int]]:
    if finish not in PARAMETERS["finish"]:
        raise ValueError("finish must be chain_only or highlight_chain_center")
    state = analyze(grid)
    chosen = None
    if finish == "highlight_chain_center":
        ordered = state["ordered"]
        if len(ordered) % 2 != 1:
            raise ValueError("highlight setting requires an odd panel count")
        chosen = ordered[len(ordered) // 2].source_index
    return _assemble(state["ordered"], state["orientation"], chosen)


def solve_wrong_source_center(grid: list[list[int]]) -> list[list[int]]:
    state = analyze(grid)
    panels = state["panels"]
    if len(panels) % 2 != 1:
        raise ValueError("counterfactual requires an odd panel count")
    chosen = panels[len(panels) // 2].source_index
    return _assemble(state["ordered"], state["orientation"], chosen)


def _vertical_panel(entry: int | None, exit_: int | None, color: int, variant: int) -> list[list[int]]:
    grid = [[7] * 5 for _ in range(5)]
    if entry is None and exit_ is None:
        raise ValueError("panel cannot omit both chain contacts")
    cells: set[tuple[int, int]] = set()
    pivot = 1 + (variant % 3)
    if entry is None:
        branch = 1 + ((exit_ + variant) % 3)
        for r in range(pivot, 5):
            cells.add((r, exit_))
        for c in range(min(branch, exit_), max(branch, exit_) + 1):
            cells.add((pivot, c))
    elif exit_ is None:
        branch = 1 + ((entry + variant + 1) % 3)
        for r in range(0, pivot + 1):
            cells.add((r, entry))
        for c in range(min(branch, entry), max(branch, entry) + 1):
            cells.add((pivot, c))
    else:
        for r in range(0, pivot + 1):
            cells.add((r, entry))
        for c in range(min(entry, exit_), max(entry, exit_) + 1):
            cells.add((pivot, c))
        for r in range(pivot, 5):
            cells.add((r, exit_))
        if variant % 2 and pivot in (1, 3):
            spur_r = 2
            cells.add((spur_r, exit_))
    for r, c in cells:
        grid[r][c] = color
    return grid


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _scene(seed: int, index: int) -> list[list[int]]:
    rng = random.Random((seed + 1) * 1000003 + index * 7919)
    profiles = [
        (3, 2, 2, False), (3, 1, 3, False), (5, 1, 5, False),
        (3, 3, 1, False), (5, 5, 1, False), (5, 1, 5, False),
        (3, 2, 2, False), (5, 1, 5, False), (3, 3, 1, False),
        (5, 5, 5, True),
    ]
    count, layout_rows, layout_cols, trailing = profiles[index]
    orientation = "vertical" if (seed + index) % 2 == 0 else "horizontal"
    contacts = [1, 2, 3]
    rng.shuffle(contacts)
    links = contacts[:2] if count == 3 else [contacts[0], contacts[1], contacts[2], contacts[0]]
    palette = sorted(rng.sample([1, 2, 3, 4, 8], count))
    # Guarantee that contact order cannot collapse to ascending color order.
    colors = ([palette[2], palette[0], palette[1]] if count == 3 else
              [palette[4], palette[0], palette[3], palette[1], palette[2]])
    panels: list[list[list[int]]] = []
    for i in range(count):
        entry = links[i - 1] if i else None
        exit_ = links[i] if i + 1 < count else None
        panel = _vertical_panel(entry, exit_, colors[i], seed + index * 7 + i)
        if i == 0:
            # Make a noncentral endpoint visibly larger than the true chain
            # center, so area/ink proxies cannot explain the alternate.
            for rr in range(1, 4):
                for cc in range(1, 4):
                    panel[rr][cc] = colors[i]
        panels.append(panel if orientation == "vertical" else _transpose(panel))

    source_permutation = ([1, 0, 2] if count == 3 else [2, 0, 4, 1, 3])
    if (seed + index) % 2:
        source_permutation = list(reversed(source_permutation))
    # Reversal can put the true center in the source center for the three-panel
    # case; rotate once to preserve the intentional source-order counterexample.
    if source_permutation[len(source_permutation) // 2] == count // 2:
        source_permutation = source_permutation[1:] + source_permutation[:1]

    height = layout_rows * 6 if trailing else layout_rows * 6 - 1
    width = layout_cols * 6 if trailing else layout_cols * 6 - 1
    grid = [[7] * width for _ in range(height)]
    for r in range(5, height, 6):
        grid[r] = [6] * width
    for c in range(5, width, 6):
        for r in range(height):
            grid[r][c] = 6

    slots = [(r, c) for r in range(layout_rows) for c in range(layout_cols)]
    if trailing:
        rng.shuffle(slots)
        occupied_slots = sorted(slots[:count])
    else:
        occupied_slots = slots[:count]
    for slot, chain_index in zip(occupied_slots, source_permutation):
        br, bc = slot
        panel = panels[chain_index]
        r0, c0 = br * 6, bc * 6
        for r in range(5):
            for c in range(5):
                grid[r0 + r][c0 + c] = panel[r][c]

    state = analyze(grid)
    if [panel.source_index for panel in state["ordered"]] == [panel.source_index for panel in state["panels"]]:
        raise AssertionError("constructed source order accidentally equals chain order")
    if state["ordered"][count // 2].source_index == state["panels"][count // 2].source_index:
        raise AssertionError("source center accidentally equals chain center")
    return grid


def input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    grids = [_scene(seed, index) for index in range(10)]
    queries = grids[6:]
    random.Random(seed ^ 0x78332CB0).shuffle(queries)
    return grids[:6], queries


def _finish(settings: dict) -> str:
    if (type(settings) is not dict or set(settings) != {"finish"}
            or settings["finish"] not in PARAMETERS["finish"]):
        raise ValueError("settings must be exactly finish=chain_only or highlight_chain_center")
    return settings["finish"]


def canonical_source() -> str:
    return Path(__file__).with_name("canonical.rkt").read_text()


def program(settings: dict) -> str:
    finish = _finish(settings)
    source = canonical_source()
    if finish == "chain_only":
        return source
    marker = "(define highlight-center #f)"
    if source.count(marker) != 1:
        raise RuntimeError("canonical highlight marker drift")
    return source.replace(marker, "(define highlight-center #t)", 1)


def wrong_program() -> str:
    source = program({"finish": "highlight_chain_center"})
    marker = "(define wrong-source-center #f)"
    if source.count(marker) != 1:
        raise RuntimeError("canonical wrong-center marker drift")
    return source.replace(marker, "(define wrong-source-center #t)", 1)


def generate(seed: int = 0, settings: dict | None = None, demos: int = 3,
             queries: int = 4) -> dict:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"finish": PARAMETERS["finish"][seed % 2]}
    finish = _finish(settings)
    demo_inputs, query_inputs = input_bank(seed)
    return {
        "train": [{"input": copy.deepcopy(grid), "output": solve(grid, finish)}
                  for grid in demo_inputs[:demos]],
        "test": [{"input": copy.deepcopy(grid), "output": solve(grid, finish)}
                 for grid in query_inputs[:queries]],
        "program_solution": program(settings),
    }

"""Deterministic matched-input authoring prototype for template relay variants."""
from __future__ import annotations

import random
from typing import Iterable

MODES = ("canonical", "match_count_relay")
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

SHAPES = (
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
)


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def validate_request(seed: int, settings: dict, demos: int, queries: int) -> str:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, *DEMO_LIMITS)
    _integer("queries", queries, *QUERY_LIMITS)
    if not isinstance(settings, dict) or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def _profile(index: int, *, query: bool) -> tuple[int, int]:
    if query:
        return ((11, 14), (15, 18), (20, 22), (30, 26))[index]
    return ((9, 10), (10, 13), (12, 16), (14, 18), (16, 20), (18, 22))[index]


def _target_count(index: int, *, query: bool) -> int:
    return ((1, 3, 2, 2) if query else (2, 3, 1, 2, 3, 1))[index]


def _rotate(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    rotated = [(c, -r) for r, c in shape]
    r0 = min(r for r, _ in rotated)
    c0 = min(c for _, c in rotated)
    return tuple(sorted((r - r0, c - c0) for r, c in rotated))


def _split(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    h = len(grid)
    divider = next(c for c in range(len(grid[0])) if all(grid[r][c] == 9 for r in range(h)))
    return [row[:divider] for row in grid], [row[divider + 1:] for row in grid]


def _crop(panel: list[list[int]]) -> list[list[int]]:
    cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value not in (0, 9)]
    if not cells:
        raise ValueError("template panel has no nonzero cells")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in panel[r0:r1 + 1]]


def _matches(board: list[list[int]], template: list[list[int]], *, literal_zero: bool = False) -> list[tuple[int, int]]:
    th, tw = len(template), len(template[0])
    result = []
    for r0 in range(len(board) - th + 1):
        for c0 in range(len(board[0]) - tw + 1):
            okay = True
            for r in range(th):
                for c in range(tw):
                    tv = template[r][c]
                    bv = board[r0 + r][c0 + c]
                    if (bv != tv) if literal_zero else (tv != 0 and bv != tv):
                        okay = False
                        break
                if not okay:
                    break
            if okay:
                result.append((r0, c0))
    return result


def _render(board: list[list[int]], positions: Iterable[tuple[int, int]]) -> list[list[int]]:
    out = [[0 for _ in row] for row in board]
    for r, c in positions:
        out[r][c] = 8
    return out


def _anchors(board: list[list[int]]) -> list[tuple[int, int]]:
    anchors = [(r, c) for r, row in enumerate(board) for c, value in enumerate(row) if value == 6]
    if len(anchors) != 3:
        raise ValueError(f"expected exactly three relay anchors, found {len(anchors)}")
    return anchors


def canonical_output(grid: list[list[int]]) -> list[list[int]]:
    panel, board = _split(grid)
    template = _crop(panel)
    th, tw = len(template), len(template[0])
    return _render(board, ((r + th - 1, c + tw - 1) for r, c in _matches(board, template)))


def match_count(grid: list[list[int]]) -> int:
    panel, board = _split(grid)
    value = len(_matches(board, _crop(panel)))
    if value not in (1, 2, 3):
        raise ValueError(f"match count must be 1..3, found {value}")
    return value


def literal_zero_intermediate(grid: list[list[int]]) -> int:
    panel, board = _split(grid)
    raw = len(_matches(board, _crop(panel), literal_zero=True))
    return max(1, min(3, raw))


def _relay_with_intermediate(grid: list[list[int]], value: int) -> list[list[int]]:
    _, board = _split(grid)
    out = canonical_output(grid)
    r, c = _anchors(board)[value - 1]
    out[r][c] = 8
    return out


def relay_output(grid: list[list[int]]) -> list[list[int]]:
    return _relay_with_intermediate(grid, match_count(grid))


def literal_zero_relay_output(grid: list[list[int]]) -> list[list[int]]:
    return _relay_with_intermediate(grid, literal_zero_intermediate(grid))


def fixed_relay_output(grid: list[list[int]], value: int) -> list[list[int]]:
    return _relay_with_intermediate(grid, value)


def component_count_relay_output(grid: list[list[int]]) -> list[list[int]]:
    panel, board = _split(grid)
    template = _crop(panel)
    color = next(value for row in template for value in row if value != 0)
    seen: set[tuple[int, int]] = set()
    components = 0
    for r in range(len(board)):
        for c in range(len(board[0])):
            if board[r][c] != color or (r, c) in seen:
                continue
            components += 1
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < len(board) and 0 <= nc < len(board[0]) and board[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return _relay_with_intermediate(grid, max(1, min(3, components)))


def _stamp(board: list[list[int]], anchor: tuple[int, int], shape: Iterable[tuple[int, int]], color: int) -> None:
    r0, c0 = anchor
    for dr, dc in shape:
        board[r0 + dr][c0 + dc] = color


def build_input(seed: int, index: int, *, query: bool) -> list[list[int]]:
    h, bw = _profile(index, query=query)
    k = _target_count(index, query=query)
    rng = random.Random((seed + 1) * 1_000_003 + (index + 1) * 97_409 + (17_000_003 if query else 0))
    base_shape_index = (seed + index + (1 if query else 0)) % len(SHAPES)
    true_anchors = ((1, 1), (1, bw - 4), (h - 4, 1))[:k]
    decoy_anchor = (h - 4, bw - 4)

    for attempt in range(len(SHAPES)):
        shape = SHAPES[(base_shape_index + attempt) % len(SHAPES)]
        rotated = _rotate(shape)
        if rotated == tuple(sorted(shape)):
            continue
        template_color = (1, 2, 3)[(seed + index + attempt) % 3]
        board = [[0 for _ in range(bw)] for _ in range(h)]
        windows: list[set[tuple[int, int]]] = []
        for anchor in true_anchors:
            _stamp(board, anchor, shape, template_color)
            window = {(anchor[0] + r, anchor[1] + c) for r in range(3) for c in range(3)}
            windows.append(window)
            wildcard = next((r, c) for r in range(3) for c in range(3) if (r, c) not in shape)
            board[anchor[0] + wildcard[0]][anchor[1] + wildcard[1]] = (4, 5, 7)[len(windows) % 3]
        _stamp(board, decoy_anchor, rotated, template_color)
        windows.append({(decoy_anchor[0] + r, decoy_anchor[1] + c) for r in range(3) for c in range(3)})
        forbidden = set().union(*windows)
        canonical_corners = {(r + 2, c + 2) for r, c in true_anchors}
        free = [(r, c) for r in range(h) for c in range(bw) if (r, c) not in forbidden and (r, c) not in canonical_corners]
        picks = [free[0], free[len(free) // 2], free[-1]]
        if len(set(picks)) != 3:
            raise ValueError("not enough relay-anchor space")
        for r, c in picks:
            board[r][c] = 6
        noise_colors = [value for value in (3, 4, 5, 7, 8) if value != template_color]
        noise_free = [cell for cell in free if cell not in picks]
        rng.shuffle(noise_free)
        noise_target = min(len(noise_free), max(12, (h * bw) // 20))
        for offset, (r, c) in enumerate(noise_free[:noise_target]):
            board[r][c] = noise_colors[offset % len(noise_colors)]

        panel = [[0, 0, 0] for _ in range(h)]
        for r, c in shape:
            panel[r][c] = template_color
        grid = [panel[r] + [9] + board[r] for r in range(h)]
        actual = _matches(board, _crop(panel))
        if actual == list(true_anchors) and len(_anchors(board)) == 3:
            return grid
    raise ValueError("could not construct an exact-match scene")


def generate_pairs(seed: int, demos: int, queries: int, mode: str) -> list[dict]:
    output = canonical_output if mode == "canonical" else relay_output
    pairs: list[dict] = []
    for index in range(demos):
        grid = build_input(seed, index, query=False)
        pairs.append({"input": grid, "output": output(grid)})
    for index in range(queries):
        grid = build_input(seed, index, query=True)
        pairs.append({"input": grid, "output": output(grid)})
    return pairs

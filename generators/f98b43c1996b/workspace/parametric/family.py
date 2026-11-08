"""Native matched-input family for f98b43c1996b.

The byte-exact default diagonalizes every solid monochrome 2x2 block.  The
alternative deliberately depends on that complete intermediate: it counts
colors after diagonalization and recolors the unique most frequent surviving
color to 8.  Constructive scenes make the most frequent source color lose its
lead after its repeated 2x2 blocks are halved, so ranking before Step A is a
causally wrong shortcut rather than an equivalent description.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "f98b43c1996b"
HERE = Path(__file__).resolve().parent
CANONICAL_SHA256 = "cbbce09642403fc1eb6a638c8fcb91255d8fa270587658c2ef5ea64259c09048"
SETTINGS = ("diagonalize_only", "highlight_most_frequent_post_color")
RIVALS = (
    "highlight_pre_frequency",
    "highlight_lowest_post_color",
    "highlight_highest_post_color",
    "highlight_first_post_color",
    "highlight_all_post_colors",
)
HYPOTHESES = SETTINGS + RIVALS

# height, width, number of repeated source-leading 2x2 blocks
_DEMO_PROFILES = (
    (8, 10, 2),
    (10, 12, 2),
    (12, 15, 3),
    (16, 18, 4),
    (22, 24, 5),
    (26, 28, 6),
)
_QUERY_PROFILES = (
    (11, 13, 2),
    (18, 21, 4),
    (24, 27, 6),
    (30, 30, 8),
)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(value: object) -> str:
    if type(value) is not dict or set(value) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    finish = value["finish"]
    if type(finish) is not str or finish not in SETTINGS:
        raise ValueError(f"finish must be one of {SETTINGS!r}")
    return finish


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 2 <= len(value) <= 30
        or type(value[0]) is not list
        or not 2 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be a rectangular 2..30 ARC grid")
    return value


def _rng(seed: int, role: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:post-frequency-v1:{seed}:{role}".encode("utf-8")
    ).digest()
    return random.Random(digest)


def canonical_program() -> str:
    text = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if hashlib.sha256(text.encode()).hexdigest() != CANONICAL_SHA256:
        raise RuntimeError("canonical.rkt no longer matches the frozen target")
    return text


def alternative_program() -> str:
    return (HERE / "highlight_most_frequent_post_color.rkt").read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "highlight_pre_frequency.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    finish = _setting(settings)
    return canonical_program() if finish == "diagonalize_only" else alternative_program()


def diagonalize(value: object) -> list[list[int]]:
    source = _grid(value)
    out = deepcopy(source)
    h, w = len(source), len(source[0])
    for r in range(h - 1):
        for c in range(w - 1):
            color = source[r][c]
            if (
                color != 0
                and source[r][c + 1] == color
                and source[r + 1][c] == color
                and source[r + 1][c + 1] == color
            ):
                out[r][c] = color
                out[r][c + 1] = 0
                out[r + 1][c] = 0
                out[r + 1][c + 1] = color
    return out


def _counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(cell for row in grid for cell in row if cell != 0)


def _unique_winner(counts: Counter[int]) -> tuple[int | None, bool]:
    if not counts:
        return None, False
    best = max(counts.values())
    winners = sorted(color for color, count in counts.items() if count == best)
    return (winners[0] if len(winners) == 1 else None), len(winners) == 1


def analyze(value: object) -> dict[str, Any]:
    source = _grid(value)
    mid = diagonalize(source)
    pre_counts = _counts(source)
    post_counts = _counts(mid)
    pre_winner, pre_unique = _unique_winner(pre_counts)
    post_winner, post_unique = _unique_winner(post_counts)
    fires = []
    for r in range(len(source) - 1):
        for c in range(len(source[0]) - 1):
            color = source[r][c]
            if (
                color != 0
                and source[r][c + 1] == color
                and source[r + 1][c] == color
                and source[r + 1][c + 1] == color
            ):
                fires.append((r, c, color))
    return {
        "height": len(source),
        "width": len(source[0]),
        "pre_counts": dict(sorted(pre_counts.items())),
        "post_counts": dict(sorted(post_counts.items())),
        "pre_winner": pre_winner,
        "post_winner": post_winner,
        "pre_winner_unique": pre_unique,
        "post_winner_unique": post_unique,
        "solid_windows": fires,
        "intermediate": mid,
    }


def _highlight(grid: list[list[int]], selected: Iterable[int]) -> list[list[int]]:
    chosen = set(selected)
    return [[8 if cell in chosen else cell for cell in row] for row in grid]


def predict(value: object, hypothesis: str) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis {hypothesis!r}")
    state = analyze(value)
    mid = state["intermediate"]
    if hypothesis == "diagonalize_only":
        return deepcopy(mid)
    colors = sorted(state["post_counts"])
    if hypothesis == "highlight_most_frequent_post_color":
        selected = [state["post_winner"]]
    elif hypothesis == "highlight_pre_frequency":
        selected = [state["pre_winner"]]
    elif hypothesis == "highlight_lowest_post_color":
        selected = [min(colors)]
    elif hypothesis == "highlight_highest_post_color":
        selected = [max(colors)]
    elif hypothesis == "highlight_first_post_color":
        selected = [next(cell for row in mid for cell in row if cell != 0)]
    elif hypothesis == "highlight_all_post_colors":
        selected = colors
    else:  # pragma: no cover - guarded above
        raise AssertionError(hypothesis)
    return _highlight(mid, selected)


def solve(value: object, finish: str) -> list[list[int]]:
    if finish not in SETTINGS:
        raise ValueError(f"finish must be one of {SETTINGS!r}")
    return predict(value, finish)


def _normalize(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(shape)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _winner_shape(size: int, variant: int) -> tuple[tuple[int, int], ...]:
    if variant % 3 == 0:
        return tuple((0, c) for c in range(size))
    if variant % 3 == 1:
        return tuple((r, 0) for r in range(size))
    horizontal = (size + 1) // 2
    vertical = size - horizontal + 1
    return _normalize(
        [(0, c) for c in range(horizontal)]
        + [(r, 0) for r in range(1, vertical)]
    )


def _anchors(h: int, w: int, shape: tuple[tuple[int, int], ...], edge: str | None):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    if edge == "top":
        candidates = [(r, c) for r, c in candidates if r == 0]
    elif edge == "bottom":
        candidates = [(r, c) for r, c in candidates if r + sh == h]
    elif edge == "left":
        candidates = [(r, c) for r, c in candidates if c == 0]
    elif edge == "right":
        candidates = [(r, c) for r, c in candidates if c + sw == w]
    return candidates


def _place(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    color: int,
    rng: random.Random,
    *,
    edge: str | None = None,
    same_color_moat: bool = True,
) -> set[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    candidates = _anchors(h, w, shape, edge)
    rng.shuffle(candidates)
    for ar, ac in candidates:
        cells = {(ar + dr, ac + dc) for dr, dc in shape}
        if any(grid[r][c] != 0 for r, c in cells):
            continue
        if same_color_moat:
            neighbors = {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= r + dr < h and 0 <= c + dc < w
            }
            if any(grid[r][c] == color for r, c in neighbors - cells):
                continue
        for r, c in cells:
            grid[r][c] = color
        return cells
    raise RuntimeError(f"unable to place color {color} shape of {len(shape)} cells")


def _scene(seed: int, role: str, profile: tuple[int, int, int], index: int) -> list[list[int]]:
    h, w, blocks = profile
    rng = _rng(seed, f"{role}:{index}")
    grid = [[0 for _ in range(w)] for _ in range(h)]

    # The source leader is color 2: 4*blocks before A, 2*blocks after A.
    # Its first block at the upper-left also guarantees boundary stress and
    # makes the row-major shortcut choose 2 rather than the true post winner 5.
    block = ((0, 0), (0, 1), (1, 0), (1, 1))
    for r, c in block:
        grid[r][c] = 2
    for _ in range(blocks - 1):
        _place(grid, block, 2, rng)

    # The post-A leader is color 5 with 2*blocks+1 cells and no solid 2x2.
    winner = _winner_shape(2 * blocks + 1, index + seed)
    _place(grid, winner, 5, rng, edge=("bottom" if index % 2 else "right"))

    # Two independent exact blocks preserve the source task's structural
    # grammar and push the 30x30 query above the substantive-cell threshold.
    _place(grid, block, 3, rng)
    _place(grid, block, 7, rng)

    # Low/high palette witnesses defeat numeric extrema; three-cell lines stay
    # below the unique post leader even for the smallest profile.
    low_shape = ((0, 0), (0, 1), (0, 2))
    high_shape = ((0, 0), (1, 0), (2, 0))
    _place(grid, low_shape, 1, rng)
    _place(grid, high_shape, 9, rng)

    state = analyze(grid)
    if not (
        state["pre_winner_unique"]
        and state["post_winner_unique"]
        and state["pre_winner"] == 2
        and state["post_winner"] == 5
        and state["pre_winner"] != state["post_winner"]
    ):
        raise RuntimeError(f"constructed frequency witness failed: {state}")
    return grid


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, Any]:
    seed_i = _integer(seed, "seed", 0, 2**63 - 1)
    finish = _setting(settings)
    demos_i = _integer(demos, "demos", 2, 6)
    queries_i = _integer(queries, "queries", 1, 4)

    demo_inputs = [
        _scene(seed_i, "demo", profile, index)
        for index, profile in enumerate(_DEMO_PROFILES[:demos_i])
    ]
    query_inputs = [
        _scene(seed_i, "query", profile, index)
        for index, profile in enumerate(_QUERY_PROFILES[:queries_i])
    ]
    all_inputs = demo_inputs + query_inputs
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("family generated duplicate inputs")

    train = [{"input": grid, "output": solve(grid, finish)} for grid in demo_inputs]
    test = [{"input": grid, "output": solve(grid, finish)} for grid in query_inputs]
    return {
        "program_solution": program({"finish": finish}),
        "train": train,
        "test": test,
        "private_query_bank": deepcopy(test),
        "metadata": {
            "task_id": TASK_ID,
            "settings": {"finish": finish},
            "seed": seed_i,
            "dependency": (
                "Step A diagonalizes exact solid monochrome 2x2 blocks; Step B "
                "ranks the colors in that transformed grid and highlights the "
                "unique largest surviving footprint."
            ),
        },
    }

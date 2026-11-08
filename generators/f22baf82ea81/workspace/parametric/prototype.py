"""Native matched-input family for crop/swap followed by an output orientation."""
from __future__ import annotations

import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "f22baf82ea81"
TRANSFORMS = ("as_is", "rotate_cw")
DEFAULT_TRANSFORM = "as_is"
HERE = Path(__file__).resolve().parent
PROGRAM_PATHS = {
    "as_is": HERE / "canonical.rkt",
    "rotate_cw": HERE / "rotate_cw.rkt",
}
CANDIDATE_RULES = (
    "as_is",
    "rotate_cw",
    "rotate_ccw",
    "rotate_180",
    "transpose",
    "crop_only_as_is",
    "crop_only_rotate_cw",
    "solid_bbox_as_is",
    "solid_bbox_rotate_cw",
    "swap_full_grid",
)

# Full six-demo/four-query bank, always constructed before slicing.
_TRAIN_PROFILES = (
    (10, 13, 4, 7, "l"),
    (12, 10, 7, 4, "zigzag"),
    (15, 15, 5, 8, "off_rect"),
    (18, 13, 9, 6, "ring"),
    (21, 24, 11, 15, "plus"),
    (27, 26, 16, 12, "growth"),
)
_TEST_PROFILES = (
    (9, 14, 3, 8, "zigzag"),
    (16, 19, 8, 11, "off_rect"),
    (24, 27, 14, 20, "ring"),
    (30, 30, 24, 26, "growth"),
)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def validate_transform(value: Any) -> str:
    if type(value) is not str or value not in TRANSFORMS:
        raise ValueError(f"post_transform must be one of {TRANSFORMS}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"post_transform"}:
        raise ValueError("settings must contain exactly post_transform")
    return validate_transform(settings["post_transform"])


def validate_request(seed: Any, demos: Any, queries: Any) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)


def program_for(transform: str) -> str:
    return PROGRAM_PATHS[validate_transform(transform)].read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(v) is not int or not 0 <= v <= 9 for v in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors")
    return [row[:] for row in grid]


def self_check(grid: Any) -> list[str]:
    try:
        g = _validate_grid(grid)
    except ValueError as exc:
        return [str(exc)]
    h, w = len(g), len(g[0])
    cells = [(r, c, g[r][c]) for r in range(h) for c in range(w) if g[r][c] != 0]
    if not cells:
        return ["missing nonzero region"]
    colors = {v for _, _, v in cells}
    errors: list[str] = []
    if len(colors) != 2:
        errors.append("expected exactly two nonzero colors")
    r0 = min(r for r, _, _ in cells)
    r1 = max(r for r, _, _ in cells)
    c0 = min(c for _, c, _ in cells)
    c1 = max(c for _, c, _ in cells)
    if r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1:
        errors.append("region must retain a zero margin")
    if any(g[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
        errors.append("region bbox contains a background hole")
    outer = g[r0][c0]
    inner = colors - {outer}
    if len(inner) != 1:
        errors.append("top-left outer color must have one distinct inner color")
    elif not any(g[r][c] in inner for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
        errors.append("inner color must occur strictly inside the bbox")
    return errors


def crop(grid: list[list[int]]) -> list[list[int]]:
    g = _validate_grid(grid)
    cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v != 0]
    if not cells:
        raise ValueError("cannot crop an empty region")
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in g[r0 : r1 + 1]]


def swapped_crop(grid: list[list[int]]) -> list[list[int]]:
    base = crop(grid)
    outer = base[0][0]
    inner = next((v for row in base for v in row if v != outer), 0)
    return [[inner if v == outer else outer if v == inner else v for v in row] for row in base]


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    g = _validate_grid(grid)
    h, w = len(g), len(g[0])
    return [[g[h - 1 - c][r] for c in range(h)] for r in range(w)]


def rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return rotate_cw(rotate_cw(rotate_cw(grid)))


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return rotate_cw(rotate_cw(grid))


def transpose(grid: list[list[int]]) -> list[list[int]]:
    g = _validate_grid(grid)
    return [[g[r][c] for r in range(len(g))] for c in range(len(g[0]))]


def solve(grid: list[list[int]], transform: str) -> list[list[int]]:
    transform = validate_transform(transform)
    intermediate = swapped_crop(grid)
    return intermediate if transform == "as_is" else rotate_cw(intermediate)


def _solidified_swapped_crop(grid: list[list[int]]) -> list[list[int]]:
    base = crop(grid)
    outer = base[0][0]
    inner = next(v for row in base for v in row if v != outer)
    cells = [(r, c) for r, row in enumerate(base) for c, v in enumerate(row) if v == inner]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    solid = [row[:] for row in base]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            solid[r][c] = inner
    return [[inner if v == outer else outer if v == inner else v for v in row] for row in solid]


def _swap_full_grid(grid: list[list[int]]) -> list[list[int]]:
    g = _validate_grid(grid)
    cells = [(r, c, v) for r, row in enumerate(g) for c, v in enumerate(row) if v != 0]
    outer = min(cells, key=lambda item: (item[0], item[1]))[2]
    inner = next(v for _, _, v in cells if v != outer)
    return [[inner if v == outer else outer if v == inner else v for v in row] for row in g]


def solve_candidate(grid: list[list[int]], name: str) -> list[list[int]]:
    if name == "as_is":
        return solve(grid, "as_is")
    if name == "rotate_cw":
        return solve(grid, "rotate_cw")
    intermediate = swapped_crop(grid)
    if name == "rotate_ccw":
        return rotate_ccw(intermediate)
    if name == "rotate_180":
        return rotate_180(intermediate)
    if name == "transpose":
        return transpose(intermediate)
    if name == "crop_only_as_is":
        return crop(grid)
    if name == "crop_only_rotate_cw":
        return rotate_cw(crop(grid))
    if name == "solid_bbox_as_is":
        return _solidified_swapped_crop(grid)
    if name == "solid_bbox_rotate_cw":
        return rotate_cw(_solidified_swapped_crop(grid))
    if name == "swap_full_grid":
        return _swap_full_grid(grid)
    raise ValueError(f"unknown candidate {name}")


def teaching_survivors(train: list[dict[str, list[list[int]]]]) -> list[str]:
    return [
        name
        for name in CANDIDATE_RULES
        if all(solve_candidate(pair["input"], name) == pair["output"] for pair in train)
    ]


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _reflect(
    cells: set[tuple[int, int]], ih: int, iw: int, flip_r: bool, flip_c: bool
) -> set[tuple[int, int]]:
    result = set(cells)
    if flip_r:
        result = {(ih - 1 - r, c) for r, c in result}
    if flip_c:
        result = {(r, iw - 1 - c) for r, c in result}
    return result


def _inner_cells(kind: str, rh: int, rw: int, rng: random.Random) -> set[tuple[int, int]]:
    ih, iw = rh - 2, rw - 2
    if ih <= 0 or iw <= 0:
        return {(1, 1)}
    if kind == "off_rect":
        sh = max(1, ih // 2)
        sw = max(1, iw // 2)
        r0 = 0 if rng.random() < 0.5 else ih - sh
        c0 = 0 if rng.random() < 0.5 else iw - sw
        local = {(r, c) for r in range(r0, r0 + sh) for c in range(c0, c0 + sw)}
    elif kind == "ring" and ih >= 3 and iw >= 3:
        local = {
            (r, c)
            for r in range(ih)
            for c in range(iw)
            if r in (0, ih - 1) or c in (0, iw - 1)
        }
    elif kind == "plus":
        mr, mc = ih // 2, iw // 2
        local = {(mr, c) for c in range(iw)} | {(r, mc) for r in range(ih)}
    elif kind == "zigzag":
        local: set[tuple[int, int]] = set()
        row = 0
        for c in range(iw):
            local.add((row, c))
            if c + 1 < iw and row + 1 < ih:
                row += 1
                local.add((row, c))
        local |= {(r, iw - 1) for r in range(row, ih)}
    elif kind == "growth":
        area = ih * iw
        target = max(1, min(area - 1 if area > 1 else 1, int(round(area * 0.48))))
        local = {(rng.randrange(ih), rng.randrange(iw))}
        while len(local) < target:
            frontier = sorted(
                {
                    (nr, nc)
                    for r, c in local
                    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                    if 0 <= nr < ih and 0 <= nc < iw and (nr, nc) not in local
                }
            )
            if not frontier:
                break
            local.add(rng.choice(frontier))
    else:
        local = {(r, 0) for r in range(ih)} | {(ih - 1, c) for c in range(iw)}
    local = _reflect(local, ih, iw, rng.random() < 0.5, rng.random() < 0.5)
    return {(r + 1, c + 1) for r, c in local}


def _scene(
    seed: int,
    split: str,
    index: int,
    profile: tuple[int, int, int, int, str],
) -> list[list[int]]:
    gh, gw, rh, rw, kind = profile
    rng = _rng(seed, split, index)
    if rh > gh - 2 or rw > gw - 2:
        raise ValueError("profile region must retain a background margin")
    rr = rng.randint(1, gh - rh - 1)
    rc = rng.randint(1, gw - rw - 1)
    outer, inner = rng.sample(list(range(1, 10)), 2)
    grid = [[0 for _ in range(gw)] for _ in range(gh)]
    for r in range(rr, rr + rh):
        for c in range(rc, rc + rw):
            grid[r][c] = outer
    for r, c in _inner_cells(kind, rh, rw, rng):
        grid[rr + r][rc + c] = inner
    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid scene: {errors}")
    return grid


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    train = [_scene(seed, "train", i, profile) for i, profile in enumerate(_TRAIN_PROFILES)]
    test = [_scene(seed, "test", i, profile) for i, profile in enumerate(_TEST_PROFILES)]
    frozen = {tuple(tuple(row) for row in grid) for grid in train + test}
    if len(frozen) != 10:
        raise RuntimeError("constructed duplicate inputs")
    return {"train": train, "test": test}


def generate_episode(
    seed: int, transform: str, demos: int = 2, queries: int = 4
) -> dict[str, Any]:
    validate_request(seed, demos, queries)
    transform = validate_transform(transform)
    bank = episode_inputs(seed)
    train = [
        {"input": grid, "output": solve(grid, transform)}
        for grid in bank["train"][:demos]
    ]
    test = [
        {"input": grid, "output": solve(grid, transform)}
        for grid in bank["test"][:queries]
    ]
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(transform),
    }

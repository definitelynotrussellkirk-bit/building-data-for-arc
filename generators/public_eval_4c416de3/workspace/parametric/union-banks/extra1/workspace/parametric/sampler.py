"""Standalone corner-motif replication generator for public ARC task 4c416de3."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_4c416de3"
RULE_TASK_ID = 'ee_4c416de3'
VERSION = "1.0.0"
SUMMARY = "Recover a complete motif at one hollow-frame corner and transport it to marker-bearing corners in each marker color."
INVARIANTS = [
    "dominant non-frame background",
    "axis-aligned hollow zero frames",
    "one complete source motif with outward cells",
    "targets retain only the deepest inward diagonal marker",
]
SETTINGS = ("reflect", "rotate")
CORNER_KINDS = ("TL", "TR", "BL", "BR")
EDGE_DIRS = {
    "TL": ((1, 0), (0, 1)), "TR": ((1, 0), (0, -1)),
    "BL": ((-1, 0), (0, 1)), "BR": ((-1, 0), (0, -1)),
}
OUT_DIRS = {
    "TL": ((-1, 0), (0, -1)), "TR": ((-1, 0), (0, 1)),
    "BL": ((1, 0), (0, -1)), "BR": ((1, 0), (0, 1)),
}
NEIGHBORHOOD = 3


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _transport(value: object) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("transport must be reflect or rotate")
    return value


def _parse_grid(grid: object) -> tuple[list[list[int]], int, int, int]:
    if type(grid) is not list or not 5 <= len(grid) <= 30:
        raise ValueError("grid height must be an exact list in 5..30")
    if type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be an exact list in 5..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("rectangular exact list rows required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("exact integer ARC colors 0..9 required")
    copied = [row[:] for row in grid]
    background = Counter(v for row in copied for v in row).most_common(1)[0][0]
    if background == 0:
        raise ValueError("the dominant background must differ from zero frame color")
    return copied, len(copied), width, background


def _reflect_offset(dr: int, dc: int, kind: str) -> tuple[int, int]:
    if kind == "TL": return dr, dc
    if kind == "TR": return dr, -dc
    if kind == "BL": return -dr, dc
    if kind == "BR": return -dr, -dc
    raise ValueError(f"unknown corner kind {kind}")


def _rotate_offset(dr: int, dc: int, kind: str) -> tuple[int, int]:
    turns = {"TL": 0, "TR": 1, "BR": 2, "BL": 3}[kind]
    for _ in range(turns):
        dr, dc = dc, -dr
    return dr, dc


def _edge_metric(grid: list[list[int]], row: int, column: int, dr: int, dc: int, background: int) -> tuple[int, bool]:
    height, width = len(grid), len(grid[0])
    count, saw_zero = 0, False
    for step in range(1, max(height, width) + 1):
        r, c = row + step * dr, column + step * dc
        if not (0 <= r < height and 0 <= c < width):
            break
        value = grid[r][c]
        if value == background:
            break
        count += 1
        saw_zero = saw_zero or value == 0
    return count, saw_zero


def find_corners(grid: list[list[int]], background: int) -> list[tuple[int, int, str]]:
    height, width = len(grid), len(grid[0])
    corners: list[tuple[int, int, str]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == background:
                continue
            for kind in CORNER_KINDS:
                (d1r, d1c), (d2r, d2c) = EDGE_DIRS[kind]
                p1, p2 = (row + d1r, column + d1c), (row + d2r, column + d2c)
                if not (0 <= p1[0] < height and 0 <= p1[1] < width and 0 <= p2[0] < height and 0 <= p2[1] < width):
                    continue
                if grid[p1[0]][p1[1]] == background or grid[p2[0]][p2[1]] == background:
                    continue
                count1, zero1 = _edge_metric(grid, row, column, d1r, d1c, background)
                count2, zero2 = _edge_metric(grid, row, column, d2r, d2c, background)
                if not (count1 >= 3 and count2 >= 3 and zero1 and zero2):
                    continue
                if any(
                    0 <= row + dr < height and 0 <= column + dc < width
                    and grid[row + dr][column + dc] == 0
                    for dr, dc in OUT_DIRS[kind]
                ):
                    continue
                corners.append((row, column, kind))
                break
    return corners


def _colored_around(grid: list[list[int]], corner: tuple[int, int, str], background: int) -> list[tuple[tuple[int, int], int]]:
    row, column, kind = corner
    height, width = len(grid), len(grid[0])
    items: list[tuple[tuple[int, int], int]] = []
    for dr in range(-NEIGHBORHOOD, NEIGHBORHOOD + 1):
        for dc in range(-NEIGHBORHOOD, NEIGHBORHOOD + 1):
            r, c = row + dr, column + dc
            if not (0 <= r < height and 0 <= c < width):
                continue
            value = grid[r][c]
            if value in (background, 0):
                continue
            items.append((_reflect_offset(dr, dc, kind), value))
    return items


def analyze(grid: object, transport: str = "reflect") -> dict[str, object]:
    mode = _transport(transport)
    parsed, height, width, background = _parse_grid(grid)
    corners = find_corners(parsed, background)
    if not corners:
        raise ValueError("no hollow-frame corners were detected")
    around = {corner: _colored_around(parsed, corner, background) for corner in corners}

    sources: list[tuple[int, int, str]] = []
    source_colors: dict[tuple[int, int, str], int] = {}
    for corner, items in around.items():
        outward = [(offset, color) for offset, color in items if offset[0] < 0 or offset[1] < 0]
        if len(outward) < 2 or len({color for _, color in outward}) != 1:
            continue
        color = outward[0][1]
        sprite = frozenset(offset for offset, value in items if value == color)
        if not any(dr == dc and dr > 0 for dr, dc in sprite):
            continue
        sources.append(corner)
        source_colors[corner] = color
    if not sources:
        raise ValueError("at least one complete outward source motif is required")

    canonical: frozenset[tuple[int, int]] | None = None
    for corner in sources:
        color = source_colors[corner]
        sprite = frozenset(offset for offset, value in around[corner] if value == color)
        if canonical is None:
            canonical = sprite
        elif sprite != canonical:
            raise ValueError("all complete source motifs must normalize to the same offsets")
    assert canonical is not None
    diagonal = [dr for dr, dc in canonical if dr == dc and dr > 0]
    if not diagonal:
        raise ValueError("source motif needs an inward diagonal marker offset")
    depth = max(diagonal)
    marker = (depth, depth)

    source_set = set(sources)
    targets: list[dict[str, object]] = []
    for corner in corners:
        if corner in source_set:
            continue
        row, column, kind = corner
        mdr, mdc = _reflect_offset(*marker, kind)
        mr, mc = row + mdr, column + mdc
        if not (0 <= mr < height and 0 <= mc < width):
            continue
        color = parsed[mr][mc]
        if color in (background, 0):
            continue
        hits = [(offset, value) for offset, value in around[corner] if offset in canonical]
        if len(hits) != 1 or hits[0] != (marker, color):
            continue
        targets.append({"row": row, "column": column, "kind": kind, "color": color})
    if not targets:
        raise ValueError("no marker-only target corners were detected")

    output = [row[:] for row in parsed]
    for target in targets:
        for dr, dc in canonical:
            actual = _reflect_offset(dr, dc, target["kind"]) if mode == "reflect" else _rotate_offset(dr, dc, target["kind"])
            r, c = target["row"] + actual[0], target["column"] + actual[1]
            if not (0 <= r < height and 0 <= c < width):
                continue
            current = output[r][c]
            if current not in (background, 0, target["color"]):
                raise ValueError(f"motif paint conflict at {(r, c)}")
            output[r][c] = target["color"]

    return {
        "height": height, "width": width, "background": background,
        "corners": [list(corner) for corner in corners],
        "sources": [list(corner) for corner in sources],
        "source_colors": [source_colors[corner] for corner in sources],
        "canonical_pattern": [list(offset) for offset in sorted(canonical)],
        "marker_offset": list(marker),
        "targets": targets,
        "transport": mode,
        "output": output,
    }


def solve(grid: object, transport: str = "reflect") -> list[list[int]]:
    return deepcopy(analyze(grid, transport)["output"])


def self_check(grid: object, **_: object) -> list[str]:
    try:
        analyze(grid, "reflect")
    except (TypeError, ValueError) as error:
        return [str(error)]
    return []


def _rng(seed: int, label: str) -> random.Random:
    raw = hashlib.sha256(f"4c416de3/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


MOTIFS: tuple[tuple[tuple[int, int], ...], ...] = (
    ((-1, 0), (0, -1), (0, 0), (1, 1), (2, 2), (1, 2)),
    ((-1, -1), (-1, 0), (0, -1), (0, 0), (1, 1), (2, 2), (2, 1)),
    ((-2, 0), (-1, 0), (0, -1), (0, 0), (1, 1), (2, 2), (0, 1)),
    ((-1, 0), (0, -2), (0, -1), (0, 0), (1, 1), (2, 2), (1, 0)),
    ((-2, -1), (-1, -1), (0, -1), (0, 0), (1, 1), (2, 2), (2, 0)),
    ((-1, 0), (0, -1), (1, 0), (1, 1), (2, 2), (2, 1)),
)

# Inclusive rectangles. Profiles 0..5 are teaching candidates; 6..9 are the
# four query sources. Profile 9 has three separated frames on a real 30x30 canvas.
PROFILES: tuple[tuple[int, int, tuple[tuple[int, int, int, int], ...], int], ...] = (
    (16, 16, ((3, 3, 12, 12),), 3),
    (18, 26, ((3, 3, 13, 12), (3, 17, 13, 23)), 5),
    (28, 20, ((3, 3, 12, 13), (18, 3, 25, 13)), 5),
    (22, 28, ((3, 3, 12, 12), (3, 18, 12, 25)), 6),
    (28, 28, ((3, 3, 12, 12), (3, 18, 12, 25), (18, 9, 25, 17)), 7),
    (30, 24, ((3, 3, 12, 13), (18, 3, 27, 13)), 6),
    (17, 19, ((3, 3, 13, 14),), 3),
    (23, 29, ((3, 3, 13, 13), (3, 19, 13, 26)), 6),
    (29, 29, ((2, 2, 10, 10), (2, 18, 10, 26), (18, 9, 26, 17)), 7),
    (30, 30, ((2, 2, 10, 10), (2, 18, 10, 26), (18, 2, 26, 10), (18, 18, 26, 26)), 8),
)


def _corner_records(rectangles: tuple[tuple[int, int, int, int], ...]) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for top, left, bottom, right in rectangles:
        out += [(top, left, "TL"), (top, right, "TR"), (bottom, left, "BL"), (bottom, right, "BR")]
    return out


def _draw_frame(grid: list[list[int]], rect: tuple[int, int, int, int]) -> None:
    top, left, bottom, right = rect
    for column in range(left, right + 1):
        grid[top][column] = 0; grid[bottom][column] = 0
    for row in range(top, bottom + 1):
        grid[row][left] = 0; grid[row][right] = 0


def _scene(seed: int, profile: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed"); _integer(profile, 0, len(PROFILES) - 1, "profile")
    height, width, rectangles, target_count = PROFILES[profile]
    rng = _rng(seed, f"scene-{profile}")
    background = rng.choice(range(1, 10))
    grid = [[background] * width for _ in range(height)]
    for rect in rectangles:
        _draw_frame(grid, rect)

    motif = tuple(MOTIFS[(seed + profile) % len(MOTIFS)])
    marker = max((dr, dc) for dr, dc in motif if dr == dc and dr > 0)
    corners = _corner_records(rectangles)
    source = corners[(seed + 3 * profile) % len(corners)]
    candidates = [corner for corner in corners if corner != source]
    rng.shuffle(candidates)
    # Ensure a transport-sensitive target is present in every pair.
    sensitive = next((corner for corner in candidates if corner[2] in ("TR", "BL")), None)
    targets: list[tuple[int, int, str]] = []
    if sensitive is not None:
        targets.append(sensitive); candidates.remove(sensitive)
    targets += candidates[: max(0, min(target_count, len(corners) - 1) - len(targets))]

    colors = [value for value in range(1, 10) if value != background]
    rng.shuffle(colors)
    source_color = colors[0]
    sr, sc, skind = source
    for dr, dc in motif:
        adr, adc = _reflect_offset(dr, dc, skind)
        r, c = sr + adr, sc + adc
        if not (0 <= r < height and 0 <= c < width):
            raise ValueError("source motif does not fit profile")
        grid[r][c] = source_color
    for index, (row, column, kind) in enumerate(targets):
        color = colors[1 + (index % (len(colors) - 1))]
        dr, dc = _reflect_offset(*marker, kind)
        r, c = row + dr, column + dc
        if not (0 <= r < height and 0 <= c < width):
            raise ValueError("target marker does not fit profile")
        grid[r][c] = color

    findings = self_check(grid)
    if findings:
        raise ValueError(f"generated invalid scene: {findings}")
    if solve(grid, "reflect") == solve(grid, "rotate"):
        raise ValueError("profile failed to distinguish reflection from rotation")
    return grid


def lesson_inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    return ([_scene(seed, i) for i in range(6)], [_scene(seed, i) for i in range(6, 10)])


def generate(seed: int, sample_index: int = 0, *, difficulty: object = None, **overrides: object) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed"); _integer(sample_index, 0, 2**63 - 1, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("unsupported difficulty")
    if overrides:
        raise ValueError("no caller overrides are supported")
    return _scene(seed, sample_index % len(PROFILES))

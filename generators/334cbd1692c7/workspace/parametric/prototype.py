"""Extend an extracted key to rectangle edges, or stamp only its footprint."""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "334cbd1692c7"
VERSION = "extension-mode-v1"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"extension_mode": "to_edges"},
    {"extension_mode": "key_only"},
)
MODES = tuple(setting["extension_mode"] for setting in SETTINGS)

# (height, width, rectangle (height, width) tuples, arm lengths U/D/L/R).
# Every rectangle is strictly larger than the key footprint, so extending the
# four extracted arm colors to the rectangle edges is visibly different from
# stamping the footprint alone.
DEMO_PROFILES = (
    (16, 18, ((7, 9),), (2, 2, 2, 2)),
    (18, 20, ((7, 8), (6, 7)), (3, 2, 2, 3)),
    (20, 22, ((8, 10), (7, 8)), (2, 3, 3, 2)),
    (22, 24, ((9, 10), (7, 9)), (3, 3, 2, 2)),
    (24, 26, ((8, 10), (7, 9), (6, 8)), (2, 3, 2, 3)),
    (26, 28, ((9, 11), (8, 9), (7, 8)), (3, 2, 3, 3)),
)
QUERY_PROFILES = (
    (15, 17, ((7, 8),), (2, 2, 2, 2)),
    (20, 24, ((8, 10), (7, 8)), (3, 2, 2, 3)),
    (26, 28, ((9, 11), (8, 9), (7, 8)), (2, 3, 3, 2)),
    (30, 30, ((9, 11), (8, 9), (7, 8)), (3, 3, 3, 2)),
)


class SceneError(ValueError):
    """Raised when a grid does not encode one unambiguous key/rectangle scene."""


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"extension_mode"}:
        raise ValueError("settings must name exactly extension_mode")
    mode = value["extension_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"extension_mode must be one of {MODES}")
    return {"extension_mode": mode}


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not value
        or len(value) > 30
        or type(value[0]) is not list
        or not value[0]
        or len(value[0]) > 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return deepcopy(value)


def program(settings: Any) -> str:
    mode = _settings(settings)["extension_mode"]
    filename = "canonical.rkt" if mode == "to_edges" else "key_only.rkt"
    return (HERE / filename).read_bytes().decode("utf-8")


def _components_of_color(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    component.add((rr, cc))
                    queue.append((rr, cc))
        components.append(component)
    return components


def _inside(rect: tuple[int, int, int, int], r: int, c: int) -> bool:
    r1, c1, r2, c2 = rect
    return r1 <= r <= r2 and c1 <= c <= c2


def analyze(grid: Any) -> dict[str, Any]:
    """Extract the exact input-dependent intermediate used by both programs."""
    data = _grid(grid)
    h, w = len(data), len(data[0])
    counts = Counter(cell for row in data for cell in row)
    if len(counts) < 3:
        raise SceneError("scene needs background, rectangle, and marker/key colors")
    # Generated scenes make these maxima strict, avoiding dependence on tie order.
    bg, bg_count = counts.most_common(1)[0]
    if list(counts.values()).count(bg_count) != 1:
        raise SceneError("background color must have a strict maximum count")
    non_bg = [(count, color) for color, count in counts.items() if color != bg]
    rect_count, rect_color = max(non_bg)
    if sum(1 for count, _ in non_bg if count == rect_count) != 1:
        raise SceneError("rectangle color must have a strict non-background maximum")

    rectangles: list[tuple[int, int, int, int]] = []
    for component in _components_of_color(data, rect_color):
        if len(component) < 10:
            continue
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        rect = (min(rows), min(cols), max(rows), max(cols))
        r1, c1, r2, c2 = rect
        area = (r2 - r1 + 1) * (c2 - c1 + 1)
        # A legal rectangle is fully filled except for marker cells.
        if len(component) < area - max(1, area // 4):
            raise SceneError("rectangle-color component is not a dense rectangle")
        rectangles.append(rect)
    rectangles.sort()
    if not rectangles:
        raise SceneError("no large rectangle-color object found")
    for index, first in enumerate(rectangles):
        for second in rectangles[index + 1 :]:
            if not (
                first[2] < second[0]
                or second[2] < first[0]
                or first[3] < second[1]
                or second[3] < first[1]
            ):
                raise SceneError("rectangle bounding boxes overlap")

    marker_values: list[int] = []
    for rect in rectangles:
        r1, c1, r2, c2 = rect
        marker_values.extend(
            data[r][c]
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if data[r][c] not in (bg, rect_color)
        )
    if not marker_values:
        raise SceneError("rectangles contain no marker color")
    marker_counts = Counter(marker_values)
    marker_color, marker_count = marker_counts.most_common(1)[0]
    if list(marker_counts.values()).count(marker_count) != 1:
        raise SceneError("marker color is ambiguous inside rectangles")

    markers: list[tuple[int, int, int]] = []
    for rect_index, rect in enumerate(rectangles):
        r1, c1, r2, c2 = rect
        found = [
            (rect_index, r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if data[r][c] == marker_color
        ]
        if not found:
            raise SceneError("every rectangle must contain a marker")
        markers.extend(found)

    def inside_any(r: int, c: int) -> bool:
        return any(_inside(rect, r, c) for rect in rectangles)

    outside_markers = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if data[r][c] == marker_color and not inside_any(r, c)
    ]
    if len(outside_markers) != 1:
        raise SceneError("scene must have exactly one outside key center")
    key_center = outside_markers[0]

    # Mirror the canonical rule's 8-connected non-background region outside all
    # rectangle bboxes. Generated scenes isolate this component from distractions.
    key_cells: set[tuple[int, int]] = {key_center}
    queue = deque([key_center])
    while queue:
        r, c = queue.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if (
                    0 <= rr < h
                    and 0 <= cc < w
                    and (rr, cc) not in key_cells
                    and data[rr][cc] != bg
                    and not inside_any(rr, cc)
                ):
                    key_cells.add((rr, cc))
                    queue.append((rr, cc))

    kr, kc = key_center
    key_offsets = sorted((r - kr, c - kc, data[r][c]) for r, c in key_cells)
    if (0, 0, marker_color) not in key_offsets:
        raise SceneError("key footprint lost its marker-colored center")
    offset_colors = {(dr, dc): color for dr, dc, color in key_offsets}
    required = ((-2, 0), (2, 0), (0, -2), (0, 2))
    if any(offset not in offset_colors for offset in required):
        raise SceneError("key must define all four arm colors two cells from center")
    arm_colors = {
        "up": offset_colors[(-2, 0)],
        "down": offset_colors[(2, 0)],
        "left": offset_colors[(0, -2)],
        "right": offset_colors[(0, 2)],
    }
    if len(set(arm_colors.values())) != 4:
        raise SceneError("the four arm colors must be distinct")
    if marker_color in arm_colors.values() or rect_color in arm_colors.values() or bg in arm_colors.values():
        raise SceneError("marker, rectangle, background, and arm colors must be distinct")
    if any(dr != 0 and dc != 0 for dr, dc, _ in key_offsets):
        raise SceneError("key footprint must be a straight four-arm cross")
    for dr, dc, color in key_offsets:
        if (dr, dc) != (0, 0):
            direction = "up" if dr < 0 else "down" if dr > 0 else "left" if dc < 0 else "right"
            if color != arm_colors[direction]:
                raise SceneError("each key arm must have one consistent color")

    return {
        "height": h,
        "width": w,
        "background": bg,
        "rect_color": rect_color,
        "marker_color": marker_color,
        "rectangles": rectangles,
        "markers": markers,
        "key_center": key_center,
        "key_cells": sorted(key_cells),
        "key_offsets": key_offsets,
        "arm_colors": arm_colors,
    }


def _rotated_color(direction: str, arm_colors: dict[str, int]) -> int:
    # A clockwise color rotation: geometry stays fixed, the extracted
    # input-dependent directional assignments are deliberately wrong.
    source = {"up": "left", "right": "up", "down": "right", "left": "down"}
    return arm_colors[source[direction]]


def _render(grid: Any, settings: Any, *, erase_key: bool, rotate_colors: bool) -> list[list[int]]:
    chosen = _settings(settings)
    mode = chosen["extension_mode"]
    data = _grid(grid)
    facts = analyze(data)
    out = deepcopy(data)
    if erase_key:
        for r, c in facts["key_cells"]:
            out[r][c] = facts["background"]

    arm_colors = facts["arm_colors"]
    for rect_index, mr, mc in facts["markers"]:
        r1, c1, r2, c2 = facts["rectangles"][rect_index]
        if mode == "to_edges":
            directional = {
                "up": _rotated_color("up", arm_colors) if rotate_colors else arm_colors["up"],
                "down": _rotated_color("down", arm_colors) if rotate_colors else arm_colors["down"],
                "left": _rotated_color("left", arm_colors) if rotate_colors else arm_colors["left"],
                "right": _rotated_color("right", arm_colors) if rotate_colors else arm_colors["right"],
            }
            for r in range(r1, mr):
                out[r][mc] = directional["up"]
            for r in range(mr + 1, r2 + 1):
                out[r][mc] = directional["down"]
            for c in range(c1, mc):
                out[mr][c] = directional["left"]
            for c in range(mc + 1, c2 + 1):
                out[mr][c] = directional["right"]
        for dr, dc, color in facts["key_offsets"]:
            rr, cc = mr + dr, mc + dc
            if r1 <= rr <= r2 and c1 <= cc <= c2:
                if rotate_colors and (dr, dc) != (0, 0):
                    direction = "up" if dr < 0 else "down" if dr > 0 else "left" if dc < 0 else "right"
                    color = _rotated_color(direction, arm_colors)
                out[rr][cc] = color
    return out


def transform(grid: Any, settings: Any) -> list[list[int]]:
    return _render(grid, settings, erase_key=True, rotate_colors=False)


def no_key_erase(grid: Any, settings: Any) -> list[list[int]]:
    return _render(grid, settings, erase_key=False, rotate_colors=False)


def rotated_arm_colors(grid: Any, settings: Any) -> list[list[int]]:
    return _render(grid, settings, erase_key=True, rotate_colors=True)


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}:{purpose}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _profile_order(seed: int, split: str):
    profiles = list(DEMO_PROFILES if split == "train" else QUERY_PROFILES)
    _rng(seed, split, 0, "profile-order").shuffle(profiles)
    return profiles


def _expanded(rect: tuple[int, int, int, int], margin: int = 1) -> tuple[int, int, int, int]:
    r1, c1, r2, c2 = rect
    return r1 - margin, c1 - margin, r2 + margin, c2 + margin


def _bbox_disjoint(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> bool:
    return first[2] < second[0] or second[2] < first[0] or first[3] < second[1] or second[3] < first[1]


def _place_profile(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, rect_sizes, arm_lengths = _profile_order(seed, split)[index]
    up_len, down_len, left_len, right_len = arm_lengths
    palette = _rng(seed, split, index, "palette").sample(range(1, 10), 6)
    rect_color, marker_color, up_color, down_color, left_color, right_color = palette

    for restart in range(96):
        local = _rng(seed, split, index, f"placement-{restart}")
        key_centers = [
            (r, c)
            for r in range(up_len, h - down_len)
            for c in range(left_len, w - right_len)
        ]
        local.shuffle(key_centers)
        placed: list[tuple[int, int, int, int]] | None = None
        selected_key: tuple[int, int] | None = None
        for kr, kc in key_centers[: min(len(key_centers), 160)]:
            key_box = _expanded((kr - up_len, kc - left_len, kr + down_len, kc + right_len), 1)
            rectangles: list[tuple[int, int, int, int]] = []
            viable = True
            ordered_sizes = list(rect_sizes)
            # Largest first; randomize equal-area ties without changing profile membership.
            local.shuffle(ordered_sizes)
            ordered_sizes.sort(key=lambda size: size[0] * size[1], reverse=True)
            for rh, rw in ordered_sizes:
                candidates = [
                    (r1, c1, r1 + rh - 1, c1 + rw - 1)
                    for r1 in range(1, h - rh)
                    for c1 in range(1, w - rw)
                ]
                local.shuffle(candidates)
                choice = next(
                    (
                        rect
                        for rect in candidates
                        if _bbox_disjoint(_expanded(rect, 1), key_box)
                        and all(_bbox_disjoint(_expanded(rect, 1), _expanded(other, 1)) for other in rectangles)
                        and rect[0] + up_len <= rect[2] - down_len
                        and rect[1] + left_len <= rect[3] - right_len
                    ),
                    None,
                )
                if choice is None:
                    viable = False
                    break
                rectangles.append(choice)
            if viable:
                placed = rectangles
                selected_key = (kr, kc)
                break
        if placed is None or selected_key is None:
            continue

        grid = [[0] * w for _ in range(h)]
        markers: list[tuple[int, int]] = []
        for rect in sorted(placed):
            r1, c1, r2, c2 = rect
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    grid[r][c] = rect_color
            marker_candidates = [
                (r, c)
                for r in range(r1 + up_len, r2 - down_len + 1)
                for c in range(c1 + left_len, c2 - right_len + 1)
            ]
            local.shuffle(marker_candidates)
            mr, mc = marker_candidates[0]
            grid[mr][mc] = marker_color
            markers.append((mr, mc))

        kr, kc = selected_key
        grid[kr][kc] = marker_color
        for distance in range(1, up_len + 1):
            grid[kr - distance][kc] = up_color
        for distance in range(1, down_len + 1):
            grid[kr + distance][kc] = down_color
        for distance in range(1, left_len + 1):
            grid[kr][kc - distance] = left_color
        for distance in range(1, right_len + 1):
            grid[kr][kc + distance] = right_color

        facts = analyze(grid)
        if len(facts["rectangles"]) != len(rect_sizes) or len(facts["markers"]) != len(rect_sizes):
            continue
        expected_key_size = 1 + sum(arm_lengths)
        if len(facts["key_offsets"]) != expected_key_size:
            continue
        return grid
    raise RuntimeError(f"could not place lawful {h}x{w} key/rectangle profile")


def _pair(grid: list[list[int]], settings: dict[str, str]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    pairs = list(demos)
    survivors = []
    for candidate in SETTINGS:
        try:
            if pairs and all(
                type(pair) is dict and pair.get("output") == transform(pair.get("input"), candidate)
                for pair in pairs
            ):
                survivors.append(dict(candidate))
        except (TypeError, ValueError):
            continue
    return survivors


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    chosen = _settings(settings)
    train = [_pair(_place_profile(seed, "train", index), chosen) for index in range(demos)]
    test = [_pair(_place_profile(seed, "test", index), chosen) for index in range(queries)]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify extension_mode")
    serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(serial) != len(set(serial)):
        raise RuntimeError("episode contains duplicate inputs")
    return {
        "train": train,
        "test": test,
        "settings": chosen,
        "seed": seed,
        "program_solution": program(chosen),
        "certificate": {
            "finite_rivals": [dict(setting) for setting in SETTINGS],
            "survivors": fit_settings(train),
            "racket_checked": False,
            "dependency": "extract the outside key's colored offsets, then stamp/extend them at rectangle markers",
        },
    }

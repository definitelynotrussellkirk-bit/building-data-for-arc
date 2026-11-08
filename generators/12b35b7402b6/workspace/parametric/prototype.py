"""Task-local native parametric family for 12b35b7402b6.

``mode=canonical`` returns the exact selected canonical Racket source.
``mode=linked_payload`` is a real two-stage rule:

A. Count all gray top-row markers and recolor the unique blue component of that
   size red (the canonical transformation).
B. Recompute red 4-connectivity on the intermediate.  The unique largest red
   component's size selects an azure component, which is recolored yellow.

The sampler is setting-neutral.  Every scene contains a pre-A red key, a
post-A key, crossed zero/one-cell diagonal-connectivity controls, and payload
decoys for marker count, rank, position, and fixed-offset shortcuts.  Adapter
generation is Python-only;
qualification independently replays all labels through protected Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys
from typing import Any, Callable, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "12b35b7402b6"
DEFAULT = {"mode": "canonical"}
PARAMETERS = {"mode": ["canonical", "linked_payload"]}
SETTINGS = [{"mode": value} for value in PARAMETERS["mode"]]
CANONICAL_SHA256 = "cb01ed25524c6dfe4c14f9eded34505f7ec8ab9251141290edaacd6a5a1f4e3d"

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes

_DEMO_SHAPES = ((15, 20), (16, 21), (17, 22), (18, 23), (19, 24), (20, 25))
_QUERY_SHAPES = ((15, 20), (19, 24), (24, 28), (30, 30))
_DEMO_PROFILES = ("demo_a", "demo_b", "demo_c", "demo_d", "demo_e", "demo_f")
_QUERY_PROFILES = ("query_a", "query_b", "query_c", "stress")
_ROLES = (
    "cluster",
    "red_decoy",
    "azure_true",
    "azure_skip",
    "azure_diag",
    "azure_extra",
    "blue_span",
    "blue_a",
    "blue_b",
)
_PROFILE_SLOTS = {
    "demo_a": (5, 10, 0, 11, 7, 2, 3, 8, 1),
    "demo_b": (4, 1, 11, 0, 6, 9, 8, 3, 10),
    "demo_c": (6, 2, 4, 9, 0, 11, 7, 1, 10),
    "demo_d": (7, 8, 3, 4, 11, 1, 0, 9, 6),
    "demo_e": (0, 11, 6, 2, 9, 4, 10, 3, 8),
    "demo_f": (1, 9, 5, 10, 2, 8, 11, 4, 7),
    "query_a": (5, 0, 10, 2, 7, 11, 3, 8, 1),
    "query_b": (4, 11, 1, 9, 6, 0, 8, 3, 10),
    "query_c": (6, 3, 8, 0, 11, 2, 7, 1, 10),
    "stress": (5, 2, 11, 0, 7, 6, 8, 3, 10),
}
_PROFILE_GROUP = {
    "demo_a": 0,
    "demo_b": 1,
    "demo_c": 2,
    "demo_d": 0,
    "demo_e": 1,
    "demo_f": 2,
    "query_a": 2,
    "query_b": 0,
    "query_c": 1,
    "stress": 0,
}


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}; bool is forbidden")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"mode"}:
        raise ValueError("settings must name exactly mode")
    mode = value["mode"]
    if type(mode) is not str or mode not in PARAMETERS["mode"]:
        raise ValueError("mode must be 'canonical' or 'linked_payload'")
    return {"mode": mode}


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return value


def _read_rule(name: str) -> str:
    path = HERE / name
    text = path.read_text()
    return text[:-1] if text.endswith("\n") else text


def canonical_source() -> str:
    source = _read_rule("canonical.rkt")
    if hashlib.sha256(source.encode()).hexdigest() != CANONICAL_SHA256:
        raise ValueError("canonical.rkt drifted from selected authority")
    return source


def program(settings: Any) -> str:
    mode = _settings(settings)["mode"]
    return canonical_source() if mode == "canonical" else _read_rule("linked_payload.rkt")


def skip_stage_a_program() -> str:
    return _read_rule("skip_stage_a.rkt")


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    return _digest(_grid(grid))


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|linked-payload-v1|{seed}|{domain}|{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def components(
    grid: list[list[int]], color: int, *, connectivity: int = 4
) -> list[list[tuple[int, int]]]:
    value = _grid(grid)
    if type(color) is not int or not 0 <= color <= 9:
        raise ValueError("color must be an exact ARC integer")
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    neighbors = (
        ((1, 0), (-1, 0), (0, 1), (0, -1))
        if connectivity == 4
        else tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        )
    )
    h, w = len(value), len(value[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if value[r][c] == color}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in neighbors:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        result.append(sorted(cells))
    return sorted(result, key=lambda cells: (cells[0], len(cells)))


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    out = [list(row) for row in _grid(grid)]
    for r, c in cells:
        out[r][c] = color
    return out


def _unique_component_by_size(
    grid: list[list[int]], color: int, size: int, *, connectivity: int = 4
) -> list[tuple[int, int]]:
    matches = [c for c in components(grid, color, connectivity=connectivity) if len(c) == size]
    if len(matches) != 1:
        raise ValueError(f"expected one color-{color} component of size {size}; found {len(matches)}")
    return matches[0]


def _unique_largest(grid: list[list[int]], color: int, *, connectivity: int = 4) -> list[tuple[int, int]]:
    comps = components(grid, color, connectivity=connectivity)
    if not comps:
        raise ValueError(f"no color-{color} components")
    maximum = max(map(len, comps))
    matches = [c for c in comps if len(c) == maximum]
    if len(matches) != 1:
        raise ValueError(f"largest color-{color} component is tied")
    return matches[0]


def _marker_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    value = _grid(grid)
    return [(r, c) for r, row in enumerate(value) for c, cell in enumerate(row) if cell == 5]


def stage_a_grid(grid: list[list[int]]) -> list[list[int]]:
    value = _grid(grid)
    markers = _marker_cells(value)
    if not markers or any(r != 0 for r, _ in markers):
        raise ValueError("all gray markers must be in the top row")
    target = _unique_component_by_size(value, 1, len(markers))
    return _paint(value, target, 2)


def _linked_transform(grid: list[list[int]]) -> list[list[int]]:
    stage = stage_a_grid(grid)
    key = _unique_largest(stage, 2)
    payload = _unique_component_by_size(stage, 8, len(key))
    return _paint(stage, payload, 4)


def skip_stage_a_transform(grid: list[list[int]]) -> list[list[int]]:
    value = _grid(grid)
    key = _unique_largest(value, 2)
    payload = _unique_component_by_size(value, 8, len(key))
    return _paint(value, payload, 4)


def transform(grid: Any, settings: Any) -> list[list[int]]:
    value = _grid(grid)
    mode = _settings(settings)["mode"]
    return stage_a_grid(value) if mode == "canonical" else _linked_transform(value)


def changed_cells(before: Any, after: Any, *, old: int, new: int) -> int:
    a, b = _grid(before), _grid(after)
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError("grids must have equal dimensions")
    return sum(
        a[r][c] == old and b[r][c] == new
        for r in range(len(a))
        for c in range(len(a[0]))
    )


def _slots(height: int, width: int) -> list[tuple[int, int, int, int]]:
    if height < 15 or width < 20:
        raise ValueError("parametric scenes require at least 15x20")
    body_top = 2
    rows, cols = 3, 4
    usable_h = height - body_top - (rows - 1)
    usable_w = width - (cols - 1)
    hs = [usable_h // rows + int(i < usable_h % rows) for i in range(rows)]
    ws = [usable_w // cols + int(i < usable_w % cols) for i in range(cols)]
    r_starts, c_starts = [], []
    cursor = body_top
    for size in hs:
        r_starts.append(cursor)
        cursor += size + 1
    cursor = 0
    for size in ws:
        c_starts.append(cursor)
        cursor += size + 1
    return [
        (r_starts[r], c_starts[c], hs[r], ws[c])
        for r in range(rows)
        for c in range(cols)
    ]


def _offset(shape_h: int, shape_w: int, slot_h: int, slot_w: int, align: str, rng: random.Random) -> tuple[int, int]:
    if align == "tl":
        return 0, 0
    if align == "tr":
        return 0, slot_w - shape_w
    if align == "bl":
        return slot_h - shape_h, 0
    if align == "br":
        return slot_h - shape_h, slot_w - shape_w
    if align == "center":
        return (slot_h - shape_h) // 2, (slot_w - shape_w) // 2
    return rng.randint(0, slot_h - shape_h), rng.randint(0, slot_w - shape_w)


def _snake_shape(size: int, slot_h: int, slot_w: int, rng: random.Random, *, align: str = "random") -> list[tuple[int, int]]:
    widths = [w for w in range(1, slot_w + 1) if math.ceil(size / w) <= slot_h]
    if not widths:
        raise ValueError(f"size {size} does not fit {slot_h}x{slot_w}")
    near = sorted(widths, key=lambda w: (abs(w - math.sqrt(size)), w))
    width = rng.choice(near[: min(3, len(near))])
    height = math.ceil(size / width)
    cells = []
    for r in range(height):
        cols = range(width) if r % 2 == 0 else range(width - 1, -1, -1)
        for c in cols:
            cells.append((r, c))
            if len(cells) == size:
                break
        if len(cells) == size:
            break
    if rng.randrange(2):
        cells = [(height - 1 - r, c) for r, c in cells]
    if rng.randrange(2):
        cells = [(r, width - 1 - c) for r, c in cells]
    dr, dc = _offset(height, width, slot_h, slot_w, align, rng)
    return sorted((dr + r, dc + c) for r, c in cells)


def _local_component_count(cells: Iterable[tuple[int, int]]) -> int:
    unseen = set(cells)
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            r, c = stack.pop()
            for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
    return count


def _cluster_shape(
    marker_count: int,
    anchor_size: int,
    slot_h: int,
    slot_w: int,
    rng: random.Random,
    *,
    satellite_size: int,
    align: str = "random",
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[tuple[int, int]]]:
    """Build a blue bridge between at least two red components.

    Recoloring the blue path is therefore what merges the red fragments.  A
    cheap ``marker_count + largest touching red`` rule is insufficient; the
    intended key is the size of the recomputed post-A component.
    """
    if type(satellite_size) is not int or satellite_size not in (0, 1):
        raise ValueError("satellite_size must be the exact integer 0 or 1")
    total = marker_count + anchor_size
    candidates: list[
        tuple[int, int, list[tuple[int, int]], list[tuple[int, int]]]
    ] = []
    for width in range(2, slot_w):
        height = math.ceil(total / width)
        if height > slot_h - 1:
            continue
        path: list[tuple[int, int]] = []
        for r in range(height):
            cols = range(width) if r % 2 == 0 else range(width - 1, -1, -1)
            for c in cols:
                path.append((r + 1, c + 1))
                if len(path) == total:
                    break
            if len(path) == total:
                break
        for left_anchor_size in range(1, anchor_size):
            target = path[
                left_anchor_size : left_anchor_size + marker_count
            ]
            anchor = (
                path[:left_anchor_size]
                + path[left_anchor_size + marker_count :]
            )
            target_bbox_area = (
                (max(r for r, _ in target) - min(r for r, _ in target) + 1)
                * (max(c for _, c in target) - min(c for _, c in target) + 1)
            )
            if (
                _local_component_count(target) == 1
                and _local_component_count(anchor) >= 2
                and _local_component_count(target + anchor) == 1
                and target_bbox_area != total
            ):
                candidates.append((width, height, target, anchor))
    if not candidates:
        raise ValueError(
            f"bridging cluster of {marker_count}+{anchor_size} does not fit "
            f"{slot_h}x{slot_w}"
        )
    width, height, target, anchor = rng.choice(candidates)
    satellite = [(0, 0)] if satellite_size else []
    bbox_h, bbox_w = height + 1, width + 1
    if rng.randrange(2):
        target = [(bbox_h - 1 - r, c) for r, c in target]
        anchor = [(bbox_h - 1 - r, c) for r, c in anchor]
        satellite = [(bbox_h - 1 - r, c) for r, c in satellite]
    if rng.randrange(2):
        target = [(r, bbox_w - 1 - c) for r, c in target]
        anchor = [(r, bbox_w - 1 - c) for r, c in anchor]
        satellite = [(r, bbox_w - 1 - c) for r, c in satellite]
    dr, dc = _offset(bbox_h, bbox_w, slot_h, slot_w, align, rng)
    move = lambda cells: sorted((dr + r, dc + c) for r, c in cells)
    return move(target), move(anchor), move(satellite)


def _marker_columns(
    rng: random.Random,
    count: int,
    width: int,
    span: int,
    *,
    start: int | None = None,
) -> list[int]:
    if not count < span <= width:
        raise ValueError("marker span must exceed marker count and fit width")
    if start is None:
        start = 0 if span == width else rng.randint(0, width - span)
    elif type(start) is not int or not 0 <= start <= width - span:
        raise ValueError("marker start must fit the requested span")
    if count == 2:
        offsets = [0, span - 1]
    else:
        offsets = [0, span - 1, *rng.sample(range(1, span - 1), count - 2)]
    return sorted(start + value for value in offsets)


def _profile_spec(seed: int, index: int, height: int, width: int, profile: str) -> dict[str, Any]:
    if profile not in _PROFILE_GROUP:
        raise ValueError(f"unknown profile {profile!r}")
    rng = _rng(seed, f"spec:{profile}", index)
    group = _PROFILE_GROUP[profile]
    if profile == "stress":
        marker_count, anchor_size, marker_span = 12, 8, width
        blue_a, blue_b = 5, 15
        azure_extra = marker_count
    else:
        # The smallest supported 4x4 cluster slot has a 3x3 inset capacity.
        # Keep the connected Stage-A key at <=9 cells so every seed is
        # realizable rather than letting random 6+4 draws fail at generation.
        marker_count = 3 + rng.randrange(3)
        anchor_size = 2 + rng.randrange(3)
        # A 4-cell target plus a 2-cell split anchor has only path layouts whose
        # target bounding-box area equals the final merged size.  Avoid that one
        # accidental equivalence so the minimum lesson always refutes the
        # plausible "target bbox area" shortcut.
        if marker_count == 4 and anchor_size == 2:
            anchor_size = 3
        marker_span = marker_count + (3, 5, 4)[group]
        if marker_span > width:
            marker_span = width
        if group == 0:
            blue_a, blue_b = 1, marker_count + 1
            azure_extra = marker_count
        elif group == 1:
            blue_a, blue_b = marker_count + 1, marker_count + 2
            azure_extra = marker_count + anchor_size + 2
        else:
            blue_a, blue_b = 1, 2
            azure_extra = 1
    true_key = marker_count + anchor_size
    # Cross the minimum lesson: demo_a uses a one-cell skip gap while demo_b
    # uses two.  This prevents "largest original red + 1" (or +2) from acting
    # as a universal replacement for recomputing the post-A component.
    skip_delta = 1 if group == 0 else 2 if group == 1 else min(3, marker_count - 1)
    skip_key = true_key - skip_delta
    # Likewise cross 4- versus 8-connectivity.  Group 0 has no diagonal
    # satellite; group 1 has one.  A fixed "8-connected size - 1" correction
    # therefore fails within the promised two demonstrations.
    diagonal_satellite_size = 0 if group == 0 else 1
    diag_payload_size = true_key + 1
    return {
        "marker_count": marker_count,
        "anchor_size": anchor_size,
        "marker_span": marker_span,
        "true_key_size": true_key,
        "skip_key_size": skip_key,
        "diagonal_satellite_size": diagonal_satellite_size,
        "skip_delta": skip_delta,
        "diag_payload_size": diag_payload_size,
        "sizes": {
            "red_decoy": skip_key,
            "azure_true": true_key,
            "azure_skip": skip_key,
            "azure_diag": diag_payload_size,
            "azure_extra": azure_extra,
            "blue_span": marker_span,
            "blue_a": blue_a,
            "blue_b": blue_b,
        },
    }


def _role_alignment(profile: str, role: str) -> str:
    if profile == "stress":
        return {
            "blue_span": "bl",
            "azure_true": "br",
            "azure_skip": "tl",
            "cluster": "center",
        }.get(role, "random")
    return {
        "azure_true": "tl" if profile in ("demo_a", "query_b") else "br",
        "azure_skip": "br" if profile in ("demo_a", "query_b") else "tl",
        "cluster": "center",
    }.get(role, "random")


def build_scene(seed: int, index: int, height: int, width: int, *, profile: str) -> dict[str, Any]:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(index, 0, 10**9, "index")
    _integer(height, 15, 30, "height")
    _integer(width, 20, 30, "width")
    spec = _profile_spec(seed, index, height, width, profile)
    slots = _slots(height, width)
    assignment = dict(zip(_ROLES, _PROFILE_SLOTS[profile]))
    grid = [[0] * width for _ in range(height)]
    marker_rng = _rng(seed, f"markers:{profile}", index)
    marker_start = 0 if profile in ("demo_a", "demo_b") else None
    for c in _marker_columns(
        marker_rng,
        spec["marker_count"],
        width,
        spec["marker_span"],
        start=marker_start,
    ):
        grid[0][c] = 5

    role_cells: dict[str, list[tuple[int, int]]] = {}
    for role in _ROLES:
        slot_index = assignment[role]
        r0, c0, sh, sw = slots[slot_index]
        rng = _rng(seed, f"shape:{profile}:{role}", index)
        align = _role_alignment(profile, role)
        if role == "cluster":
            target, anchor, satellite = _cluster_shape(
                spec["marker_count"],
                spec["anchor_size"],
                sh,
                sw,
                rng,
                satellite_size=spec["diagonal_satellite_size"],
                align=align,
            )
            translated = {
                "blue_target": [(r0 + r, c0 + c) for r, c in target],
                "red_anchor": [(r0 + r, c0 + c) for r, c in anchor],
                "red_satellite": [(r0 + r, c0 + c) for r, c in satellite],
            }
            for name, cells in translated.items():
                role_cells[name] = cells
            for r, c in translated["blue_target"]:
                grid[r][c] = 1
            for name in ("red_anchor", "red_satellite"):
                for r, c in translated[name]:
                    grid[r][c] = 2
            continue
        size = spec["sizes"][role]
        local = _snake_shape(size, sh, sw, rng, align=align)
        cells = [(r0 + r, c0 + c) for r, c in local]
        role_cells[role] = cells
        color = 2 if role == "red_decoy" else 8 if role.startswith("azure_") else 1
        for r, c in cells:
            grid[r][c] = color

    facts = scene_facts(grid)
    expected = {
        "marker_count": spec["marker_count"],
        "marker_span": spec["marker_span"],
        "pre_stage_largest_red_size": spec["skip_key_size"],
        "post_stage_largest_red_size": spec["true_key_size"],
        "post_stage_largest_red8_size": (
            spec["true_key_size"] + spec["diagonal_satellite_size"]
        ),
    }
    for key, value in expected.items():
        if facts.get(key) != value:
            raise RuntimeError(f"scene invariant failed: {key}={facts.get(key)!r}, expected {value!r}")
    if not facts["unique_blue_match"]:
        raise RuntimeError("scene must have one blue marker-count match")
    if (
        len(facts["touching_red_component_sizes"]) < 2
        or sum(facts["touching_red_component_sizes"]) != spec["anchor_size"]
    ):
        raise RuntimeError(
            "Stage A must bridge at least two red components whose total is the anchor size"
        )
    for size in (
        spec["true_key_size"],
        spec["skip_key_size"],
        spec["diag_payload_size"],
    ):
        if facts["azure_sizes"].count(size) != 1:
            raise RuntimeError(f"scene must have one azure component of size {size}")
    return {
        "grid": grid,
        "profile": profile,
        "shape": [height, width],
        **{k: spec[k] for k in (
            "marker_count",
            "marker_span",
            "anchor_size",
            "true_key_size",
            "skip_key_size",
            "diagonal_satellite_size",
            "skip_delta",
            "diag_payload_size",
        )},
        "role_cells": role_cells,
        "input_sha256": grid_sha256(grid),
    }


def scene_facts(grid: Any) -> dict[str, Any]:
    value = _grid(grid)
    markers = _marker_cells(value)
    marker_cols = sorted(c for r, c in markers if r == 0)
    marker_count = len(markers)
    marker_span = max(marker_cols) - min(marker_cols) + 1 if marker_cols else 0
    blue = components(value, 1)
    red_pre = components(value, 2)
    azure = components(value, 8)
    unique_blue = [c for c in blue if len(c) == marker_count]
    touching_red_sizes: list[int] = []
    if len(unique_blue) == 1:
        target_set = set(unique_blue[0])
        touching_red_sizes = sorted(
            len(comp)
            for comp in red_pre
            if any(
                (r + dr, c + dc) in target_set
                for r, c in comp
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
        )
    stage = stage_a_grid(value) if len(unique_blue) == 1 and markers and all(r == 0 for r, _ in markers) else None
    red_post = components(stage, 2) if stage is not None else []
    red8_post = components(stage, 2, connectivity=8) if stage is not None else []
    true_size = max(map(len, red_post), default=0)
    payload_order = sorted(azure, key=lambda c: c[0])
    true_ranks = [i for i, cells in enumerate(payload_order) if len(cells) == true_size]
    target_bbox_area = 0
    if len(unique_blue) == 1:
        rows = [r for r, _ in unique_blue[0]]
        cols = [c for _, c in unique_blue[0]]
        target_bbox_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    return {
        "marker_count": marker_count,
        "marker_span": marker_span,
        "blue_sizes": [len(c) for c in blue],
        "unique_blue_match": len(unique_blue) == 1,
        "pre_stage_largest_red_size": max(map(len, red_pre), default=0),
        "touching_red_component_sizes": touching_red_sizes,
        "post_stage_largest_red_size": true_size,
        "post_stage_largest_red8_size": max(map(len, red8_post), default=0),
        "azure_sizes": [len(c) for c in azure],
        "true_payload_position_rank": true_ranks[0] if len(true_ranks) == 1 else None,
        "target_bbox_area": target_bbox_area,
        "nonzero_count": sum(cell != 0 for row in value for cell in row),
    }


def _recolor_blue_selected(grid: list[list[int]], selector: Callable[[list[list[tuple[int, int]]]], list[tuple[int, int]] | None]) -> list[list[int]]:
    comps = components(grid, 1)
    selected = selector(comps)
    return _paint(grid, selected, 2) if selected else [list(row) for row in grid]


def _recolor_azure_by_size(stage: list[list[int]], size: int) -> list[list[int]]:
    matches = [c for c in components(stage, 8) if len(c) == size]
    return _paint(stage, matches[0], 4) if len(matches) == 1 else [list(row) for row in stage]


def canonical_rivals(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    facts = scene_facts(grid)
    comps = components(grid, 1)
    by_pos = sorted(comps, key=lambda c: c[0])
    return {
        "gray_horizontal_span": _recolor_blue_selected(grid, lambda cs: next((c for c in cs if len(c) == facts["marker_span"]), None)),
        "largest_blue": _recolor_blue_selected(grid, lambda cs: max(cs, key=len)),
        "smallest_blue": _recolor_blue_selected(grid, lambda cs: min(cs, key=len)),
        "top_left_blue": _paint(grid, by_pos[0], 2),
        "bottom_right_blue": _paint(grid, by_pos[-1], 2),
    }


def _bbox_center2(cells: list[tuple[int, int]]) -> tuple[int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows) + max(rows), min(cols) + max(cols)


def _distance2(a: tuple[int, int], b: tuple[int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _azure_by_reference_distance(
    stage: list[list[int]], reference: tuple[int, int], *, farthest: bool
) -> list[list[int]]:
    azure = components(stage, 8)
    ordered = sorted(
        azure,
        key=lambda cells: (
            -_distance2(_bbox_center2(cells), reference)
            if farthest
            else _distance2(_bbox_center2(cells), reference),
            cells[0],
        ),
    )
    return _paint(stage, ordered[0], 4)


def linked_rivals(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    facts = scene_facts(grid)
    stage = stage_a_grid(grid)
    azure = components(stage, 8)
    by_pos = sorted(azure, key=lambda c: c[0])
    by_size_desc = sorted(azure, key=lambda c: (-len(c), c[0]))
    total_red = sum(cell == 2 for row in stage for cell in row)
    marker_reference = _bbox_center2(_marker_cells(grid))
    return {
        "skip_stage_a": skip_stage_a_transform(grid),
        "pre_stage_red_size": _recolor_azure_by_size(stage, facts["pre_stage_largest_red_size"]),
        "pre_stage_red_plus_one": _recolor_azure_by_size(
            stage, facts["pre_stage_largest_red_size"] + 1
        ),
        "pre_stage_red_plus_two": _recolor_azure_by_size(
            stage, facts["pre_stage_largest_red_size"] + 2
        ),
        "marker_plus_largest_touching_red": _recolor_azure_by_size(
            stage,
            facts["marker_count"]
            + max(facts["touching_red_component_sizes"], default=0),
        ),
        "marker_count_payload": _recolor_azure_by_size(stage, facts["marker_count"]),
        "marker_span_payload": _recolor_azure_by_size(stage, facts["marker_span"]),
        "eight_connectivity": _recolor_azure_by_size(stage, facts["post_stage_largest_red8_size"]),
        "eight_connectivity_minus_one": _recolor_azure_by_size(
            stage, facts["post_stage_largest_red8_size"] - 1
        ),
        "target_bbox_area": _recolor_azure_by_size(stage, facts["target_bbox_area"]),
        "global_red_count": _recolor_azure_by_size(stage, total_red),
        "largest_azure": _paint(stage, by_size_desc[0], 4),
        "smallest_azure": _paint(stage, by_size_desc[-1], 4),
        "second_largest_azure": _paint(stage, by_size_desc[1], 4),
        "top_left_azure": _paint(stage, by_pos[0], 4),
        "bottom_right_azure": _paint(stage, by_pos[-1], 4),
        "nearest_marker_bbox_center": _azure_by_reference_distance(
            stage, marker_reference, farthest=False
        ),
        "farthest_marker_bbox_center": _azure_by_reference_distance(
            stage, marker_reference, farthest=True
        ),
    }


def shortcut_outputs(grid: list[list[int]], settings: dict[str, str]) -> dict[str, list[list[int]]]:
    mode = _settings(settings)["mode"]
    return canonical_rivals(grid) if mode == "canonical" else linked_rivals(grid)


def certify(episode: dict[str, Any]) -> dict[str, Any]:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("queries must be exactly four")
    seen = set()
    for pair in train + test:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("pairs must contain exactly input and output")
        grid, output = _grid(pair["input"]), _grid(pair["output"])
        if (len(grid), len(grid[0])) != (len(output), len(output[0])):
            raise ValueError("output dimensions must match input")
        key = grid_sha256(grid)
        if key in seen:
            raise ValueError("all inputs must be distinct")
        seen.add(key)
        if transform(grid, chosen) != output:
            raise ValueError("claim label disagrees with selected Python semantics")

    survivors = [
        setting
        for setting in SETTINGS
        if all(transform(pair["input"], setting) == pair["output"] for pair in train)
    ]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify chosen mode: {survivors}")

    names = sorted(shortcut_outputs(train[0]["input"], chosen))
    refutations = {}
    for name in names:
        refutations[name] = any(
            shortcut_outputs(pair["input"], chosen)[name] != pair["output"]
            for pair in train
        )
    if not all(refutations.values()):
        raise ValueError(f"declared shortcut survives demonstrations: {refutations}")
    return {
        "scope": "two settings plus task-specific semantic shortcuts",
        "survivors": copy.deepcopy(survivors),
        "shortcut_refutations": refutations,
        "query_input_sha256": [grid_sha256(pair["input"]) for pair in test],
    }


def generate(
    seed: int,
    settings: dict[str, str] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    if settings is None:
        settings = _rng(seed, "settings").choice(SETTINGS)
    chosen = _settings(settings)
    train = []
    for index in range(demos):
        h, w = _DEMO_SHAPES[index]
        scene = build_scene(seed, index, h, w, profile=_DEMO_PROFILES[index])
        train.append({"input": scene["grid"], "output": transform(scene["grid"], chosen)})
    test = []
    for slot, ((h, w), profile) in enumerate(zip(_QUERY_SHAPES, _QUERY_PROFILES)):
        scene = build_scene(seed, 10_000 + slot, h, w, profile=profile)
        test.append({"input": scene["grid"], "output": transform(scene["grid"], chosen)})
    episode = {
        "schema": "12b35b7402b6-linked-payload-proposal-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "selection_scope": "once_per_episode",
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


class RacketRunner:
    """One protected Racket process for bounded authoring evidence."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc: Any) -> None:
        self.bridge.close()


def public_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    if type(query_index) is not int or not 0 <= query_index < 4:
        raise ValueError("query_index must be the exact integer 0..3")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must contain demonstrations and four queries")
    return public_challenge_bytes({"train": train, "test": [test[query_index]]})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--mode", choices=PARAMETERS["mode"], default="canonical")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    episode = generate(args.seed, {"mode": args.mode}, args.demos, args.queries)
    result = {
        "status": "prototype_proposed",
        "settings": episode["settings"],
        "counts": {"demos": len(episode["train"]), "queries": len(episode["test"])},
        "certificate": episode["certificate"],
    }
    if args.racket:
        with RacketRunner() as execute:
            for pair in episode["train"] + episode["test"]:
                if execute(episode["program_solution"], pair["input"]) != pair["output"]:
                    raise RuntimeError("protected Racket disagreed with claim label")
            result["racket"] = execute.identity
            result["racket_evaluations"] = len(episode["train"]) + len(episode["test"])
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"episode": episode, "result": result}, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

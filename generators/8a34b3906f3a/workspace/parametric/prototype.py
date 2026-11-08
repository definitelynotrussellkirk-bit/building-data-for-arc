"""Source-bound rotational completion with a genuine completion-driven selector.

``same_color`` is the byte-exact canonical rule. ``contact_payload`` first
constructs that same fourfold-completed red intermediate. Newly completed red
then contacts exactly one isolated colored key; the selected key color chooses a
distant same-color payload (and key) to recolor azure. Inputs are matched across
settings. Protected Racket, not this Python mirror, is the execution authority.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable, Iterable

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
REPO = HERE.parents[3]
TASK_ID = "8a34b3906f3a"

_RUNTIME = REPO / "shared" / "runtime"
if str(_RUNTIME) not in sys.path:
    sys.path.insert(0, str(_RUNTIME))

_BASE_PATH = HOME / "generator.py"
_BASE_SPEC = importlib.util.spec_from_file_location(
    "_base_8a34b3906f3a_for_parametric", _BASE_PATH
)
if _BASE_SPEC is None or _BASE_SPEC.loader is None:
    raise ImportError(_BASE_PATH)
BASE = importlib.util.module_from_spec(_BASE_SPEC)
_BASE_SPEC.loader.exec_module(BASE)

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

DEFAULT = {"completion_style": "same_color"}
PARAMETERS = {"completion_style": ["same_color", "contact_payload"]}
SETTINGS = [{"completion_style": value} for value in PARAMETERS["completion_style"]]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (4, 4)
KEY_COLORS = (3, 4, 5)

_CANONICAL = (HERE / "canonical.rkt").read_text()
_CONTACT_PAYLOAD = (HERE / "contact_payload.rkt").read_text()

# The first two examples deliberately hold size/count fixed while changing the
# completion-selected key color. Later examples expand size, density and border
# contact without changing the episode rule.
_DEMO_PROFILES = (
    {"grid_size": 15, "n_orbits": 4, "n_complete_orbits": 0, "profile": "interior"},
    {"grid_size": 15, "n_orbits": 4, "n_complete_orbits": 1, "profile": "mixed"},
    {"grid_size": 17, "n_orbits": 5, "n_complete_orbits": 0, "profile": "boundary"},
    {"grid_size": 19, "n_orbits": 6, "n_complete_orbits": 1, "profile": "mixed"},
    {"grid_size": 21, "n_orbits": 7, "n_complete_orbits": 2, "profile": "boundary"},
    {"grid_size": 23, "n_orbits": 8, "n_complete_orbits": 0, "profile": "mixed"},
)
_QUERY_PROFILES = (
    {"grid_size": 21, "n_orbits": 8, "n_complete_orbits": 0, "profile": "boundary"},
    {"grid_size": 23, "n_orbits": 9, "n_complete_orbits": 1, "profile": "mixed"},
    {"grid_size": 25, "n_orbits": 10, "n_complete_orbits": 2, "profile": "boundary"},
    # The exact canonical quotient-center program is lawful on this separately
    # constrained 30x30 extension: embed a 29x29 orbit scene at offset (1,1),
    # so all rotations around integer center 15 remain in bounds.
    {"grid_size": 30, "n_orbits": 12, "n_complete_orbits": 1, "profile": "boundary"},
)

_COMMON_RIVALS = ("identity", "first_orbit_only", "mark_added", "key_only")
_COLOR_RIVALS = tuple(f"fixed_color_{color}" for color in KEY_COLORS)
EXTRA_RIVALS = _COMMON_RIVALS + _COLOR_RIVALS
TEACHING_SELECTOR_RIVALS = (
    "first_read",
    "last_read",
    "near_center",
    "far_center",
    "top_payload",
    "left_payload",
    "near_payload",
    "widest_payload",
    "tallest_payload",
    "near_input_red",
    "first_added_only",
    "diagonal_contact",
)

_PAYLOAD_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
)


def _raw(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def digest(value: object) -> str:
    return hashlib.sha256(_raw(value)).hexdigest()


def _integer(value: object, name: str, lo: int, hi: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in {lo}..{hi}")
    return value


def _settings(settings: object, *, seed: int | None = None) -> dict[str, str]:
    if settings is None:
        if seed is None:
            raise ValueError("settings are required")
        return dict(_rng(seed, "settings").choice(SETTINGS))
    if type(settings) is not dict or set(settings) != {"completion_style"}:
        raise ValueError("settings must contain exactly completion_style")
    value = settings["completion_style"]
    if type(value) is not str or value not in PARAMETERS["completion_style"]:
        raise ValueError("completion_style must be same_color or contact_payload")
    return {"completion_style": value}


def _grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings: object) -> str:
    selected = _settings(settings)
    return _CANONICAL if selected == DEFAULT else _CONTACT_PAYLOAD


def _rotate(cell: tuple[int, int], center: int) -> tuple[int, int]:
    r, c = cell
    dr, dc = r - center, c - center
    return center + dc, center - dr


def _orthogonal(cell: tuple[int, int], h: int, w: int) -> list[tuple[int, int]]:
    r, c = cell
    return [
        (rr, cc)
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= rr < h and 0 <= cc < w
    ]


def _red_projection(grid: list[list[int]]) -> list[list[int]]:
    return [[0 if value in KEY_COLORS else value for value in row] for row in grid]


def _complete_unchecked(grid: list[list[int]]) -> list[list[int]]:
    center = len(grid) // 2
    out = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            current = (r, c)
            for _ in range(3):
                current = _rotate(current, center)
                rr, cc = current
                if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
                    raise ValueError("red rotation clips the board")
                out[rr][cc] = 2
    return out


def _added_unchecked(grid: list[list[int]]) -> set[tuple[int, int]]:
    projected = _red_projection(grid)
    completed = _complete_unchecked(projected)
    return {
        (r, c)
        for r, row in enumerate(completed)
        for c, value in enumerate(row)
        if value == 2 and projected[r][c] == 0
    }


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = [start]
        component = []
        while queue:
            cell = queue.pop()
            component.append(cell)
            for neighbor in _orthogonal(cell, h, w):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        result.append(sorted(component))
    return sorted(result, key=lambda cells: (len(cells), cells))


def _red_errors(projected: list[list[int]]) -> list[str]:
    errors: list[str] = []
    h, w = len(projected), len(projected[0])
    if h != w:
        errors.append("red grammar requires a square board")
        return errors
    if h not in tuple(range(13, 30, 2)) + (30,):
        errors.append("red grammar size must be odd 13..29 or constrained 30")
    scene = BASE.analyze_scene(projected)
    if scene["palette"] != [0, 2, 9]:
        errors.append("red projection palette must be exactly [0, 2, 9]")
    if scene["marker_cells"] != [[h // 2, w // 2]]:
        errors.append("red grammar needs one central color-9 marker")
    if not 3 <= scene["orbit_count"] <= 12:
        errors.append("red grammar needs 3..12 rotational orbits")
    if any(row["present_count"] not in (3, 4) for row in scene["orbits"]):
        errors.append("each red orbit must have three or four members")
    if scene["incomplete_orbits"] < 1:
        errors.append("red grammar needs an incomplete orbit")
    if len(scene["missing_quadrants"]) != 1:
        errors.append("all incomplete red orbits must omit one common quadrant")
    if scene["complete_orbits"] > 2:
        errors.append("red grammar admits at most two complete orbits")
    try:
        _complete_unchecked(projected)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def analyze_parametric_scene(grid: object) -> dict[str, Any]:
    source = _grid(grid)
    h, w = len(source), len(source[0])
    palette = sorted({value for row in source for value in row})
    if palette != [0, 2, 3, 4, 5, 9]:
        raise ValueError(f"parametric color grammar must be exactly [0, 2, 3, 4, 5, 9], got {palette}")
    projected = _red_projection(source)
    errors = _red_errors(projected)
    if errors:
        raise ValueError("input differs from the admitted red grammar: " + "; ".join(errors))

    completed_projection = _complete_unchecked(projected)
    added = _added_unchecked(source)
    if not added:
        raise ValueError("completion must add at least one red cell")
    if any(source[r][c] != 0 for r, c in added):
        raise ValueError("auxiliary colors may not occupy a completed red cell")

    key_positions: dict[str, list[int]] = {}
    payload_cells: dict[str, list[list[int]]] = {}
    payload_sizes: dict[str, int] = {}
    color_counts: dict[str, int] = {}
    contact_colors: list[int] = []
    all_aux_contacts: list[tuple[int, tuple[int, int]]] = []
    for color in KEY_COLORS:
        components = _components(source, color)
        sizes = sorted(len(component) for component in components)
        if sizes != [1, 4]:
            raise ValueError(f"color {color} must contain one singleton key and one connected four-cell payload")
        key = next(component[0] for component in components if len(component) == 1)
        payload = next(component for component in components if len(component) == 4)
        contacts = [cell for cell in _orthogonal(key, h, w) if cell in added]
        for cell in payload:
            for neighbor in _orthogonal(cell, h, w):
                if neighbor in added:
                    all_aux_contacts.append((color, cell))
        if contacts:
            contact_colors.append(color)
        key_positions[str(color)] = list(key)
        payload_cells[str(color)] = [list(cell) for cell in payload]
        payload_sizes[str(color)] = len(payload)
        color_counts[str(color)] = sum(value == color for row in source for value in row)

    if all_aux_contacts:
        raise ValueError("only singleton keys, never payload cells, may contact newly completed red")
    if len(contact_colors) != 1:
        raise ValueError(f"exactly one key color must contact newly completed red, got {contact_colors}")
    selected = contact_colors[0]
    selected_key = tuple(key_positions[str(selected)])
    if any(
        projected[neighbor[0]][neighbor[1]] == 2
        for neighbor in _orthogonal(selected_key, h, w)
    ):
        raise ValueError("selected key must be activated by completion, not by original red")

    red_scene = BASE.analyze_scene(projected)
    red_cells = [(r, c) for r, row in enumerate(projected) for c, value in enumerate(row) if value == 2]
    min_edge_distance = min(min(r, c, h - 1 - r, w - 1 - c) for r, c in red_cells)
    return {
        "height": h,
        "width": w,
        "size": h if h == w else None,
        "palette": palette,
        "orbit_count": red_scene["orbit_count"],
        "complete_orbits": red_scene["complete_orbits"],
        "incomplete_orbits": red_scene["incomplete_orbits"],
        "missing_quadrant": red_scene["missing_quadrant"],
        "red_bbox_height": red_scene["red_bbox_height"],
        "red_bbox_width": red_scene["red_bbox_width"],
        "touches_boundary_band": min_edge_distance <= 1,
        "selected_color": selected,
        "selected_key": list(selected_key),
        "selected_key_contacts_added": any(
            neighbor in added for neighbor in _orthogonal(selected_key, h, w)
        ),
        "key_positions": key_positions,
        "payload_cells": payload_cells,
        "payload_sizes": payload_sizes,
        "color_counts": color_counts,
        "added_cells": [list(cell) for cell in sorted(added)],
        "completed_red_sha256": digest(completed_projection),
    }


def _admitted_grid(grid: object) -> list[list[int]]:
    source = _grid(grid)
    analyze_parametric_scene(source)
    return source


def complete_rotation(grid: object) -> list[list[int]]:
    source = _admitted_grid(grid)
    return _complete_unchecked(source)


def added_cells(grid: object) -> set[tuple[int, int]]:
    source = _admitted_grid(grid)
    return _added_unchecked(source)


def transform(grid: object, settings: object) -> list[list[int]]:
    source = _admitted_grid(grid)
    selected = _settings(settings)
    completed = _complete_unchecked(source)
    if selected["completion_style"] == "same_color":
        return completed
    chosen = analyze_parametric_scene(source)["selected_color"]
    return [[8 if value == chosen else value for value in row] for row in completed]


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    payload = f"{TASK_ID}|rotation-contact-payload-v2|{seed}|{domain}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _scene_seed(seed: int, split: str, index: int) -> int:
    return _rng(seed, f"{split}-red-scene", index).randrange(0, 2**63)


def _quadrant_schedule(seed: int, split: str) -> tuple[int, int, int, int]:
    values = [0, 1, 2, 3]
    _rng(seed, f"{split}-quadrants").shuffle(values)
    return tuple(values)


def _color_schedule(seed: int, split: str) -> tuple[int, int, int]:
    values = list(KEY_COLORS)
    _rng(seed, f"{split}-selected-colors").shuffle(values)
    return tuple(values)


def _normalize_shape(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = list(shape)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_orientations(shape: tuple[tuple[int, int], ...]) -> list[tuple[tuple[int, int], ...]]:
    forms = set()
    current = list(shape)
    for _ in range(4):
        forms.add(_normalize_shape(current))
        forms.add(_normalize_shape((r, -c) for r, c in current))
        current = [(c, -r) for r, c in current]
    return sorted(forms)


def _embed_29_in_30(grid: list[list[int]]) -> list[list[int]]:
    if len(grid) != 29 or len(grid[0]) != 29:
        raise ValueError("30x30 extension requires a 29x29 source")
    out = [[0] * 30 for _ in range(30)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            out[r + 1][c + 1] = value
    return out


def _red_scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    if not 0 <= index < len(profiles):
        raise IndexError(index)
    controls = dict(profiles[index])
    requested_size = controls["grid_size"]
    controls["missing_quadrant"] = _quadrant_schedule(seed, split)[index % 4]
    if requested_size == 30:
        controls["grid_size"] = 29
    grid = BASE.generate(
        _scene_seed(seed, split, index),
        1000 + index,
        difficulty=None,
        **controls,
    )
    if requested_size == 30:
        grid = _embed_29_in_30(grid)
    projected = _red_projection(grid)
    errors = _red_errors(projected)
    if errors:
        raise RuntimeError("red sampler returned an invalid scene: " + "; ".join(errors))
    return grid


def _safe_payload_cells(
    source: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    completed_red: set[tuple[int, int]],
    keys: set[tuple[int, int]],
    rng: random.Random,
) -> list[tuple[int, int]] | None:
    h, w = len(source), len(source[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    origins = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(origins)
    for r0, c0 in origins:
        cells = [(r0 + r, c0 + c) for r, c in shape]
        if any(source[r][c] != 0 for r, c in cells):
            continue
        if any(cell in keys for cell in cells):
            continue
        if any(
            neighbor in completed_red
            for cell in cells
            for neighbor in _orthogonal(cell, h, w)
        ):
            continue
        if any(
            neighbor in keys or neighbor in completed_red
            for cell in cells
            for neighbor in _orthogonal(cell, h, w)
        ):
            continue
        return cells
    return None


def _augment_with_keys_and_payloads(
    red_grid: list[list[int]], *, selected_color: int, rng: random.Random
) -> list[list[int]]:
    if selected_color not in KEY_COLORS:
        raise ValueError("selected color must be one of the key colors")
    source = copy.deepcopy(red_grid)
    h, w = len(source), len(source[0])
    projected = _red_projection(source)
    completed = _complete_unchecked(projected)
    original_red = {(r, c) for r in range(h) for c in range(w) if projected[r][c] == 2}
    completed_red = {(r, c) for r in range(h) for c in range(w) if completed[r][c] == 2}
    added = completed_red - original_red

    selected_candidates = []
    for missing in sorted(added):
        for cell in _orthogonal(missing, h, w):
            if source[cell[0]][cell[1]] != 0 or cell in added:
                continue
            if any(neighbor in original_red for neighbor in _orthogonal(cell, h, w)):
                continue
            selected_candidates.append(cell)
    selected_candidates = sorted(set(selected_candidates))
    rng.shuffle(selected_candidates)
    if not selected_candidates:
        raise RuntimeError("no completion-only key position available")
    selected_key = selected_candidates[0]

    decoy_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if source[r][c] == 0
        and (r, c) not in added
        and (r, c) != selected_key
        and all(neighbor not in completed_red for neighbor in _orthogonal((r, c), h, w))
        and abs(r - selected_key[0]) + abs(c - selected_key[1]) > 2
    ]
    rng.shuffle(decoy_candidates)
    if len(decoy_candidates) < 2:
        raise RuntimeError("not enough decoy key positions")

    keys: dict[int, tuple[int, int]] = {selected_color: selected_key}
    decoy_colors = [color for color in KEY_COLORS if color != selected_color]
    chosen_decoys: list[tuple[int, int]] = []
    for color in decoy_colors:
        candidate = next(
            (
                cell
                for cell in decoy_candidates
                if cell not in chosen_decoys
                and all(abs(cell[0] - other[0]) + abs(cell[1] - other[1]) > 1 for other in chosen_decoys + [selected_key])
            ),
            None,
        )
        if candidate is None:
            raise RuntimeError("could not separate decoy keys")
        keys[color] = candidate
        chosen_decoys.append(candidate)

    for color, (r, c) in keys.items():
        source[r][c] = color

    shapes = list(_PAYLOAD_SHAPES)
    rng.shuffle(shapes)
    colors = list(KEY_COLORS)
    rng.shuffle(colors)
    key_set = set(keys.values())
    for color, base_shape in zip(colors, shapes[: len(colors)], strict=True):
        orientations = _shape_orientations(base_shape)
        rng.shuffle(orientations)
        placed = None
        for shape in orientations:
            placed = _safe_payload_cells(source, shape, completed_red, key_set, rng)
            if placed is not None:
                break
        if placed is None:
            raise RuntimeError(f"could not place payload for color {color}")
        for r, c in placed:
            source[r][c] = color

    analyze_parametric_scene(source)
    return source


def _scene(seed: int, split: str, index: int, attempt: int = 0) -> list[list[int]]:
    red = _red_scene(seed, split, index)
    selected = _color_schedule(seed, split)[index % len(KEY_COLORS)]
    return _augment_with_keys_and_payloads(
        red,
        selected_color=selected,
        rng=_rng(seed, f"{split}-aux-attempt-{attempt}", index),
    )


def _selector_choice(name: str, source: list[list[int]]) -> int | None:
    scene = analyze_parametric_scene(source)
    keys = {int(color): tuple(cell) for color, cell in scene["key_positions"].items()}
    payloads = {
        int(color): [tuple(cell) for cell in cells]
        for color, cells in scene["payload_cells"].items()
    }
    center = len(source) // 2
    if name == "first_read":
        return min(keys, key=lambda color: (keys[color], color))
    if name == "last_read":
        return max(keys, key=lambda color: (keys[color], -color))
    if name == "near_center":
        return min(
            keys,
            key=lambda color: (
                abs(keys[color][0] - center) + abs(keys[color][1] - center),
                color,
            ),
        )
    if name == "far_center":
        return max(
            keys,
            key=lambda color: (
                abs(keys[color][0] - center) + abs(keys[color][1] - center),
                -color,
            ),
        )
    if name == "top_payload":
        return min(payloads, key=lambda color: (min(r for r, _ in payloads[color]), color))
    if name == "left_payload":
        return min(payloads, key=lambda color: (min(c for _, c in payloads[color]), color))
    if name == "near_payload":
        return min(
            payloads,
            key=lambda color: (
                min(abs(r - center) + abs(c - center) for r, c in payloads[color]),
                color,
            ),
        )
    if name == "widest_payload":
        return max(
            payloads,
            key=lambda color: (
                max(c for _, c in payloads[color]) - min(c for _, c in payloads[color]) + 1,
                -color,
            ),
        )
    if name == "tallest_payload":
        return max(
            payloads,
            key=lambda color: (
                max(r for r, _ in payloads[color]) - min(r for r, _ in payloads[color]) + 1,
                -color,
            ),
        )
    if name == "near_input_red":
        projected = _red_projection(source)
        red = [(r, c) for r, row in enumerate(projected) for c, value in enumerate(row) if value == 2]
        return min(
            keys,
            key=lambda color: (
                min(abs(keys[color][0] - r) + abs(keys[color][1] - c) for r, c in red),
                color,
            ),
        )
    added = [tuple(cell) for cell in scene["added_cells"]]
    if name == "first_added_only":
        first = min(added)
        for r, c in sorted(_orthogonal(first, len(source), len(source[0]))):
            if source[r][c] in KEY_COLORS:
                return source[r][c]
        return None
    if name == "diagonal_contact":
        for r, c in sorted(added):
            for rr, cc in sorted(((r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1))):
                if 0 <= rr < len(source) and 0 <= cc < len(source[0]) and source[rr][cc] in KEY_COLORS:
                    return source[rr][cc]
        return None
    raise KeyError(name)


def _selector_output(name: str, source: list[list[int]]) -> list[list[int]]:
    completed = _complete_unchecked(source)
    selected = _selector_choice(name, source)
    if selected is None:
        return completed
    return [[8 if value == selected else value for value in row] for row in completed]


def _teaching_inputs(seed: int, demos: int) -> list[list[list[int]]]:
    # Search only the two-example teaching prefix. The red scenes and selected
    # colors are fixed; bounded auxiliary layouts are chosen constructively so
    # no declared position/rank/motif/partial-contact selector fits both demos.
    candidate_count = 12
    first = [_scene(seed, "demo", 0, attempt) for attempt in range(candidate_count)]
    second = [_scene(seed, "demo", 1, attempt) for attempt in range(candidate_count)]
    chosen = None
    for left in first:
        left_selected = analyze_parametric_scene(left)["selected_color"]
        for right in second:
            right_selected = analyze_parametric_scene(right)["selected_color"]
            survivors = [
                name
                for name in TEACHING_SELECTOR_RIVALS
                if _selector_choice(name, left) == left_selected
                and _selector_choice(name, right) == right_selected
            ]
            if not survivors:
                chosen = [left, right]
                break
        if chosen is not None:
            break
    if chosen is None:
        raise RuntimeError("bounded teaching-layout search could not refute declared selector rivals")
    chosen.extend(_scene(seed, "demo", index, 0) for index in range(2, demos))
    return chosen


def _paint_added(source: list[list[int]], color: int) -> list[list[int]]:
    out = _complete_unchecked(source)
    for r, c in _added_unchecked(source):
        out[r][c] = color
    return out


def _first_orbit_only(source: list[list[int]]) -> list[list[int]]:
    projected = _red_projection(source)
    scene = BASE.analyze_scene(projected)
    out = copy.deepcopy(source)
    missing = next(
        (tuple(row["missing"]) for row in scene["orbits"] if row["present_count"] == 3),
        None,
    )
    if missing is not None:
        out[missing[0]][missing[1]] = 2
    return out


def _rival_output(name: str, grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    source = _admitted_grid(grid)
    if name == "identity":
        return copy.deepcopy(source)
    if name == "first_orbit_only":
        return _first_orbit_only(source)
    if name == "mark_added":
        return _paint_added(source, 8)
    scene = analyze_parametric_scene(source)
    completed = _complete_unchecked(source)
    if name == "key_only":
        out = copy.deepcopy(completed)
        r, c = scene["selected_key"]
        out[r][c] = 8
        return out
    if name.startswith("fixed_color_"):
        color = int(name.rsplit("_", 1)[1])
        return [[8 if value == color else value for value in row] for row in completed]
    raise KeyError(name)


def certify(
    episode: object,
    *,
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    selected = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(selected):
        raise ValueError("private program does not match selected settings")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not DEMO_LIMITS[0] <= len(train) <= DEMO_LIMITS[1]:
        raise ValueError("demos must contain 2..6 pairs")
    if type(test) is not list or len(test) != 4:
        raise ValueError("queries must contain exactly four pairs")

    normalized: list[tuple[list[list[int]], list[list[int]]]] = []
    for split, collection in (("train", train), ("test", test)):
        for index, pair in enumerate(collection):
            if type(pair) is not dict or set(pair) != {"input", "output"}:
                raise ValueError(f"malformed {split} pair {index}")
            inp = _admitted_grid(pair["input"])
            out = _grid(pair["output"])
            normalized.append((inp, out))
    hashes = [digest(inp) for inp, _ in normalized]
    if len(hashes) != len(set(hashes)):
        raise ValueError("all demonstration and query inputs must be distinct")

    def predict(candidate: dict[str, str], grid: list[list[int]]) -> list[list[int]]:
        if execute is None:
            return transform(grid, candidate)
        return _grid(execute(program(candidate), grid))

    for split, collection in (("train", train), ("test", test)):
        for index, pair in enumerate(collection):
            if predict(selected, pair["input"]) != pair["output"]:
                raise ValueError(f"label mismatch in {split} pair {index}")

    refutations = []
    survivors = []
    for candidate in SETTINGS:
        disagree = [
            index
            for index, pair in enumerate(train)
            if predict(candidate, pair["input"]) != pair["output"]
        ]
        refutations.append({"settings": dict(candidate), "disagreeing_demo_indices": disagree})
        if not disagree:
            survivors.append(dict(candidate))
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify selected settings: {survivors}")

    extra = {}
    for name in EXTRA_RIVALS:
        disagree = [
            index
            for index, pair in enumerate(train)
            if _rival_output(name, pair["input"], selected) != pair["output"]
        ]
        if not disagree:
            raise ValueError(f"shortcut {name!r} survives every demonstration")
        extra[name] = disagree

    selector_refutations = {}
    if selected["completion_style"] == "contact_payload":
        for name in TEACHING_SELECTOR_RIVALS:
            disagree = [
                index
                for index, pair in enumerate(train)
                if _selector_output(name, pair["input"]) != pair["output"]
            ]
            if not disagree:
                raise ValueError(f"selector shortcut {name!r} survives every demonstration")
            selector_refutations[name] = disagree

    return {
        "scope": "two declared styles plus identity, partial-completion, cosmetic-marking, key-only and fixed-color rivals",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": refutations,
        "extra_refutations": extra,
        "selector_refutations": selector_refutations,
        "selected_colors": [analyze_parametric_scene(pair["input"])["selected_color"] for pair in train],
        "queries": [
            {
                "index": index,
                "input_sha256": digest(pair["input"]),
                "output_sha256": digest(pair["output"]),
                "unanimous": True,
            }
            for index, pair in enumerate(test)
        ],
    }


def generate(
    seed: int,
    settings: object = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, "seed", -(2**63), 2**63 - 1)
    _integer(demos, "demos", *DEMO_LIMITS)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    selected = _settings(settings, seed=seed)
    train_inputs = _teaching_inputs(seed, demos)
    test_inputs = [_scene(seed, "query", index, 0) for index in range(4)]
    inputs = train_inputs + test_inputs
    hashes = [digest(grid) for grid in inputs]
    if len(hashes) != len(set(hashes)):
        raise ValueError("episode inputs must be distinct")
    episode = {
        "schema": f"{TASK_ID}-parametric-rotation-contact-v2",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": [
            {"input": grid, "output": transform(grid, selected)} for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": transform(grid, selected)} for grid in test_inputs
        ],
        "program_solution": program(selected),
        "program_sha256": hashlib.sha256(program(selected).encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: object, index: int) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    _integer(index, "query index", 0, 3)
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must retain four controller-side queries")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


def _datum(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_rule(source: str, grid: list[list[int]], *, bridge=None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge

    own = bridge is None
    bridge = RacketBridge(timeout=60) if own else bridge
    try:
        return _grid(bridge.eval_text(f"({wrap_rule(source)} {_datum(_admitted_grid(grid))})"))
    finally:
        if own:
            bridge.close()


class RacketRunner:
    """One protected Racket process for bounded authoring evidence."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=60)
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        return execute_rule(source, grid, bridge=self.bridge)

    def __exit__(self, exc_type, exc, tb):
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "adversarial_probe.py",
        HERE / "canonical.rkt",
        HERE / "contact_payload.rkt",
        HOME / "generator.py",
    ]
    return {
        path.relative_to(REPO).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
        if path.is_file()
    }


def write_evidence(episodes: list[dict[str, Any]], destination: Path) -> dict[str, Any]:
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    public = destination / "public"
    public.mkdir()
    private_rows = []
    seen = set()
    with RacketRunner() as runner:
        for episode in episodes:
            certificate = certify(episode, execute=runner)
            view = public_turn(episode, 0)
            public_id = public_challenge_id(view)
            if public_id in seen:
                raise ValueError(f"duplicate public first-turn challenge {public_id}")
            seen.add(public_id)
            (public / f"{public_id}.json").write_bytes(public_challenge_bytes(view))
            private_rows.append(
                {
                    "public_id": public_id,
                    "seed": episode["seed"],
                    "settings": episode["settings"],
                    "program_solution": episode["program_solution"],
                    "program_sha256": episode["program_sha256"],
                    "query_outputs": [pair["output"] for pair in episode["test"]],
                    "query_input_sha256": [digest(pair["input"]) for pair in episode["test"]],
                    "selected_colors": [
                        analyze_parametric_scene(pair["input"])["selected_color"]
                        for pair in episode["train"] + episode["test"]
                    ],
                    "certificate": certificate,
                }
            )
        runtime = runner.identity
    private = {
        "schema": f"{TASK_ID}-parametric-authoring-evidence-v2",
        "task_id": TASK_ID,
        "episodes": private_rows,
        "racket": runtime,
        "source_hashes": source_hashes(),
        "limits": (
            "Finite seeds/settings and declared rivals only. The 30x30 case is a separately "
            "constrained quotient-center extension, not a broadening of the repaired odd-square base."
        ),
    }
    (destination / "private.json").write_bytes(_raw(private))
    manifest = {
        "schema": "arcpuzzles-parametric-prototype-export-v1",
        "task_id": TASK_ID,
        "episode_count": len(private_rows),
        "public_ids": sorted(seen),
        "files": {
            path.relative_to(destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(destination.rglob("*"))
            if path.is_file()
        },
    }
    (destination / "manifest.json").write_bytes(_raw(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="append", type=int, default=[])
    parser.add_argument("--completion-style", choices=PARAMETERS["completion_style"])
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    selected = SETTINGS if args.all_settings else [
        {"completion_style": args.completion_style or DEFAULT["completion_style"]}
    ]
    episodes = [
        generate(seed, setting, args.demos, args.queries)
        for setting in selected
        for seed in (args.seed or [0])
    ]
    manifest = write_evidence(episodes, args.out)
    print(json.dumps({"out": str(args.out), "episodes": len(episodes), "manifest": manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

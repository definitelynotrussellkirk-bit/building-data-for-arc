"""Native adapter for the frame-and-marker orientation family."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("orientation.py")
_SPEC = importlib.util.spec_from_file_location(
    "_cf5ccd73cfe5_orientation_" + hashlib.sha256(str(_PATH).encode()).hexdigest(),
    _PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load orientation prototype from {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _orientation(settings):
    if not isinstance(settings, dict) or set(settings) != {"orientation"}:
        raise ValueError("settings must contain exactly orientation")
    value = settings["orientation"]
    if value not in _PROTOTYPE.SETTINGS:
        raise ValueError(f"unsupported orientation: {value!r}")
    return value


def program(settings):
    return _PROTOTYPE.program(_orientation(settings))

_GENERATOR = _PROTOTYPE.generator()


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _transform(grid, orientation):
    facts, errors = _GENERATOR._analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    r0, c0, _r1, _c1 = facts["marker_bbox"]
    cells = {
        (r - r0, c - c0)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == facts["marker_color"]
    }
    if orientation in ("flip_ud", "rot180"):
        cells = {(facts["marker_h"] - 1 - r, c) for r, c in cells}
    if orientation in ("flip_lr", "rot180"):
        cells = {(r, facts["marker_w"] - 1 - c) for r, c in cells}
    return _GENERATOR._render_pattern(
        cells,
        facts["marker_h"],
        facts["marker_w"],
        facts["frame_h"] - 2,
        facts["frame_w"] - 2,
        facts["frame_color"],
        facts["marker_color"],
    )


def _all_outputs(grid):
    return {setting: _transform(grid, setting) for setting in _PROTOTYPE.SETTINGS}


def _accepted_generated(seed, count, *, start, forbidden=()):
    accepted = []
    seen = set(forbidden)
    for index in range(start, start + 1024):
        grid = _GENERATOR.generate(seed, index)
        key = _PROTOTYPE.encoded(grid)
        if key in seen:
            continue
        outputs = _all_outputs(grid)
        if len({_PROTOTYPE.encoded(value) for value in outputs.values()}) != len(_PROTOTYPE.SETTINGS):
            continue
        seen.add(key)
        accepted.append((grid, outputs))
        if len(accepted) == count:
            return accepted
    raise RuntimeError("bounded orientation sampler exhausted; no partial episode emitted")


def _teaching_generated(seed, demos):
    pool = _accepted_generated(seed, 24, start=0)
    rivals = tuple(_GENERATOR.CANONICAL_SHORTCUTS.values())

    def refutes_declared_shortcuts(items):
        return all(
            any(rival(grid) != outputs[setting] for grid, outputs in items)
            for setting in _PROTOTYPE.SETTINGS
            for rival in rivals
        )

    chosen = None
    for size in range(1, min(3, demos) + 1):
        for indices in itertools.combinations(range(len(pool)), size):
            items = [pool[index] for index in indices]
            if refutes_declared_shortcuts(items):
                chosen = list(indices)
                break
        if chosen is not None:
            break
    if chosen is None:
        raise RuntimeError("no bounded demonstration set refutes declared shortcuts")
    chosen_set = set(chosen)
    chosen.extend(index for index in range(len(pool)) if index not in chosen_set)
    return [pool[index] for index in chosen[:demos]]


def _large_scene(seed, slot):
    profiles = (
        # Exact 30x30: frame reaches left/bottom, marker reaches top/right.
        (30, 30, 4, 0, 26, 26, 0, 27),
        # Wide stress: frame reaches top/right, marker reaches bottom/left.
        (29, 30, 0, 4, 23, 26, 26, 0),
        # Tall stress: frame reaches left/bottom, marker reaches top/right.
        (30, 29, 4, 0, 26, 23, 0, 26),
    )
    patterns = (
        ((0, 0), (0, 1), (1, 0), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 2), (2, 0)),
    )
    palettes = ((2, 8), (5, 3), (7, 1), (4, 6))
    if type(slot) is not int or not 0 <= slot < len(profiles):
        raise ValueError("large-scene slot outside supported range")
    h, w, fr, fc, fh, fw, mr, mc = profiles[slot]
    frame_color, marker_color = palettes[(seed + slot) % len(palettes)]
    grid = [[0] * w for _ in range(h)]
    for c in range(fc, fc + fw):
        grid[fr][c] = frame_color
        grid[fr + fh - 1][c] = frame_color
    for r in range(fr, fr + fh):
        grid[r][fc] = frame_color
        grid[r][fc + fw - 1] = frame_color
    for dr, dc in patterns[(seed + slot) % len(patterns)]:
        grid[mr + dr][mc + dc] = marker_color
    errors = _GENERATOR.self_check(grid)
    if errors:
        raise RuntimeError("invalid parametric stress scene: " + "; ".join(errors))
    outputs = _all_outputs(grid)
    if len({_PROTOTYPE.encoded(value) for value in outputs.values()}) != len(_PROTOTYPE.SETTINGS):
        raise RuntimeError("parametric stress scene does not distinguish every orientation")
    return grid, outputs


def generate(seed, settings, demos, queries):
    orientation = _orientation(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")

    teaching = _teaching_generated(seed, demos)
    seen = {_PROTOTYPE.encoded(grid) for grid, _outputs in teaching}
    ordinary_query = _accepted_generated(seed, 1, start=4096, forbidden=seen)[0]
    query_pool = [ordinary_query, *(_large_scene(seed, slot) for slot in range(3))]
    selected = [*teaching, *query_pool[:queries]]
    if len({_PROTOTYPE.encoded(grid) for grid, _outputs in selected}) != len(selected):
        raise RuntimeError("demonstration/query input collision; no partial episode emitted")

    pairs = [
        {"input": grid, "output": outputs[orientation]}
        for grid, outputs in selected
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program({"orientation": orientation}),
    }

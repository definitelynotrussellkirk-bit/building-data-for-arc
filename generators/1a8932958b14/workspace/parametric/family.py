"""Source-bound native parametric family for task ``1a8932958b14``.

The canonical setting moves the payload by the red-to-green marker vector.  The
alternative setting adds a genuine two-step dependency:

1. classify the payload bounding box as wider or taller;
2. use that intermediate to choose the marker-vector multiplier, then translate
   the payload (wide -> +2, tall -> -1).

The same deterministic inputs are used for both settings.  Every generated input
keeps the -1, +1 and +2 marker-vector translations in bounds, so all declared
rules and finite rivals are total over the admitted family grammar.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


TASK_ID = "1a8932958b14"
FAMILY_VERSION = "2.0.0"
PARAMETER_NAME = "translation_policy"
SETTINGS = ("marker_vector", "payload_axis_gate")
DEFAULT_SETTINGS = {PARAMETER_NAME: "marker_vector"}
_CANONICAL_SHA256 = "aa6d40d026b329b0b5f7a9aa1e89644629386b057e095d94ab2e5e33db2d9777"
_COLORS = (1, 4, 5, 6, 7, 8, 9)
_CANDIDATE_MULTIPLIERS = (-1, 1, 2)


@dataclass(frozen=True)
class _Profile:
    height: int
    width: int
    shape_height: int
    shape_width: int
    delta: tuple[int, int]
    boundary_contact: bool = False

    @property
    def axis(self) -> str:
        if self.shape_width == self.shape_height:
            raise ValueError("parametric payloads must not have square bounding boxes")
        return "wide" if self.shape_width > self.shape_height else "tall"


# The first two demonstrations are deliberately paired: same 14x14 field,
# marker vector, palette cardinality and density, but transposed payload axes.
# This makes the axis intermediate visible without relying on a correlated cue.
_DEMO_PROFILES = (
    _Profile(14, 14, 4, 8, (2, 1)),
    _Profile(14, 14, 8, 4, (2, 1)),
    _Profile(16, 17, 5, 9, (-2, 1)),
    _Profile(17, 16, 9, 5, (-2, 1)),
    _Profile(18, 20, 6, 11, (0, 2)),
    _Profile(20, 18, 11, 6, (2, 0)),
)

_QUERY_PROFILES = (
    _Profile(18, 22, 6, 11, (2, 1)),
    _Profile(22, 18, 11, 6, (-2, 1)),
    _Profile(26, 30, 8, 16, (0, -2), boundary_contact=True),
    _Profile(30, 30, 18, 10, (0, 2), boundary_contact=True),
)


_AXIS_GATE_PROGRAM = """(rule!
  ;; Alternative: payload-axis classification controls the marker-vector step.
  (let* ((src (first (find-color g 2)))
         (dst (first (find-color g 3)))
         (base-dr (- (first dst) (first src)))
         (base-dc (- (second dst) (second src)))
         (payload
           (filter (lambda (cell)
                     (let ((v (third cell)))
                       (and (not (= v 0)) (not (= v 2)) (not (= v 3)))))
                   (grid-cells g)))
         (points (map (lambda (cell) (list (first cell) (second cell))) payload))
         (bb (bbox-of-cells points))
         (payload-height (+ 1 (- (third bb) (first bb))))
         (payload-width (+ 1 (- (fourth bb) (second bb))))
         (multiplier (if (> payload-width payload-height) 2 -1))
         (dr (* multiplier base-dr))
         (dc (* multiplier base-dc)))
    (foldl (lambda (cell out)
             (let* ((r (first cell)) (c (second cell)) (v (third cell))
                    (nr (+ r dr)) (nc (+ c dc)))
               (if (and (not (= v 0)) (not (= v 2)) (not (= v 3))
                        (in-bounds? nr nc (rows g) (cols g)))
                   (set-cell out nr nc v)
                   out)))
           (empty-grid (rows g) (cols g) 0)
           payload)))"""


def forced_axis_program(axis: str) -> str:
    """Racket witness that forces the axis intermediate to one value.

    This is not a declared family setting.  It exists only for protected-Racket
    causal evidence showing that a wrong Step-A result changes Step B and output.
    """
    if axis not in ("wide", "tall"):
        raise ValueError("axis must be 'wide' or 'tall'")
    multiplier = 2 if axis == "wide" else -1
    return _AXIS_GATE_PROGRAM.replace(
        "(multiplier (if (> payload-width payload-height) 2 -1))",
        f"(multiplier {multiplier})",
    ).replace(
        ";; Alternative: payload-axis classification controls the marker-vector step.",
        f";; Causal witness: force the payload-axis intermediate to {axis}.",
    )


def _canonical_program() -> str:
    path = Path(__file__).with_name("canonical.rkt")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != _CANONICAL_SHA256:
        raise ValueError(
            f"canonical.rkt source drift: expected {_CANONICAL_SHA256}, got {digest}"
        )
    return data.decode("utf-8")


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must name exactly {PARAMETER_NAME!r}")
    selected = settings[PARAMETER_NAME]
    if type(selected) is not str or selected not in SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {SETTINGS}")
    return selected


def program(settings: dict[str, Any]) -> str:
    selected = _validate_settings(settings)
    return _canonical_program() if selected == "marker_vector" else _AXIS_GATE_PROGRAM


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed: int, split: str, index: int) -> random.Random:
    token = f"{TASK_ID}:{FAMILY_VERSION}:{seed}:{split}:{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(token).digest()[:16], "big"))


def _shape_cells(profile: _Profile, rng: random.Random) -> tuple[tuple[int, int], ...]:
    """Dense connected rectangle with sparse nonadjacent interior holes."""
    sh, sw = profile.shape_height, profile.shape_width
    row_phase = rng.randrange(3)
    col_phase = rng.randrange(3)
    cells = {
        (row, col)
        for row in range(sh)
        for col in range(sw)
        if not (
            0 < row < sh - 1
            and 0 < col < sw - 1
            and row % 3 == row_phase
            and col % 3 == col_phase
        )
    }
    if len(cells) == sh * sw:
        # Small shapes can miss the selected residue pair.  Remove one interior
        # cell while retaining the full border and hence 4-connectivity.
        cells.remove((sh // 2, sw // 2))
    return tuple(sorted(cells))


def _placement_bounds(size: int, span: int, delta: int) -> tuple[int, int]:
    shifts = [multiplier * delta for multiplier in _CANDIDATE_MULTIPLIERS]
    low = max(0, -min(shifts))
    high = min(size - span, size - span - max(shifts))
    if low > high:
        raise ValueError("profile cannot keep all candidate translations in bounds")
    return low, high


def _choose_origin(profile: _Profile, rng: random.Random) -> tuple[int, int]:
    top_low, top_high = _placement_bounds(
        profile.height, profile.shape_height, profile.delta[0]
    )
    left_low, left_high = _placement_bounds(
        profile.width, profile.shape_width, profile.delta[1]
    )
    if profile.boundary_contact:
        # Query stress cases use a horizontal marker vector, so touching the top
        # boundary remains lawful under every candidate translation.
        top = 0 if top_low == 0 else top_low
    else:
        top = rng.randint(top_low, top_high)
    left = rng.randint(left_low, left_high)
    return top, left


def _marker_options(
    profile: _Profile,
    payload: set[tuple[int, int]],
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    dr, dc = profile.delta
    blocked = set(payload)
    for multiplier in _CANDIDATE_MULTIPLIERS:
        blocked.update(
            (row + multiplier * dr, col + multiplier * dc)
            for row, col in payload
        )
    options = []
    for row in range(profile.height):
        for col in range(profile.width):
            destination = (row + dr, col + dc)
            if not (0 <= destination[0] < profile.height and 0 <= destination[1] < profile.width):
                continue
            if (row, col) in blocked or destination in blocked:
                continue
            options.append(((row, col), destination))
    return options


def _build_input(seed: int, split: str, index: int, profile: _Profile) -> list[list[int]]:
    rng = _rng(seed, split, index)
    shape = _shape_cells(profile, rng)
    top, left = _choose_origin(profile, rng)
    payload = {(top + row, left + col) for row, col in shape}
    markers = _marker_options(profile, payload)
    if not markers:
        raise RuntimeError("profile has no marker placement outside payload/output footprints")
    source, destination = rng.choice(markers)

    palette = rng.sample(_COLORS, 4)
    color_phase = rng.randrange(len(palette))
    grid = [[0 for _ in range(profile.width)] for _ in range(profile.height)]
    for row, col in sorted(payload):
        grid[row][col] = palette[(3 * row + 5 * col + color_phase) % len(palette)]
    grid[source[0]][source[1]] = 2
    grid[destination[0]][destination[1]] = 3
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact ARC colors 0..9")

    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    payload = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2, 3)
    ]
    if len(red) != 1 or len(green) != 1 or not payload:
        raise ValueError("expected one red marker, one green marker, and one payload")
    cells = {(row, col) for row, col, _ in payload}
    stack = [next(iter(cells))]
    seen = {stack[0]}
    while stack:
        row, col = stack.pop()
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + drow, col + dcol)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    if seen != cells:
        raise ValueError("payload must be one 4-connected object")

    rows = [row for row, _, _ in payload]
    cols = [col for _, col, _ in payload]
    bbox_height = max(rows) - min(rows) + 1
    bbox_width = max(cols) - min(cols) + 1
    if bbox_height == bbox_width:
        raise ValueError("payload bounding box must be strictly wide or tall")
    axis = "wide" if bbox_width > bbox_height else "tall"
    base_delta = (green[0][0] - red[0][0], green[0][1] - red[0][1])
    if base_delta == (0, 0):
        raise ValueError("marker vector must be nonzero")
    return {
        "height": len(grid),
        "width": width,
        "source": red[0],
        "destination": green[0],
        "payload": payload,
        "payload_cells": cells,
        "bbox_height": bbox_height,
        "bbox_width": bbox_width,
        "payload_axis": axis,
        "base_delta": base_delta,
    }


def _multiplier(policy: str, axis: str) -> int:
    if policy == "marker_vector":
        return 1
    if policy == "payload_axis_gate":
        return 2 if axis == "wide" else -1
    raise ValueError(f"unknown translation policy {policy!r}")


def _translate(grid: list[list[int]], multiplier: int) -> list[list[int]]:
    facts = _analyze(grid)
    dr = multiplier * facts["base_delta"][0]
    dc = multiplier * facts["base_delta"][1]
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for row, col, value in facts["payload"]:
        nr, nc = row + dr, col + dc
        if not (0 <= nr < facts["height"] and 0 <= nc < facts["width"]):
            raise ValueError("selected translation moves payload out of bounds")
        output[nr][nc] = value
    return output


def transform(grid: list[list[int]], policy: str) -> list[list[int]]:
    if type(policy) is not str or policy not in SETTINGS:
        raise ValueError(f"policy must be one of {SETTINGS}")
    facts = _analyze(grid)
    return _translate(grid, _multiplier(policy, facts["payload_axis"]))


def transform_with_axis(grid: list[list[int]], axis: str) -> list[list[int]]:
    if axis not in ("wide", "tall"):
        raise ValueError("axis must be 'wide' or 'tall'")
    return _translate(grid, 2 if axis == "wide" else -1)


def sequential_trace(grid: list[list[int]], policy: str) -> dict[str, Any]:
    if policy not in SETTINGS:
        raise ValueError(f"policy must be one of {SETTINGS}")
    facts = _analyze(grid)
    multiplier = _multiplier(policy, facts["payload_axis"])
    return {
        "step_a": "classify payload bounding-box axis",
        "intermediate": facts["payload_axis"],
        "step_b": "choose marker-vector multiplier from payload axis, then translate",
        "selected_multiplier": multiplier,
        "base_delta": list(facts["base_delta"]),
        "final_delta": [
            multiplier * facts["base_delta"][0],
            multiplier * facts["base_delta"][1],
        ],
    }


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    facts = _analyze(grid)
    cells = facts["payload_cells"]
    base_dr, base_dc = facts["base_delta"]
    gated_multiplier = 2 if facts["payload_axis"] == "wide" else -1
    bbox_area = facts["bbox_height"] * facts["bbox_width"]
    return {
        "height": facts["height"],
        "width": facts["width"],
        "payload_size": len(facts["payload"]),
        "palette_size": len({value for _, _, value in facts["payload"]}),
        "payload_axis": facts["payload_axis"],
        "bbox_height": facts["bbox_height"],
        "bbox_width": facts["bbox_width"],
        "bbox_solid": len(cells) == bbox_area,
        "boundary_contact": any(
            row in (0, facts["height"] - 1) or col in (0, facts["width"] - 1)
            for row, col in cells
        ),
        "canonical_delta": [base_dr, base_dc],
        "gated_delta": [gated_multiplier * base_dr, gated_multiplier * base_dc],
    }


def _validate_request(seed: Any, settings: Any, demos: Any, queries: Any) -> str:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")
    return _validate_settings(settings)


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    selected = _validate_request(seed, settings, demos, queries)
    train_inputs = [
        _build_input(seed, "demo", index, _DEMO_PROFILES[index])
        for index in range(demos)
    ]
    test_inputs = [
        _build_input(seed, "query", index, _QUERY_PROFILES[index])
        for index in range(queries)
    ]
    return {
        "train": [
            {"input": grid, "output": transform(grid, selected)}
            for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": transform(grid, selected)}
            for grid in test_inputs
        ],
        "program_solution": program(settings),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def finite_setting_survivors(demos: list[dict[str, Any]]) -> list[str]:
    survivors = []
    for setting in SETTINGS:
        if all(transform(pair["input"], setting) == pair["output"] for pair in demos):
            survivors.append(setting)
    return survivors


def _rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    facts = _analyze(grid)
    vertical_dominant = abs(facts["base_delta"][0]) >= abs(facts["base_delta"][1])
    palette_even = len({value for _, _, value in facts["payload"]}) % 2 == 0
    return {
        "always_double": _translate(grid, 2),
        "always_reverse": _translate(grid, -1),
        "axis_gate_swapped": _translate(
            grid, -1 if facts["payload_axis"] == "wide" else 2
        ),
        "vector_orientation_gate": _translate(grid, 2 if vertical_dominant else -1),
        "palette_parity_gate": _translate(grid, 2 if palette_even else -1),
    }


def audit_shortcuts(demos: list[dict[str, Any]], selected: str) -> list[dict[str, Any]]:
    if selected not in SETTINGS:
        raise ValueError(f"selected must be one of {SETTINGS}")
    rows = []
    # The other declared setting is itself the most important finite rival.
    rival_names: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        f"declared_{SETTINGS[1] if selected == SETTINGS[0] else SETTINGS[0]}": (
            lambda grid: transform(grid, SETTINGS[1] if selected == SETTINGS[0] else SETTINGS[0])
        )
    }
    for name in (
        "always_double",
        "always_reverse",
        "axis_gate_swapped",
        "vector_orientation_gate",
        "palette_parity_gate",
    ):
        rival_names[name] = lambda grid, name=name: _rival_outputs(grid)[name]

    for name, rival in rival_names.items():
        mismatches = [
            index
            for index, pair in enumerate(demos)
            if rival(pair["input"]) != pair["output"]
        ]
        rows.append(
            {
                "name": name,
                "refuted": bool(mismatches),
                "mismatching_demo_indices": mismatches,
            }
        )
    return rows


def episode_summary(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [scene_facts(pair["input"]) for pair in episode["train"]],
        "test": [scene_facts(pair["input"]) for pair in episode["test"]],
        "public_sha256": hashlib.sha256(
            json.dumps(public_challenge(episode), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }

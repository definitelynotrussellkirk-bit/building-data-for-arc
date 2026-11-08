#!/usr/bin/env python3
"""Native marker-derived cycle-phase family for ``f891d1ff5dd8``.

The exact canonical setting still starts the body cycle at ``row0[0]``.  The
alternative first reads the unique row-1 cell whose color occurs in row 0,
locates that color's (unique) header index, and uses that input-dependent index
as the body-cycle phase.  Inputs are sampled independently of the private
setting and labels returned by :func:`generate` are deterministic Python claims;
native qualification independently re-executes every claim in protected Racket.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "f891d1ff5dd8"
VERSION = "marker-derived-cycle-phase-v1"
CYCLE_STARTS = ("first_header", "row1_marker")
DEFAULT_SETTINGS = {"cycle_start": "first_header"}
CANONICAL_RULE_HASH = "9a77eb6a5412"
CANONICAL_SHA256 = "0f0bd2e42171cc41e580b5adbbde6c7dcd73b9efdc12ca822b6b99a6b7594363"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

SEQUENTIAL_DEPENDENCY = {
    "step_a": (
        "Read the unique row-1 cell whose color occurs in row 0, then locate "
        "that marker color's unique index in the ordered header."
    ),
    "intermediate": "The marker color's input-dependent zero-based header index.",
    "step_b": (
        "Use that header index as the phase offset when selecting the uniform "
        "color for every body row."
    ),
    "why_b_depends_on_a": (
        "The first body color and every later cycle position depend on where "
        "this input's marker color occurs in row 0; using the marker's physical "
        "column or phase zero changes the painted body."
    ),
}

# Fixed geometry roles make count requests prefix-stable.  Seeded colors and
# body details still vary each episode.  Every phase is nonzero and differs from
# the marker's physical column, so either declared setting is distinguished by
# every demonstration.  The final query is substantive 30x30 stress.
DEMO_PROFILES = (
    (9, 5, 2, 4),
    (12, 6, 4, 1),
    (15, 7, 3, 6),
    (18, 8, 5, 2),
    (21, 9, 7, 3),
    (24, 10, 6, 9),
)
QUERY_PROFILES = (
    (13, 7, 4, 1),
    (19, 11, 8, 3),
    (25, 16, 11, 5),
    (30, 30, 17, 4),
)


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _validate_seed(seed: Any) -> int:
    return _integer(seed, 0, 2**63 - 1, "seed")


def validate_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"cycle_start"}:
        raise ValueError("settings must contain exactly cycle_start")
    value = settings["cycle_start"]
    if type(value) is not str or value not in CYCLE_STARTS:
        raise ValueError(f"cycle_start must be one of {CYCLE_STARTS}")
    return {"cycle_start": value}


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the selected authority")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    programs: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical source for {TASK_ID}")
    return _check_canonical_source(programs.pop())


MARKER_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (colors (row-at g 0))
                (marker (find (lambda (v) (member? v colors))
                              (row-at g 1)))
                (phase-pair (find (lambda (iv) (= (second iv) marker))
                                  (enumerate-list colors)))
                (phase (first phase-pair)))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (< r 2)
                               (at g r c)
                               (nth colors (mod (+ phase (- r 2)) w))))))))"""

MARKER_COLUMN_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (colors (row-at g 0))
                (marker-cell (find (lambda (iv) (member? (second iv) colors))
                                   (enumerate-list (row-at g 1))))
                (phase (first marker-cell)))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (< r 2)
                               (at g r c)
                               (nth colors (mod (+ phase (- r 2)) w))))))))"""


def program(settings: Any, *, root: Path | str | None = None) -> str:
    normalized = validate_settings(settings)
    if normalized == DEFAULT_SETTINGS:
        return canonical_source(root=root)
    return MARKER_PROGRAM


def counterfactual_program(name: str) -> str:
    if name != "marker_column":
        raise ValueError("counterfactual name must be marker_column")
    return MARKER_COLUMN_PROGRAM


def _strict_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be rectangular with dimensions 1..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must contain exact integer colors 0..9")
    return copy.deepcopy(value)


def analyze(grid: Any) -> dict[str, int]:
    """Validate the admitted marker grammar and return its causal intermediate."""
    value = _strict_grid(grid)
    if len(value) < 3:
        raise ValueError("marker-cycle inputs need at least three rows")
    header = value[0]
    if any(color == 0 for color in header) or len(set(header)) < 2:
        raise ValueError("row 0 must be a nonzero ordered cycle with at least two colors")
    row1 = value[1]
    marker_cells = [(column, color) for column, color in enumerate(row1) if color in header]
    if len(marker_cells) != 1:
        raise ValueError("row 1 must contain exactly one header-colored marker")
    marker_column, marker_color = marker_cells[0]
    if header.count(marker_color) != 1:
        raise ValueError("the row-1 marker color must occur exactly once in row 0")
    decoys = set(row1) - {marker_color}
    if len(decoys) != 1:
        raise ValueError("all non-marker row-1 cells must share one decoy color")
    decoy_color = next(iter(decoys))
    if decoy_color == 0 or decoy_color in header:
        raise ValueError("the nonzero row-1 decoy color must be absent from row 0")
    return {
        "marker_color": marker_color,
        "marker_column": marker_column,
        "marker_header_index": header.index(marker_color),
        "decoy_color": decoy_color,
    }


def solve(grid: Any, settings: Any) -> list[list[int]]:
    normalized = validate_settings(settings)
    value = _strict_grid(grid)
    info = analyze(value)
    header = value[0]
    phase = 0 if normalized == DEFAULT_SETTINGS else info["marker_header_index"]
    output = copy.deepcopy(value)
    width = len(header)
    for r in range(2, len(value)):
        output[r] = [header[(phase + r - 2) % width]] * width
    return output


def _rng(seed: int, split: str, index: int) -> random.Random:
    return random.Random(f"{TASK_ID}:{VERSION}:inputs:{seed}:{split}:{index}")


def _fill_rect(
    grid: list[list[int]],
    color: int,
    top: int,
    left: int,
    bottom: int,
    right: int,
) -> None:
    for r in range(max(2, top), min(len(grid) - 1, bottom) + 1):
        for c in range(max(0, left), min(len(grid[0]) - 1, right) + 1):
            grid[r][c] = color


def _draw_body(grid: list[list[int]], decoy: int, rng: random.Random, role: int) -> None:
    """Place distributed overwrite distractors, including boundary contact."""
    height, width = len(grid), len(grid[0])
    body_h = height - 2
    # Top-left boundary block.
    _fill_rect(
        grid,
        decoy,
        2,
        0,
        2 + max(1, body_h // 5),
        max(1, width // 5),
    )
    # Interior block with a seed/role-dependent offset.
    center_h = max(2, body_h // 4)
    center_w = max(2, width // 4)
    center_top = 2 + max(0, body_h // 2 - center_h // 2 + (role % 2))
    center_left = max(0, width // 2 - center_w // 2 + rng.choice((-1, 0, 1)))
    _fill_rect(
        grid,
        decoy,
        center_top,
        center_left,
        center_top + center_h,
        center_left + center_w,
    )
    # Bottom-right boundary block.
    tail_h = max(2, body_h // 5)
    tail_w = max(2, width // 5)
    _fill_rect(grid, decoy, height - 1 - tail_h, width - 1 - tail_w, height - 1, width - 1)

    # A sparse crossing makes ordinary inputs less rectangle-specific.  It is
    # deterministic and remains a pure distractor because both rules overwrite
    # the entire body.
    if height >= 12 and width >= 7:
        row = 2 + (role * 3 + rng.randrange(max(1, body_h))) % body_h
        for c in range(role % 3, width, max(3, width // 6)):
            grid[row][c] = decoy
        column = (role * 5 + rng.randrange(width)) % width
        for r in range(2 + role % 2, height, max(3, body_h // 6)):
            grid[r][column] = decoy


def _make_input(
    seed: int,
    split: str,
    index: int,
    profile: tuple[int, int, int, int],
) -> list[list[int]]:
    height, width, marker_header_index, marker_column = profile
    if not (
        3 <= height <= 30
        and 2 <= width <= 30
        and 0 < marker_header_index < width
        and 0 <= marker_column < width
        and marker_column != marker_header_index
    ):
        raise AssertionError("invalid fixed profile")
    rng = _rng(seed, split, index)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    decoy, marker = palette[:2]
    fillers = palette[2:]
    offset = rng.randrange(len(fillers))
    header = [fillers[(column + offset + index) % len(fillers)] for column in range(width)]
    header[marker_header_index] = marker
    row1 = [decoy] * width
    row1[marker_column] = marker
    grid = [[0] * width for _ in range(height)]
    grid[0] = header
    grid[1] = row1
    _draw_body(grid, decoy, rng, index + (0 if split == "demo" else 11))
    observed = analyze(grid)
    if observed["marker_header_index"] != marker_header_index:
        raise AssertionError("constructed marker phase differs from profile")
    if observed["marker_column"] != marker_column:
        raise AssertionError("constructed marker column differs from profile")
    return grid


def input_bank(seed: Any) -> dict[str, list[list[list[int]]]]:
    seed = _validate_seed(seed)
    return {
        "train": [
            _make_input(seed, "demo", index, profile)
            for index, profile in enumerate(DEMO_PROFILES)
        ],
        "test": [
            _make_input(seed, "query", index, profile)
            for index, profile in enumerate(QUERY_PROFILES)
        ],
    }


def generate(
    seed: Any,
    settings: Any,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    seed = _validate_seed(seed)
    normalized = validate_settings(settings)
    demos = _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    queries = _integer(queries, MIN_QUERIES, MAX_QUERIES, "queries")
    bank = input_bank(seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": copy.deepcopy(grid), "output": solve(grid, normalized)}

    return {
        "train": [pair(grid) for grid in bank["train"][:demos]],
        "test": [pair(grid) for grid in bank["test"][:queries]],
        "program_solution": program(normalized),
        "settings": copy.deepcopy(normalized),
        "seed": seed,
        "prototype_version": VERSION,
    }


def parameters_for_seed(seed: Any) -> dict[str, str]:
    seed = _validate_seed(seed)
    return {
        "cycle_start": random.Random(f"{TASK_ID}:{VERSION}:settings:{seed}").choice(
            CYCLE_STARTS
        )
    }


def public_challenge(episode: Any, *, query_index: Any = 0) -> dict[str, Any]:
    query_index = _integer(query_index, 0, MAX_QUERIES - 1, "query_index")
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or query_index >= len(test):
        raise ValueError("episode does not contain the requested query")
    public = {
        "train": [
            {
                "input": _strict_grid(pair["input"]),
                "output": _strict_grid(pair["output"]),
            }
            for pair in train
        ],
        "test": [{"input": _strict_grid(test[query_index]["input"])}],
    }
    # The shared helper is also a strict visible-grid validator.
    public_challenge_bytes(public)
    return public


def public_record(episode: Any, *, query_index: Any = 0) -> tuple[str, bytes, dict[str, Any]]:
    public = public_challenge(episode, query_index=query_index)
    payload = public_challenge_bytes(public)
    return public_challenge_id(public), payload, public


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    value = _strict_grid(grid)
    if type(source) is not str or not source.strip():
        raise ValueError("source must be nonempty Racket text")
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in value
    ) + ")"
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        output = normalize_grid(active.eval_text(f"({wrap_rule(source)} {literal})"))
    if output is None:
        raise RuntimeError("Racket program did not return a rectangular grid")
    return _strict_grid(output)


# Executable finite rivals for the bounded self-audit.  They all preserve the
# canonical outer transformation and differ only in how the phase is inferred.
def _phase_program(phase_bindings: str, phase_expression: str, *, reverse: bool = False) -> str:
    index = (
        f"(mod (- {phase_expression} (- r 2)) w)"
        if reverse
        else f"(mod (+ {phase_expression} (- r 2)) w)"
    )
    return f"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (colors (row-at g 0))
                {phase_bindings})
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (< r 2)
                               (at g r c)
                               (nth colors {index})))))))"""


def rival_programs(*, root: Path | str | None = None) -> dict[str, str]:
    canonical = canonical_source(root=root)
    marker_bindings = """(marker (find (lambda (v) (member? v colors)) (row-at g 1)))
                (phase-pair (find (lambda (iv) (= (second iv) marker))
                                  (enumerate-list colors)))
                (phase (first phase-pair))"""
    marker_cell_bindings = """(marker-cell (find (lambda (iv) (member? (second iv) colors))
                                   (enumerate-list (row-at g 1))))
                (phase (first marker-cell))"""
    minimum_bindings = """(target (min-list colors))
                (phase-pair (find (lambda (iv) (= (second iv) target))
                                  (enumerate-list colors)))
                (phase (first phase-pair))"""
    maximum_bindings = minimum_bindings.replace("min-list", "max-list")
    marker_value_bindings = """(marker (find (lambda (v) (member? v colors)) (row-at g 1)))
                (phase (mod marker w))"""
    return {
        "canonical_phase_zero": canonical,
        "marker_header_index": MARKER_PROGRAM,
        "marker_physical_column": _phase_program(marker_cell_bindings, "phase"),
        "minimum_header_color": _phase_program(minimum_bindings, "phase"),
        "maximum_header_color": _phase_program(maximum_bindings, "phase"),
        "marker_numeric_mod_width": _phase_program(marker_value_bindings, "phase"),
        "reverse_from_marker": _phase_program(marker_bindings, "phase", reverse=True),
    }

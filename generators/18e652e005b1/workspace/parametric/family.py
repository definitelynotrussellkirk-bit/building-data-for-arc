"""Native matched-input family for 18e652e005b1.

The byte-exact default crops a monochrome motif and broadcasts recolored copies
with blank separator columns.  The alternative uses the same extracted motif
and command order but places copies at stride ``motif_width - 1``.  Cells with
one contributor keep that copy's command color; true multi-copy intersections
are highlighted with 8.  The retained counterfactual makes the same overlap
intermediate but silently lets the first copy win, isolating the second step.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "18e652e005b1"
HERE = Path(__file__).resolve().parent
CANONICAL_SHA256 = "5cf809a8190fd5960c857c40999362d16350ed2479be617e222a07f0d8705fc9"
SETTINGS = ("gapped", "overlap_highlight")
RIVALS = (
    "overlap_first_wins",
    "overlap_last_wins",
    "overlap_highlight_all",
    "overlap_highlight_left_edge",
)
HYPOTHESES = SETTINGS + RIVALS

# input h, input w, commands, cropped motif h, cropped motif w, dense
_DEMO_PROFILES = (
    (8, 10, 2, 4, 4, False),
    (10, 12, 3, 5, 4, False),
    (12, 15, 4, 6, 5, False),
    (16, 18, 5, 8, 5, True),
    (22, 24, 3, 12, 8, True),
    (26, 28, 2, 17, 12, True),
)
_QUERY_PROFILES = (
    (9, 11, 3, 5, 3, False),
    (15, 17, 4, 9, 6, True),
    (24, 26, 2, 15, 11, True),
    (30, 30, 2, 20, 14, True),
)
_COMMAND_PALETTE = (2, 4, 6, 9, 3, 5)
_MOTIF_COLOR = 7


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(value: object) -> str:
    if type(value) is not dict or set(value) != {"layout"}:
        raise ValueError("settings must contain exactly layout")
    layout = value["layout"]
    if type(layout) is not str or layout not in SETTINGS:
        raise ValueError(f"layout must be one of {SETTINGS!r}")
    return layout


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
        f"{TASK_ID}:overlap-highlight-v1:{seed}:{role}".encode("utf-8")
    ).digest()
    return random.Random(digest)


def canonical_program() -> str:
    text = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if hashlib.sha256(text.encode()).hexdigest() != CANONICAL_SHA256:
        raise RuntimeError("canonical.rkt no longer matches the frozen target")
    return text


def alternative_program() -> str:
    return (HERE / "overlap_highlight.rkt").read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "overlap_first_wins.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    layout = _setting(settings)
    return canonical_program() if layout == "gapped" else alternative_program()


def _extract(value: object) -> dict[str, Any]:
    source = _grid(value)
    h, w = len(source), len(source[0])
    if any(source[r][-1] != 0 for r in range(h)):
        raise ValueError("reserved final input column must be blank")

    command_cols = [c for c, color in enumerate(source[-1]) if color != 0]
    if command_cols != list(range(len(command_cols))) or len(command_cols) < 2:
        raise ValueError("commands must be a nonzero prefix of length at least two")
    commands = [source[-1][c] for c in command_cols]
    if len(set(commands)) != len(commands):
        raise ValueError("command colors must be distinct")

    cells = [
        (r, c)
        for r in range(h - 1)
        for c in range(w - 1)
        if source[r][c] != 0
    ]
    if len(cells) < 3:
        raise ValueError("motif must contain at least three cells")
    motif_colors = {source[r][c] for r, c in cells}
    if len(motif_colors) != 1 or next(iter(motif_colors)) in commands:
        raise ValueError("motif must use one color distinct from every command")

    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    motif = [row[c0 : c1 + 1] for row in source[r0 : r1 + 1]]
    return {
        "source": source,
        "commands": commands,
        "motif": motif,
        "motif_color": next(iter(motif_colors)),
        "bbox": (r0, c0, r1, c1),
    }


def _gapped(state: dict[str, Any]) -> list[list[int]]:
    motif = state["motif"]
    commands = state["commands"]
    mh, mw = len(motif), len(motif[0])
    out_w = len(commands) * mw + len(commands) - 1
    out = [[0 for _ in range(out_w)] for _ in range(mh)]
    for index, color in enumerate(commands):
        left = index * (mw + 1)
        for r in range(mh):
            for c in range(mw):
                if motif[r][c] != 0:
                    out[r][left + c] = color
    return out


def _overlap_state(state: dict[str, Any]) -> tuple[list[list[list[int]]], int]:
    motif = state["motif"]
    commands = state["commands"]
    mh, mw = len(motif), len(motif[0])
    stride = max(1, mw - 1)
    out_w = mw + (len(commands) - 1) * stride
    contributors: list[list[list[int]]] = [
        [[] for _ in range(out_w)] for _ in range(mh)
    ]
    for index, color in enumerate(commands):
        left = index * stride
        for r in range(mh):
            for c in range(mw):
                if motif[r][c] != 0:
                    contributors[r][left + c].append(color)
    return contributors, stride


def _render_overlap(contributors: list[list[list[int]]], mode: str) -> list[list[int]]:
    out = []
    for row in contributors:
        rendered = []
        for colors in row:
            if not colors:
                rendered.append(0)
            elif mode == "highlight" and len(colors) > 1:
                rendered.append(8)
            elif mode == "last":
                rendered.append(colors[-1])
            elif mode == "highlight_all":
                rendered.append(8)
            else:
                rendered.append(colors[0])
        out.append(rendered)
    return out


def analyze(value: object) -> dict[str, Any]:
    state = _extract(value)
    contributors, stride = _overlap_state(state)
    overlap_cells = sum(len(colors) > 1 for row in contributors for colors in row)
    overlap_rows = sorted(
        {r for r, row in enumerate(contributors) if any(len(colors) > 1 for colors in row)}
    )
    motif = state["motif"]
    return {
        "height": len(state["source"]),
        "width": len(state["source"][0]),
        "commands": len(state["commands"]),
        "command_colors": list(state["commands"]),
        "motif_height": len(motif),
        "motif_width": len(motif[0]),
        "motif_cells": sum(cell != 0 for row in motif for cell in row),
        "stride": stride,
        "overlap_cells": overlap_cells,
        "overlap_rows": overlap_rows,
        "contributors": contributors,
        "gapped": _gapped(state),
    }


def predict(value: object, hypothesis: str) -> list[list[int]]:
    if type(hypothesis) is not str or hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis {hypothesis!r}")
    state = analyze(value)
    contributors = state["contributors"]
    if hypothesis == "gapped":
        return deepcopy(state["gapped"])
    if hypothesis == "overlap_highlight":
        return _render_overlap(contributors, "highlight")
    if hypothesis == "overlap_first_wins":
        return _render_overlap(contributors, "first")
    if hypothesis == "overlap_last_wins":
        return _render_overlap(contributors, "last")
    if hypothesis == "overlap_highlight_all":
        return _render_overlap(contributors, "highlight_all")
    if hypothesis == "overlap_highlight_left_edge":
        # A plausible but wrong shortcut: mark the first occupied cell of every
        # output row instead of the cells with multiple copy contributors.
        out = _render_overlap(contributors, "first")
        for row in out:
            occupied = [c for c, color in enumerate(row) if color != 0]
            if occupied:
                row[occupied[0]] = 8
        return out
    raise AssertionError(hypothesis)  # pragma: no cover


def solve(value: object, layout: str) -> list[list[int]]:
    if layout not in SETTINGS:
        raise ValueError(f"layout must be one of {SETTINGS!r}")
    return predict(value, layout)


def _motif(mh: int, mw: int, dense: bool, variant: int) -> set[tuple[int, int]]:
    # Full top and bottom rows ensure both crop edges are occupied on identical
    # rows, producing at least two genuine intersections at every copy boundary.
    cells = {(0, c) for c in range(mw)} | {(mh - 1, c) for c in range(mw)}
    if dense:
        for r in range(1, mh - 1):
            for c in range(mw):
                if (2 * r + 3 * c + variant) % 4 != 0:
                    cells.add((r, c))
    elif variant % 2 == 0:
        # Connected C/frame-like morphology.
        cells.update((r, 0) for r in range(mh))
        bridge = mh // 2
        cells.update((bridge, c) for c in range(mw))
    else:
        # Disconnected bars plus interior evidence, preserving crop dimensions.
        for r in range(2, mh - 2, 3):
            for c in range(1, mw - 1):
                if (r + c + variant) % 2 == 0:
                    cells.add((r, c))
    return cells


def _scene(
    seed: int,
    role: str,
    profile: tuple[int, int, int, int, int, bool],
    index: int,
) -> list[list[int]]:
    h, w, n_commands, mh, mw, dense = profile
    if n_commands * mw + n_commands - 1 > 30:
        raise RuntimeError("profile canonical output exceeds ARC width")
    rng = _rng(seed, f"{role}:{index}")
    grid = [[0 for _ in range(w)] for _ in range(h)]
    motif = _motif(mh, mw, dense, index + seed)

    # Vary placement while keeping the reserved final column blank.  Stress
    # profiles alternate top/left versus bottom/right attachment.
    if index % 2 == 0:
        top, left = 0, 0
    else:
        top, left = h - 1 - mh, w - 1 - mw
    # A seed-dependent harmless translation exercises absolute-position
    # invariance when slack exists.
    if h - 1 - mh > 0 and index not in (0, 3):
        top = rng.randrange(h - mh)
    if w - 1 - mw > 0 and index not in (0, 3):
        left = rng.randrange(w - mw)
    for r, c in motif:
        grid[top + r][left + c] = _MOTIF_COLOR

    palette = list(_COMMAND_PALETTE)
    shift = rng.randrange(len(palette))
    palette = palette[shift:] + palette[:shift]
    commands = palette[:n_commands]
    for c, color in enumerate(commands):
        grid[-1][c] = color

    state = analyze(grid)
    if state["overlap_cells"] < n_commands - 1:
        raise RuntimeError("constructed motif does not create enough intersections")
    if state["motif_height"] != mh or state["motif_width"] != mw:
        raise RuntimeError("constructed motif crop dimensions drifted")
    return grid


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, Any]:
    seed_i = _integer(seed, "seed", 0, 2**63 - 1)
    layout = _setting(settings)
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

    train = [{"input": grid, "output": solve(grid, layout)} for grid in demo_inputs]
    test = [{"input": grid, "output": solve(grid, layout)} for grid in query_inputs]
    return {
        "program_solution": program({"layout": layout}),
        "train": train,
        "test": test,
        "private_query_bank": deepcopy(test),
        "metadata": {
            "task_id": TASK_ID,
            "settings": {"layout": layout},
            "seed": seed_i,
            "dependency": (
                "Step A places command-recolored motif copies at one-column "
                "overlap stride; Step B detects cells with multiple true copy "
                "contributors and highlights exactly those intersections."
            ),
        },
    }

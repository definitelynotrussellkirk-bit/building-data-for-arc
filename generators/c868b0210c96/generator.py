"""Generator for arc_additional_puzzles_21_set17_bundle:M119.

Rule: cell (0,0) is a 1-based panel selector, cell (0,1) is a transform
command (0=id,1=cw,2=180,3=transpose,4=flip-lr,5=flip-ud). The body (rows
1+) holds panels separated by blank columns; output = the selected panel,
cropped to content, with the command applied.

This generator builds N body panels (each column non-blank so it doesn't
split) separated by blank columns, and a control row selecting one panel
and a command.

Combinatorial axes: grid size, panel count, panel contents/sizes, the
selector, and the command.
Degenerates: no_select, no_command, no_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c868b0210c96"
VERSION = "2.0.0"  # diversity: N random panels + free selector/command (was fixed ~20)
TASK_ID = "c868b0210c96"
SUMMARY = (
    "0-bg grid (size varies). Row 0 is a control row: (0,0)=1-based panel "
    "selector, (0,1)=transform command (0..5). The body (rows 1+) holds N "
    "single-color connected motif panels separated by blank columns. Rule: "
    "take the selected panel, crop to content, apply the command. Panel "
    "count/shapes/sizes, selector and command vary while preserving the "
    "canonical one-color-per-panel distribution."
)

INVARIANTS = [
    "row 0 holds the selector at (0,0) and the command at (0,1)",
    "body panels are separated by blank columns and have no internal blank column",
    "each body panel is a single-color connected motif (matching the canonical task)",
    "the output is the selected cropped panel under the dihedral command",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_select", "no_command", "no_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "varies"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "varies"},
    "n_panels":       {"type": "int", "default": "varies", "valid": "2..5"},
    "select_idx":     {"type": "int", "default": "rng 1..N", "valid": "1..N"},
    "command":        {"type": "int", "default": "rng 0..5", "valid": "0..5"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_select|no_command|no_panels"},
}


def _panel(rng, hp, wp, color):
    """Single-color connected motif; every column has >=1 non-0 so it never splits.

    The canonical examples use one colored object per panel.  A previous version
    filled each panel with independent per-cell colors, which still exercised the
    Racket splitter but drifted away from the task distribution by turning each
    panel into many tiny components.  Build a random-walk mask instead: one path
    crosses all columns, then a few adjacent cells thicken it.
    """
    mask = [[False] * wp for _ in range(hp)]
    r = rng.randint(0, hp - 1)
    path = []
    for c in range(wp):
        prev_r = r
        if c:
            r = max(0, min(hp - 1, r + rng.choice([-1, 0, 1])))
            # If the random walk changes row, add a vertical bridge in this
            # column so consecutive columns remain 4-connected, not diagonal.
            step = 1 if r >= prev_r else -1
            for rr in range(prev_r, r + step, step):
                mask[rr][c] = True
                path.append((rr, c))
        mask[r][c] = True
        path.append((r, c))
    for r, c in list(path):
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        rng.shuffle(dirs)
        for dr, dc in dirs[:rng.randint(0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < hp and 0 <= nc < wp:
                mask[nr][nc] = True
    if hp * wp >= 9 and all(mask[r][c] for r in range(hp) for c in range(wp)):
        # Keep at least one hole in large panels so selected outputs are not
        # indistinguishable solid-color blocks.  Removing a corner from a full
        # rectangle preserves 4-connectivity and column non-blankness.
        mask[0][0] = False
    return [[color if mask[r][c] else 0 for c in range(wp)] for r in range(hp)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        nr, sr = (2, 3), (2, 3)
    elif difficulty == "hard":
        nr, sr = (4, 5), (3, 5)
    else:
        nr, sr = (2, 4), (2, 4)

    N = rng.randint(*nr)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], N)
    panels = []
    for i in range(N):
        hp = rng.randint(*sr); wp = rng.randint(*sr)
        panels.append(_panel(rng, hp, wp, colors[i]))

    bh = max(len(p) for p in panels)
    body_w = sum(len(p[0]) for p in panels) + (N - 1)   # one blank column between panels
    w = max(body_w, 2)
    h = bh + 1
    g = full_grid(h, w, 0)

    # place panels left to right, each at a random vertical offset, blank col between
    col = 0
    for p in panels:
        hp = len(p); wp = len(p[0])
        top = 1 + rng.randint(0, bh - hp)
        for r in range(hp):
            for c in range(wp):
                if p[r][c]:
                    g[top + r][col + c] = p[r][c]
        col += wp + 1

    sel = rng.randint(1, N)
    cmd = rng.randint(0, 5)
    g[0][0] = sel
    g[0][1] = cmd
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify selector/command and canonical panel structure."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h < 2 or w < 2:
        return ["need selector/command header plus body panels"]
    sel, cmd = grid[0][0], grid[0][1]
    if sel <= 0:
        errs.append("row 0 col 0 (selector) is 0 — expected 1-based panel index")
    if not (0 <= cmd <= 5):
        errs.append(f"command {cmd} outside 0..5")

    def blank_body_col(c):
        return all(grid[r][c] == 0 for r in range(1, h))

    panels = []
    c = 0
    while c < w:
        while c < w and blank_body_col(c):
            c += 1
        if c >= w:
            break
        start = c
        while c < w and not blank_body_col(c):
            c += 1
        panels.append((start, c - 1))
    if not panels:
        errs.append("body (rows 1+) has no panels")
        return errs
    if sel > len(panels):
        errs.append(f"selector {sel} exceeds panel count {len(panels)}")

    for start, end in panels:
        cells = [(r, c) for r in range(1, h) for c in range(start, end + 1) if grid[r][c] != 0]
        colors = {grid[r][c] for r, c in cells}
        if len(colors) != 1:
            errs.append(f"panel {start}..{end} has colors {sorted(colors)}; expected one motif color")
            continue
        seen = {cells[0]} if cells else set()
        stack = list(seen)
        cell_set = set(cells)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cell_set and nb not in seen:
                    seen.add(nb); stack.append(nb)
        if len(seen) != len(cell_set):
            errs.append(f"panel {start}..{end} is not 4-connected")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(4, 7, 0)
    g[1][0] = 3; g[2][1] = 3
    g[1][4] = 4; g[2][5] = 4
    g[0][0] = 1; g[0][1] = 1
    if name == "no_select":
        g[0][0] = 0
        return g
    if name == "no_command":
        g[0][1] = 0
        return g
    if name == "no_panels":
        return full_grid(4, 7, 0)
    return g

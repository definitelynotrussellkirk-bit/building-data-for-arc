"""Fresh generators and Python mirror for public ARC parent 7491f3cf.

The input contains four equal panels inside a monochrome frame.  The first
panel supplies an 8-connected divider and a singleton marker.  The next two
panels supply candidate pixels.  The fourth panel is completed by selecting
one source inside the marker's 4-connected region and the other outside it.
"""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import random
from typing import Iterable

RULE_TASK_ID = 'ee_7491f3cf'

Grid = list[list[int]]
Point = tuple[int, int]


def _validate_grid(grid: Grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError('grid must be a non-empty list of rows')
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError('grid must be rectangular')
    if len(grid) > 30 or width > 30:
        raise ValueError('ARC grids are at most 30x30')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('grid cells must be integer colors 0..9')
    return len(grid), width


def _runs(values: Iterable[bool]) -> list[tuple[int, int]]:
    values = list(values)
    out: list[tuple[int, int]] = []
    i = 0
    while i < len(values):
        if not values[i]:
            i += 1
            continue
        j = i + 1
        while j < len(values) and values[j]:
            j += 1
        out.append((i, j))
        i = j
    return out


def panel_layout(grid: Grid) -> tuple[int, list[int], list[tuple[int, int]], tuple[int, int]]:
    """Return frame color, separator columns, four panel column runs, row run."""
    h, w = _validate_grid(grid)
    frame = grid[0][0]
    full_rows = [r for r in range(h) if all(grid[r][c] == frame for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == frame for r in range(h))]
    interior_rows = [r for r in range(h) if r not in full_rows]
    if not interior_rows or interior_rows != list(range(min(interior_rows), max(interior_rows) + 1)):
        raise ValueError('expected one contiguous panel row band')
    panel_cols = _runs(c not in set(full_cols) for c in range(w))
    if len(panel_cols) != 4 or len({b - a for a, b in panel_cols}) != 1:
        raise ValueError('expected four equal panels separated by full frame columns')
    return frame, full_cols, panel_cols, (min(interior_rows), max(interior_rows) + 1)


def split_panels(grid: Grid) -> list[Grid]:
    _, _, columns, (r0, r1) = panel_layout(grid)
    return [[row[c0:c1] for row in grid[r0:r1]] for c0, c1 in columns]


def join_panels(panels: list[Grid], frame: int, *, trailing_frame_columns: int = 1) -> Grid:
    if type(frame) is not int or not 0 <= frame <= 9:
        raise ValueError('invalid frame color')
    if not isinstance(panels, list) or len(panels) != 4:
        raise ValueError('exactly four panels required')
    dims = [_validate_grid(p) for p in panels]
    if len(set(dims)) != 1:
        raise ValueError('panel dimensions must match')
    if type(trailing_frame_columns) is not int or not 1 <= trailing_frame_columns <= 2:
        raise ValueError('trailing frame width must be 1 or 2')
    h, w = dims[0]
    total_w = 1 + 4 * w + 3 + trailing_frame_columns
    if h + 2 > 30 or total_w > 30:
        raise ValueError('joined grid exceeds ARC bounds')
    out = [[frame] * total_w]
    for r in range(h):
        row = [frame]
        for i, panel in enumerate(panels):
            row.extend(panel[r])
            row.extend([frame] * (trailing_frame_columns if i == 3 else 1))
        out.append(row)
    out.append([frame] * total_w)
    return out


def _components(cells: set[Point], *, diagonal: bool) -> list[set[Point]]:
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    remaining = set(cells)
    result: list[set[Point]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        comp = {start}
        queue = [start]
        while queue:
            r, c = queue.pop()
            for dr, dc in offsets:
                q = (r + dr, c + dc)
                if q in remaining:
                    remaining.remove(q)
                    comp.add(q)
                    queue.append(q)
        result.append(comp)
    return result


def derive(grid: Grid) -> dict:
    panels = split_panels(grid)
    ph, pw = len(panels[0]), len(panels[0][0])
    background = Counter(v for panel in panels for row in panel for v in row).most_common(1)[0][0]
    control = panels[0]
    foreground = {(r, c) for r in range(ph) for c in range(pw) if control[r][c] != background}
    comps = _components(foreground, diagonal=True)
    if len(comps) < 2:
        raise ValueError('control panel needs a divider and a separate marker')
    # The intended divider is the largest 8-connected non-background object.
    divider = max(comps, key=lambda x: (len(x), tuple(sorted(x, reverse=True))))
    marker_cells = sorted(foreground - divider)
    if len(marker_cells) != 1:
        raise ValueError('control panel needs exactly one singleton marker outside the divider')
    marker = marker_cells[0]
    region: set[Point] = {marker}
    queue: deque[Point] = deque([marker])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            q = (r + dr, c + dc)
            if 0 <= q[0] < ph and 0 <= q[1] < pw and q not in divider and q not in region:
                region.add(q)
                queue.append(q)
    return {
        'panels': panels,
        'background': background,
        'divider': sorted(divider),
        'marker': list(marker),
        'marked_region': sorted(region),
    }


def solve(grid: Grid, source_assignment: str = 'second_in_marked') -> Grid:
    if source_assignment not in ('second_in_marked', 'third_in_marked'):
        raise ValueError('unknown source assignment')
    info = derive(grid)
    panels: list[Grid] = info['panels']
    bg: int = info['background']
    divider = {tuple(p) for p in info['divider']}
    marked = {tuple(p) for p in info['marked_region']}
    first, second = panels[1], panels[2]
    if source_assignment == 'third_in_marked':
        first, second = second, first
    h, w = len(first), len(first[0])
    completed = [[bg] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            p = (r, c)
            # The marked source receives the divider too.  It wins any overlap.
            if p in marked or p in divider:
                if first[r][c] != bg:
                    completed[r][c] = first[r][c]
                    continue
            if p not in marked or p in divider:
                if second[r][c] != bg:
                    completed[r][c] = second[r][c]
    _, full_cols, runs, (r0, r1) = panel_layout(grid)
    out = [row[:] for row in grid]
    c0, c1 = runs[3]
    for r in range(r0, r1):
        out[r][c0:c1] = completed[r - r0]
    return out


def _rng(seed: int, stream: str, index: int) -> random.Random:
    raw = hashlib.sha256(f'{seed}:{stream}:{index}:7491f3cf'.encode()).digest()
    return random.Random(int.from_bytes(raw, 'big'))


def _palette(seed: int, index: int) -> tuple[int, int, int, int, int, int]:
    rng = _rng(seed, 'palette', index)
    colors = list(range(10))
    rng.shuffle(colors)
    return tuple(colors[:6])  # frame, background, divider, marker, source A, source B


def _control_panel(h: int, w: int, bg: int, divider_color: int, marker_color: int,
                   orientation: str, marker_side: int) -> Grid:
    panel = [[bg] * w for _ in range(h)]
    if orientation == 'vertical':
        k = w // 2
        for r in range(h):
            panel[r][k] = divider_color
        marker = (h // 2, 0 if marker_side == 0 else w - 1)
    elif orientation == 'horizontal':
        k = h // 2
        for c in range(w):
            panel[k][c] = divider_color
        marker = (0 if marker_side == 0 else h - 1, w // 2)
    elif orientation == 'diag_down':
        # Top-right to bottom-left staircase, 8-connected and 4-separating.
        for r in range(h):
            c = round((w - 1) * (h - 1 - r) / max(1, h - 1))
            panel[r][c] = divider_color
        marker = (0, 0) if marker_side == 0 else (h - 1, w - 1)
    else:
        # Top-left to bottom-right staircase.
        for r in range(h):
            c = round((w - 1) * r / max(1, h - 1))
            panel[r][c] = divider_color
        marker = (0, w - 1) if marker_side == 0 else (h - 1, 0)
    # Keep marker separate even under 8-connectivity.  If necessary, choose the
    # farthest corner from the divider.
    divider = {(r, c) for r in range(h) for c in range(w) if panel[r][c] == divider_color}
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if min(max(abs(r - rr), abs(c - cc)) for rr, cc in divider) >= 2]
    if marker not in candidates:
        marker = max(candidates, key=lambda p: min(max(abs(p[0]-q[0]), abs(p[1]-q[1])) for q in divider))
    panel[marker[0]][marker[1]] = marker_color
    return panel


def _scene(seed: int, index: int, *, query: bool = False) -> Grid:
    # Every request uses fixed indices; counts never affect generated bytes.
    if query:
        dims = [(9, 5), (14, 5), (20, 6), (28, 6)]
        h, w = dims[index]
        absolute = 1000 + index
    else:
        dims = [(5, 5), (7, 5), (9, 5), (11, 5), (13, 5), (15, 5)]
        h, w = dims[index]
        absolute = index
    frame, bg, divc, markc, ca, cb = _palette(seed, absolute)
    # Avoid ambiguity if a shuffled palette accidentally gives source/background
    # colors equal through a future edit; tuple is sampled without replacement.
    orientations = ('vertical', 'horizontal', 'diag_down', 'diag_up')
    orientation = orientations[absolute % len(orientations)]
    p0 = _control_panel(h, w, bg, divc, markc, orientation, absolute % 2)
    info_grid = join_panels([p0, [[bg]*w for _ in range(h)], [[bg]*w for _ in range(h)], [[bg]*w for _ in range(h)]], frame)
    info = derive(info_grid)
    marked = {tuple(p) for p in info['marked_region']}
    divider = {tuple(p) for p in info['divider']}
    rng = _rng(seed, 'patterns', absolute)
    p1 = [[bg] * w for _ in range(h)]
    p2 = [[bg] * w for _ in range(h)]
    # Dense, distinct source textures, including both sides and the divider.
    for r in range(h):
        for c in range(w):
            if (r * 5 + c * 3 + absolute) % 4 == 0 or (r + c + absolute) % 7 == 0:
                p1[r][c] = ca
            if (r * 2 + c * 7 + absolute) % 5 == 0 or (2*r + c + absolute) % 8 == 0:
                p2[r][c] = cb
    # Pin discriminating cells in both regions and on the derived divider.
    inside = sorted(marked)
    outside = sorted({(r,c) for r in range(h) for c in range(w)} - marked - divider)
    boundary = sorted(divider)
    for cells, target, color in ((inside, p1, ca), (inside, p2, cb),
                                 (outside, p1, ca), (outside, p2, cb),
                                 (boundary, p1, ca), (boundary, p2, cb)):
        if cells:
            r, c = cells[rng.randrange(len(cells))]
            target[r][c] = color
    blank = [[bg] * w for _ in range(h)]
    trailing = 1
    return join_panels([p0, p1, p2, blank], frame, trailing_frame_columns=trailing)


def candidate_solve(grid: Grid, name: str, intended: str) -> Grid:
    if name == 'intended':
        return solve(grid, intended)
    if name == 'other_setting':
        return solve(grid, 'third_in_marked' if intended == 'second_in_marked' else 'second_in_marked')
    if name == 'identity':
        return [row[:] for row in grid]
    info = derive(grid)
    panels = info['panels']; bg = info['background']
    out = [row[:] for row in grid]
    _, _, runs, (r0, r1) = panel_layout(grid)
    c0, c1 = runs[3]
    if name == 'second_everywhere':
        replacement = panels[1]
    elif name == 'third_everywhere':
        replacement = panels[2]
    elif name == 'union_everywhere':
        replacement = [[panels[1][r][c] if panels[1][r][c] != bg else panels[2][r][c]
                        for c in range(len(panels[1][0]))] for r in range(len(panels[1]))]
    else:
        raise ValueError(name)
    for r in range(r0, r1):
        out[r][c0:c1] = replacement[r-r0]
    return out


def survivors(demos: list[dict], intended: str) -> list[str]:
    names = ('intended', 'other_setting', 'identity', 'second_everywhere', 'third_everywhere', 'union_everywhere')
    return [name for name in names if all(candidate_solve(p['input'], name, intended) == p['output'] for p in demos)]


def self_check(grid: Grid, **_: object) -> list[str]:
    findings: list[str] = []
    try:
        info = derive(grid)
        if solve(grid, 'second_in_marked') == grid:
            findings.append('canonical rule must change the fourth panel')
        if solve(grid, 'second_in_marked') == solve(grid, 'third_in_marked'):
            findings.append('settings must be distinguishable')
        if len(info['panels']) != 4:
            findings.append('expected four panels')
    except Exception as exc:  # pragma: no cover - defensive generator boundary
        findings.append(str(exc))
    return findings


def generate(seed: int, sample_index: int, difficulty: str = 'medium') -> dict[str, Grid]:
    """Ordinary base-generator API exercised by authoring preflight."""
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('seed outside exact bounds')
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError('sample_index must be a nonnegative integer')
    grid = _scene(seed, sample_index % 4, query=True)
    return {'input': grid}

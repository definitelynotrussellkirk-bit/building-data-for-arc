from collections import Counter


def _split_frames(grid):
    """Split a film-strip grid on full-width monochrome separator rows."""
    separators = [
        r for r, row in enumerate(grid)
        if row and len(set(row)) == 1 and row[0] != 0
    ]
    if not separators:
        return [grid]

    frames = []
    start = 0
    for r in separators:
        if r > start:
            frames.append([row[:] for row in grid[start:r]])
        start = r + 1
    if start < len(grid):
        frames.append([row[:] for row in grid[start:]])
    return frames


def _growth_step(frames):
    """Extrapolate a one-column-at-a-time recolouring process."""
    transitions = []
    for before, after in zip(frames, frames[1:]):
        changes = []
        for r in range(len(before)):
            for c in range(len(before[0])):
                if before[r][c] != after[r][c]:
                    changes.append((r, c, before[r][c], after[r][c]))
        if not changes:
            return None
        cols = {c for _, c, _, _ in changes}
        pairs = {(old, new) for _, _, old, new in changes}
        if len(cols) != 1 or len(pairs) != 1:
            return None
        old, new = next(iter(pairs))
        transitions.append((next(iter(cols)), old, new))

    columns = [item[0] for item in transitions]
    if len(columns) < 2:
        return None
    step = columns[-1] - columns[-2]
    if step == 0 or any(b - a != step for a, b in zip(columns, columns[1:])):
        return None
    old_new = {(old, new) for _, old, new in transitions}
    if len(old_new) != 1:
        return None

    old, new = next(iter(old_new))
    target_col = columns[-1] + step
    h, w = len(frames[-1]), len(frames[-1][0])
    if not (0 <= target_col < w):
        return None
    result = [row[:] for row in frames[-1]]
    changed = False
    for r in range(h):
        if result[r][target_col] == old:
            result[r][target_col] = new
            changed = True
    return result if changed else None


def _translation_step(frames):
    """Extrapolate a compact foreground object's constant translation."""
    background = Counter(v for frame in frames for row in frame for v in row).most_common(1)[0][0]

    def foreground(frame):
        return [(r, c, frame[r][c]) for r in range(len(frame)) for c in range(len(frame[0])) if frame[r][c] != background]

    objects = [foreground(frame) for frame in frames]
    if any(not obj for obj in objects):
        return None

    anchors = [(min(r for r, _, _ in obj), min(c for _, c, _ in obj)) for obj in objects]
    deltas = [(r2 - r1, c2 - c1) for (r1, c1), (r2, c2) in zip(anchors, anchors[1:])]
    if not deltas or len(set(deltas)) != 1:
        return None
    dr, dc = deltas[0]

    normalized = []
    for obj, (ar, ac) in zip(objects, anchors):
        normalized.append(sorted((r - ar, c - ac, value) for r, c, value in obj))
    if len({tuple(shape) for shape in normalized}) != 1:
        return None

    h, w = len(frames[-1]), len(frames[-1][0])
    result = [[background for _ in range(w)] for _ in range(h)]
    for r, c, value in objects[-1]:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < h and 0 <= nc < w):
            return None
        result[nr][nc] = value
    return result


def solve(grid):
    frames = _split_frames(grid)
    if len(frames) < 2 or len({(len(f), len(f[0])) for f in frames}) != 1:
        raise ValueError("expected an equal-sized sequence of frames")

    result = _growth_step(frames)
    if result is not None:
        return result

    result = _translation_step(frames)
    if result is not None:
        return result

    raise ValueError("sequence is neither a supported growth nor translation pattern")

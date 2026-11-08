from __future__ import annotations


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col),
                             (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _corner(component: set[tuple[int, int]]):
    """Return (orientation, top, bottom, left, right), or None."""
    if len(component) != 3:
        return None
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    if bottom - top != 1 or right - left != 1:
        return None

    square = {
        (top, left), (top, right),
        (bottom, left), (bottom, right),
    }
    missing = square - component
    if len(missing) != 1:
        return None
    missing_cell = next(iter(missing))
    orientation = {
        (bottom, right): "TL",
        (bottom, left): "TR",
        (top, right): "BL",
        (top, left): "BR",
    }[missing_cell]
    return orientation, top, bottom, left, right


def _find_frames(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    marker_cells = {
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value not in (0, 1)
    }
    corners = []
    for index, component in enumerate(_components(marker_cells)):
        parsed = _corner(component)
        if parsed is not None:
            corners.append((index, *parsed))

    by_orientation: dict[str, list[tuple[int, int, int, int, int]]] = {
        "TL": [], "TR": [], "BL": [], "BR": []
    }
    for index, orientation, top, bottom, left, right in corners:
        by_orientation[orientation].append((index, top, bottom, left, right))

    candidates: list[tuple[tuple[int, int, int, int], frozenset[int]]] = []
    for tl in by_orientation["TL"]:
        tl_id, top, _, left, _ = tl
        for tr in by_orientation["TR"]:
            tr_id, tr_top, _, _, right = tr
            if tr_top != top or right <= left:
                continue
            for bl in by_orientation["BL"]:
                bl_id, _, bottom, bl_left, _ = bl
                if bl_left != left or bottom <= top:
                    continue
                for br in by_orientation["BR"]:
                    br_id, _, br_bottom, _, br_right = br
                    if br_bottom == bottom and br_right == right:
                        candidates.append(
                            ((top, bottom, left, right),
                             frozenset((tl_id, tr_id, bl_id, br_id)))
                        )

    # Normally the corner matching is unique.  The small set-packing step also
    # protects against accidental row/column alignments between separate frames.
    best_frames: list[tuple[int, int, int, int]] = []
    best_key = (-1, float("inf"))

    def search(position: int, used: frozenset[int], chosen: list[tuple[int, int, int, int]], area: int):
        nonlocal best_frames, best_key
        key = (len(used), area)
        if key[0] > best_key[0] or (key[0] == best_key[0] and key[1] < best_key[1]):
            best_key = key
            best_frames = list(chosen)
        for candidate_index in range(position, len(candidates)):
            frame, ids = candidates[candidate_index]
            if used.isdisjoint(ids):
                top, bottom, left, right = frame
                search(
                    candidate_index + 1,
                    used | ids,
                    chosen + [frame],
                    area + (bottom - top + 1) * (right - left + 1),
                )

    search(0, frozenset(), [], 0)
    return sorted(best_frames)


def _axis_score(
    frames: list[tuple[int, int, int, int]],
    ones_by_frame: list[set[tuple[int, int]]],
    axis: str,
) -> tuple[int, int, int]:
    crossing_frames = 0
    paired_nonfixed = 0
    new_cells = 0

    for (top, bottom, left, right), ones in zip(frames, ones_by_frame):
        signs: set[int] = set()
        reflected: set[tuple[int, int]] = set()
        for row, col in ones:
            if axis == "vertical":
                delta = 2 * row - (top + bottom)
                reflected_cell = (top + bottom - row, col)
            else:
                delta = 2 * col - (left + right)
                reflected_cell = (row, left + right - col)
            if delta < 0:
                signs.add(-1)
            elif delta > 0:
                signs.add(1)
            reflected.add(reflected_cell)

        if -1 in signs and 1 in signs:
            crossing_frames += 1
        paired_nonfixed += sum(
            1 for cell in ones
            if cell in reflected and (
                (axis == "vertical" and 2 * cell[0] != top + bottom)
                or (axis == "horizontal" and 2 * cell[1] != left + right)
            )
        )
        new_cells += len(reflected - ones)

    # A source motif should occupy one side of the intended mirror.  Prefer the
    # axis with no cross-axis motif, then the least pre-existing mirrored pairs,
    # then the largest genuinely added copy.
    return crossing_frames, paired_nonfixed, -new_cells


def solve(grid: list[list[int]]) -> list[list[int]]:
    frames = _find_frames(grid)
    if not frames:
        return [row[:] for row in grid]

    ones_by_frame: list[set[tuple[int, int]]] = []
    for top, bottom, left, right in frames:
        ones_by_frame.append({
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if grid[row][col] == 1
        })

    axis = min(
        ("vertical", "horizontal"),
        key=lambda candidate: _axis_score(frames, ones_by_frame, candidate),
    )

    output = [[0 if value == 1 else value for value in row] for row in grid]
    for (top, bottom, left, right), ones in zip(frames, ones_by_frame):
        for row, col in ones:
            output[row][col] = 1
            if axis == "vertical":
                output[top + bottom - row][col] = 1
            else:
                output[row][left + right - col] = 1
    return output

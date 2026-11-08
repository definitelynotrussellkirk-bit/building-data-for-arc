"""Reusable ARC generator primitives.

These helpers are intentionally small and policy-explicit. They provide a
shared vocabulary for generators and experiments without committing to a single
solver strategy.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, Sequence

Grid = list[list[int]]
Cell = int | None
PartialGrid = list[list[Cell]]
Position = tuple[int, int]
BBox = tuple[int, int, int, int]
Delta = tuple[int, int]


@dataclass(frozen=True)
class Object:
    """Connected component with cached geometry."""

    color: int | None
    cells: frozenset[Position]
    bbox: BBox

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def bbox_area(self) -> int:
        r1, c1, r2, c2 = self.bbox
        return (r2 - r1 + 1) * (c2 - c1 + 1)


@dataclass(frozen=True)
class Region:
    """Background region with border-contact metadata."""

    cells: frozenset[Position]
    bbox: BBox
    touches_border: bool

    @property
    def size(self) -> int:
        return len(self.cells)


@dataclass(frozen=True)
class RayStep:
    """One cell visited by a raycast."""

    position: Position
    value: int
    steps: int


def clone_grid(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def shape(grid: Sequence[Sequence[Any]]) -> tuple[int, int]:
    return (len(grid), len(grid[0]) if grid else 0)


def in_bounds(grid: Sequence[Sequence[Any]], row: int, col: int) -> bool:
    h, w = shape(grid)
    return 0 <= row < h and 0 <= col < w


def blank_grid(height: int, width: int, fill: int = 0) -> Grid:
    return [[fill for _ in range(width)] for _ in range(height)]


def background_color(
    grid: Grid,
    policy: Literal["zero", "mode", "corner"] = "zero",
    tie: Literal["lowest", "first", "error"] = "lowest",
) -> int:
    """Choose a background color using an explicit policy."""

    if policy == "zero":
        return 0

    values: list[int]
    if policy == "mode":
        values = [value for row in grid for value in row]
    elif policy == "corner":
        h, w = shape(grid)
        if h == 0 or w == 0:
            return 0
        values = [grid[0][0], grid[0][w - 1], grid[h - 1][0], grid[h - 1][w - 1]]
    else:
        raise ValueError(f"unknown background policy: {policy}")

    if not values:
        return 0

    counts = Counter(values)
    best_count = max(counts.values())
    tied = [value for value, count in counts.items() if count == best_count]
    if len(tied) == 1:
        return tied[0]
    if tie == "lowest":
        return min(tied)
    if tie == "first":
        return next(value for value in values if value in tied)
    if tie == "error":
        raise ValueError(f"background color tie: {sorted(tied)}")
    raise ValueError(f"unknown tie policy: {tie}")


def nonzero_colors(grid: Grid, background: int = 0) -> set[int]:
    return {
        value
        for row in grid
        for value in row
        if value != background
    }


def mask_color(grid: Grid, color: int) -> set[Position]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }


def positions_from_mask(mask: Iterable[Position] | Sequence[Sequence[Any]]) -> set[Position]:
    """Accept either a position iterable or a same-shape truthy mask grid."""

    if isinstance(mask, set):
        return set(mask)

    items = list(mask)
    if not items:
        return set()

    first = items[0]
    if isinstance(first, tuple) and len(first) == 2:
        return {(int(row), int(col)) for row, col in items}

    return {
        (row, col)
        for row, values in enumerate(items)
        for col, value in enumerate(values)
        if value
    }


def bbox_of_mask(mask: Iterable[Position] | Sequence[Sequence[Any]]) -> BBox | None:
    positions = positions_from_mask(mask)
    if not positions:
        return None
    return (
        min(row for row, _ in positions),
        min(col for _, col in positions),
        max(row for row, _ in positions),
        max(col for _, col in positions),
    )


def _neighbors(row: int, col: int, connectivity: Literal[4, 8] = 4) -> Iterable[Position]:
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        deltas.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
    for dr, dc in deltas:
        yield row + dr, col + dc


def components4(
    grid: Grid,
    background: int = 0,
    match_colors: bool = True,
) -> list[Object]:
    """Return 4-connected non-background components.

    By default, adjacent cells are connected only when they have the same
    color. Set `match_colors=False` to group all non-background adjacency.
    """

    h, w = shape(grid)
    seen: set[Position] = set()
    objects: list[Object] = []

    for start_row in range(h):
        for start_col in range(w):
            if (start_row, start_col) in seen or grid[start_row][start_col] == background:
                continue

            color = grid[start_row][start_col]
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: set[Position] = set()

            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for nr, nc in _neighbors(row, col, 4):
                    if not in_bounds(grid, nr, nc) or (nr, nc) in seen:
                        continue
                    if grid[nr][nc] == background:
                        continue
                    if match_colors and grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))

            bbox = bbox_of_mask(cells)
            if bbox is not None:
                objects.append(Object(color if match_colors else None, frozenset(cells), bbox))

    return objects


def select_color_by_rank(
    grid: Grid,
    rank: int = 0,
    background: int = 0,
    largest: bool = True,
    tie: Literal["numeric", "first", "error"] = "numeric",
) -> int | None:
    """Select a color by frequency rank, excluding `background`."""

    values = [
        value
        for row in grid
        for value in row
        if value != background
    ]
    if not values:
        return None

    counts = Counter(values)
    grouped: dict[int, list[int]] = {}
    for color, count in counts.items():
        grouped.setdefault(count, []).append(color)

    count_order = sorted(grouped, reverse=largest)
    if rank < 0 or rank >= len(count_order):
        return None

    tied = grouped[count_order[rank]]
    if len(tied) == 1:
        return tied[0]
    if tie == "numeric":
        return min(tied)
    if tie == "first":
        return next(value for value in values if value in tied)
    if tie == "error":
        raise ValueError(f"color-rank tie: {sorted(tied)}")
    raise ValueError(f"unknown tie policy: {tie}")


def _object_metric(obj: Object, key: str | Callable[[Object], Any]) -> Any:
    if callable(key):
        return key(obj)
    if key == "size":
        return obj.size
    if key == "bbox_area":
        return obj.bbox_area
    if key == "top":
        return obj.bbox[0]
    if key == "left":
        return obj.bbox[1]
    if key == "color":
        return -1 if obj.color is None else obj.color
    raise ValueError(f"unknown object selection key: {key}")


def select_object(
    objects: Sequence[Object],
    key: str | Callable[[Object], Any] = "size",
    largest: bool = True,
    index: int = 0,
    tie: Literal["reading_order", "color", "error"] = "reading_order",
) -> Object | None:
    """Select an object by metric with an explicit tie policy."""

    if not objects:
        return None

    def tie_key(obj: Object) -> tuple[Any, ...]:
        if tie == "color":
            return (-1 if obj.color is None else obj.color, obj.bbox[0], obj.bbox[1])
        if tie in ("reading_order", "error"):
            return (obj.bbox[0], obj.bbox[1], -1 if obj.color is None else obj.color)
        raise ValueError(f"unknown tie policy: {tie}")

    metric_pairs = [(_object_metric(obj, key), obj) for obj in objects]
    metric_order: list[Any] = []
    for metric, _ in sorted(metric_pairs, key=lambda item: item[0], reverse=largest):
        if not any(metric == seen for seen in metric_order):
            metric_order.append(metric)

    best_metric = metric_order[0]
    tied = [obj for metric, obj in metric_pairs if metric == best_metric]
    if len(tied) > 1 and tie == "error":
        raise ValueError(f"object selection tie on {key}: {len(tied)} candidates")

    ranked: list[Object] = []
    for metric in metric_order:
        ranked.extend(sorted(
            [obj for candidate_metric, obj in metric_pairs if candidate_metric == metric],
            key=tie_key,
        ))
    if index < 0 or index >= len(ranked):
        return None
    return ranked[index]


def crop_bbox(grid: Grid, bbox: BBox) -> Grid:
    r1, c1, r2, c2 = bbox
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def overlay(
    base: Grid | PartialGrid,
    top: Grid | PartialGrid,
    transparent: int | None = 0,
) -> PartialGrid:
    """Overlay `top` on `base`; transparent or unknown top cells pass through."""

    if shape(base) != shape(top):
        raise ValueError(f"overlay shape mismatch: {shape(base)} != {shape(top)}")

    out: PartialGrid = []
    for base_row, top_row in zip(base, top):
        out_row: list[Cell] = []
        for base_value, top_value in zip(base_row, top_row):
            if top_value is None or top_value == transparent:
                out_row.append(base_value)
            else:
                out_row.append(top_value)
        out.append(out_row)
    return out


def translate_layer(
    layer: Grid,
    delta: Delta,
    background: int = 0,
    transparent: int = 0,
    output_shape: tuple[int, int] | None = None,
    clip: bool = True,
) -> Grid:
    """Translate non-transparent cells onto a blank canvas."""

    h, w = output_shape or shape(layer)
    out = blank_grid(h, w, background)
    dr, dc = delta

    for row, values in enumerate(layer):
        for col, value in enumerate(values):
            if value == transparent:
                continue
            nr, nc = row + dr, col + dc
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = value
            elif not clip:
                raise ValueError(f"translated cell out of bounds: {(nr, nc)}")

    return out


def _selector_positions(
    grid: Grid,
    selector: int | Object | Iterable[Position] | Callable[[int, int, int], bool],
) -> set[Position]:
    if isinstance(selector, Object):
        return set(selector.cells)
    if isinstance(selector, int):
        return mask_color(grid, selector)
    if callable(selector):
        return {
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if selector(row, col, value)
        }
    return positions_from_mask(selector)


def slide_layer(
    scene: Grid,
    selector: int | Object | Iterable[Position] | Callable[[int, int, int], bool],
    delta: Delta,
    vacated: Literal["background", "preserve-scene", "unknown", "inpaint-symmetry", "inpaint-period"] = "background",
    collision: Literal["overwrite", "block", "merge", "error"] = "overwrite",
    background: int = 0,
    underlay: Grid | None = None,
    unknown_value: Cell = None,
    clip: bool = True,
    merge: Callable[[Cell, int], Cell] | None = None,
) -> PartialGrid:
    """Move a selected layer inside a scene with explicit erase/collision policy."""

    h, w = shape(scene)
    selected = _selector_positions(scene, selector)
    moving = [(row, col, scene[row][col]) for row, col in sorted(selected)]
    dr, dc = delta

    destinations: list[tuple[int, int, int]] = []
    out_of_bounds = False
    collisions: list[Position] = []

    for row, col, value in moving:
        nr, nc = row + dr, col + dc
        if not (0 <= nr < h and 0 <= nc < w):
            out_of_bounds = True
            if clip:
                continue
            if collision == "block":
                return clone_grid(scene)
            raise ValueError(f"slide destination out of bounds: {(nr, nc)}")
        if (nr, nc) not in selected and scene[nr][nc] != background:
            collisions.append((nr, nc))
        destinations.append((nr, nc, value))

    if collisions:
        if collision == "error":
            raise ValueError(f"slide collision at {collisions}")
        if collision == "block":
            return clone_grid(scene)

    if out_of_bounds and not clip and collision == "block":
        return clone_grid(scene)

    out: PartialGrid = clone_grid(scene)
    for row, col, _ in moving:
        if vacated == "background":
            out[row][col] = background
        elif vacated == "preserve-scene":
            out[row][col] = underlay[row][col] if underlay is not None else background
        elif vacated in ("unknown", "inpaint-symmetry", "inpaint-period"):
            out[row][col] = unknown_value
        else:
            raise ValueError(f"unknown vacated policy: {vacated}")

    for nr, nc, value in destinations:
        if collision == "merge" and merge is not None:
            out[nr][nc] = merge(out[nr][nc], value)
        else:
            out[nr][nc] = value

    return out


def move_content_to_edge(
    grid: Grid,
    vertical: Literal["top", "bottom"] | None = None,
    horizontal: Literal["left", "right"] | None = None,
    background: int = 0,
) -> Grid:
    mask = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != background
    }
    bbox = bbox_of_mask(mask)
    if bbox is None:
        return clone_grid(grid)

    h, w = shape(grid)
    r1, c1, r2, c2 = bbox
    dr = 0
    dc = 0
    if vertical == "top":
        dr = -r1
    elif vertical == "bottom":
        dr = h - 1 - r2
    elif vertical is not None:
        raise ValueError(f"unknown vertical edge: {vertical}")

    if horizontal == "left":
        dc = -c1
    elif horizontal == "right":
        dc = w - 1 - c2
    elif horizontal is not None:
        raise ValueError(f"unknown horizontal edge: {horizontal}")

    return translate_layer(grid, (dr, dc), background=background, transparent=background)


def _transpose(grid: Grid) -> Grid:
    if not grid:
        return []
    return [list(row) for row in zip(*grid)]


def _separator_indexes(
    grid: Grid,
    axis: Literal["rows", "cols"],
    separator_color: int | None = None,
    background: int = 0,
    predicate: Callable[[list[int], int], bool] | None = None,
) -> list[int]:
    lines = grid if axis == "rows" else _transpose(grid)
    indexes: list[int] = []
    for idx, line in enumerate(lines):
        if predicate is not None:
            if predicate(line, idx):
                indexes.append(idx)
        elif separator_color is not None:
            if line and all(value == separator_color for value in line):
                indexes.append(idx)
        elif line and all(value == line[0] for value in line) and line[0] != background:
            indexes.append(idx)
    return indexes


def _ranges_between_separators(length: int, separators: Sequence[int]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    start = 0
    for sep in sorted(separators):
        if start < sep:
            ranges.append((start, sep))
        start = sep + 1
    if start < length:
        ranges.append((start, length))
    return ranges


def split_by_separators(
    grid: Grid,
    axis: Literal["rows", "cols"],
    separators: Sequence[int] | None = None,
    separator_color: int | None = None,
    background: int = 0,
    predicate: Callable[[list[int], int], bool] | None = None,
) -> list[Grid]:
    """Split a grid into panels, excluding separator rows or columns."""

    if axis not in ("rows", "cols"):
        raise ValueError("axis must be 'rows' or 'cols'")

    if axis == "cols":
        return [
            _transpose(panel)
            for panel in split_by_separators(
                _transpose(grid),
                "rows",
                separators=separators,
                separator_color=separator_color,
                background=background,
                predicate=predicate,
            )
        ]

    sep_indexes = list(separators) if separators is not None else _separator_indexes(
        grid,
        "rows",
        separator_color=separator_color,
        background=background,
        predicate=predicate,
    )
    ranges = _ranges_between_separators(len(grid), sep_indexes)
    return [[row[:] for row in grid[start:end]] for start, end in ranges]


def take_panel(
    grid: Grid,
    row_index: int = 0,
    col_index: int = 0,
    row_separators: Sequence[int] | None = None,
    col_separators: Sequence[int] | None = None,
    separator_color: int | None = None,
    background: int = 0,
) -> Grid:
    row_panels = split_by_separators(
        grid,
        "rows",
        separators=row_separators,
        separator_color=separator_color,
        background=background,
    )
    if row_index < 0 or row_index >= len(row_panels):
        raise IndexError(f"row panel out of range: {row_index}")

    col_panels = split_by_separators(
        row_panels[row_index],
        "cols",
        separators=col_separators,
        separator_color=separator_color,
        background=background,
    )
    if col_index < 0 or col_index >= len(col_panels):
        raise IndexError(f"col panel out of range: {col_index}")
    return col_panels[col_index]


def zip_panels(
    left: Grid,
    right: Grid,
    op: Literal["or", "and", "xor", "difference"] = "or",
    background: int = 0,
    color: int | None = None,
) -> Grid:
    if shape(left) != shape(right):
        raise ValueError(f"panel shape mismatch: {shape(left)} != {shape(right)}")

    out = blank_grid(*shape(left), fill=background)
    for row, (left_row, right_row) in enumerate(zip(left, right)):
        for col, (a, b) in enumerate(zip(left_row, right_row)):
            a_on = a != background
            b_on = b != background
            if op == "or":
                out[row][col] = a if a_on else b
            elif op == "and":
                out[row][col] = (color if color is not None else a) if a_on and b_on else background
            elif op == "xor":
                out[row][col] = a if a_on and not b_on else b if b_on and not a_on else background
            elif op == "difference":
                out[row][col] = a if a_on and not b_on else background
            else:
                raise ValueError(f"unknown panel zip op: {op}")
    return out


def raycast(
    grid: Grid,
    start: Position,
    direction: Delta,
    blockers: set[int] | None = None,
    include_start: bool = False,
    max_steps: int | None = None,
) -> list[RayStep]:
    """Walk a ray until it exits, reaches `max_steps`, or hits a blocker."""

    dr, dc = direction
    if dr == 0 and dc == 0:
        raise ValueError("raycast direction cannot be zero")

    row, col = start
    if not include_start:
        row += dr
        col += dc

    steps: list[RayStep] = []
    step_count = 0
    while in_bounds(grid, row, col):
        value = grid[row][col]
        steps.append(RayStep((row, col), value, step_count + 1))
        if blockers is not None and value in blockers:
            break
        step_count += 1
        if max_steps is not None and step_count >= max_steps:
            break
        row += dr
        col += dc

    return steps


def _region_from_cells(grid: Grid, cells: set[Position]) -> Region:
    bbox = bbox_of_mask(cells)
    if bbox is None:
        raise ValueError("cannot build region from empty cells")
    h, w = shape(grid)
    touches_border = any(row in (0, h - 1) or col in (0, w - 1) for row, col in cells)
    return Region(frozenset(cells), bbox, touches_border)


def background_regions(
    grid: Grid,
    background: int = 0,
    connectivity: Literal[4, 8] = 4,
) -> list[Region]:
    h, w = shape(grid)
    seen: set[Position] = set()
    regions: list[Region] = []

    for start_row in range(h):
        for start_col in range(w):
            if (start_row, start_col) in seen or grid[start_row][start_col] != background:
                continue

            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells: set[Position] = set()

            while queue:
                row, col = queue.popleft()
                cells.add((row, col))
                for nr, nc in _neighbors(row, col, connectivity):
                    if not in_bounds(grid, nr, nc) or (nr, nc) in seen:
                        continue
                    if grid[nr][nc] != background:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))

            regions.append(_region_from_cells(grid, cells))

    return regions


def enclosed_regions(
    grid: Grid,
    background: int = 0,
    connectivity: Literal[4, 8] = 4,
) -> list[Region]:
    return [
        region
        for region in background_regions(grid, background=background, connectivity=connectivity)
        if not region.touches_border
    ]


def _period_ok(
    grid: Grid,
    row_period: int,
    col_period: int,
    wildcard: int | None,
) -> bool:
    h, w = shape(grid)
    for row in range(h):
        for col in range(w):
            value = grid[row][col]
            anchor = grid[row % row_period][col % col_period]
            if wildcard is not None and (value == wildcard or anchor == wildcard):
                continue
            if value != anchor:
                return False
    return True


def detect_period(
    grid: Grid,
    axis: Literal["rows", "cols", "both"] = "both",
    max_period: int | None = None,
    wildcard: int | None = None,
) -> int | tuple[int, int] | None:
    """Detect the smallest exact row/column period, optionally ignoring holes."""

    h, w = shape(grid)
    if h == 0 or w == 0:
        return None

    max_row = min(max_period or h, h)
    max_col = min(max_period or w, w)

    row_period = next((
        period for period in range(1, max_row + 1)
        if _period_ok(grid, period, w, wildcard)
    ), None)
    col_period = next((
        period for period in range(1, max_col + 1)
        if _period_ok(grid, h, period, wildcard)
    ), None)

    if axis == "rows":
        return row_period
    if axis == "cols":
        return col_period
    if axis == "both":
        if row_period is None or col_period is None:
            return None
        return (row_period, col_period)
    raise ValueError("axis must be 'rows', 'cols', or 'both'")


def _choose_value(values: list[int], tie: Literal["mode", "first", "error"]) -> int | None:
    if not values:
        return None
    if tie == "first":
        return values[0]

    counts = Counter(values)
    best_count = max(counts.values())
    tied = [value for value, count in counts.items() if count == best_count]
    if len(tied) == 1:
        return tied[0]
    if tie == "mode":
        return min(tied)
    if tie == "error":
        raise ValueError(f"value tie: {sorted(tied)}")
    raise ValueError(f"unknown tie policy: {tie}")


def _symmetry_peer(row: int, col: int, h: int, w: int, symmetry: str) -> Position:
    if symmetry == "lr":
        return (row, w - 1 - col)
    if symmetry == "ud":
        return (h - 1 - row, col)
    if symmetry == "rot180":
        return (h - 1 - row, w - 1 - col)
    if symmetry == "transpose":
        return (col, row)
    raise ValueError(f"unknown symmetry: {symmetry}")


def complete_by_symmetry(
    grid: Grid,
    symmetry: Literal["lr", "ud", "rot180", "transpose"] = "lr",
    unknown: int = 0,
    tie: Literal["first", "mode", "error"] = "first",
) -> Grid:
    """Fill unknown cells from their symmetric counterpart when available."""

    h, w = shape(grid)
    if symmetry == "transpose" and h != w:
        raise ValueError("transpose symmetry requires a square grid")

    out = clone_grid(grid)
    for row in range(h):
        for col in range(w):
            if grid[row][col] != unknown:
                continue
            pr, pc = _symmetry_peer(row, col, h, w, symmetry)
            peer = grid[pr][pc]
            if peer != unknown:
                chosen = _choose_value([peer], tie)
                if chosen is not None:
                    out[row][col] = chosen
    return out


def fill_periodic_holes(
    grid: Grid,
    row_period: int,
    col_period: int,
    hole: int = 0,
    tie: Literal["mode", "first", "error"] = "mode",
) -> Grid:
    """Fill hole cells from observed cells with the same period phase."""

    if row_period <= 0 or col_period <= 0:
        raise ValueError("periods must be positive")

    h, w = shape(grid)
    phase_values: dict[tuple[int, int], list[int]] = {}
    for row in range(h):
        for col in range(w):
            value = grid[row][col]
            if value == hole:
                continue
            phase_values.setdefault((row % row_period, col % col_period), []).append(value)

    out = clone_grid(grid)
    for row in range(h):
        for col in range(w):
            if out[row][col] != hole:
                continue
            chosen = _choose_value(phase_values.get((row % row_period, col % col_period), []), tie)
            if chosen is not None:
                out[row][col] = chosen
    return out


def best_candidate(
    candidates: Sequence[Any],
    score: Callable[[Any], Any],
    largest: bool = False,
    tie: Literal["first", "last", "error"] = "error",
) -> Any:
    """Return the best-scoring candidate with explicit tie behavior."""

    if not candidates:
        raise ValueError("no candidates")

    scored = [(score(candidate), idx, candidate) for idx, candidate in enumerate(candidates)]
    best_score = max(item[0] for item in scored) if largest else min(item[0] for item in scored)
    tied = [item for item in scored if item[0] == best_score]
    if len(tied) == 1 or tie == "first":
        return tied[0][2]
    if tie == "last":
        return tied[-1][2]
    if tie == "error":
        raise ValueError(f"candidate score tie: {best_score!r}")
    raise ValueError(f"unknown tie policy: {tie}")


def unique_or_reject(
    candidates: Sequence[Any],
    key: Callable[[Any], Any] | None = None,
) -> Any:
    """Return the only candidate, or the first if all candidates are equivalent."""

    if not candidates:
        raise ValueError("no candidates")
    if key is None:
        key = lambda candidate: candidate

    keys = [key(candidate) for candidate in candidates]
    first_key = keys[0]
    if all(candidate_key == first_key for candidate_key in keys):
        return candidates[0]
    unique_keys: list[Any] = []
    for candidate_key in keys:
        if not any(candidate_key == seen_key for seen_key in unique_keys):
            unique_keys.append(candidate_key)
    raise ValueError(f"expected a unique candidate, got {len(unique_keys)} unique keys")

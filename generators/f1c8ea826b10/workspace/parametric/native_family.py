"""Native chamber-checker phase-anchor family for f1c8ea826b10.

The default setting returns the selected canonical Racket source byte-for-byte.
The alternate setting preserves region discovery and numeric min/max color
selection, but lets the minimum-color marker's input position choose which
checkerboard parity receives that color.

The sampler is independent of the private setting.  It builds one deterministic
six-demonstration/four-query plan and returns prefixes, so a one-query first turn
is byte-identical to the first turn of a four-query lesson.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import random
from pathlib import Path


HOME = Path(__file__).resolve().parent
SETTINGS = (
    {"phase_anchor": "bbox_top_left"},
    {"phase_anchor": "minimum_marker"},
)
DEFAULT = {"phase_anchor": "bbox_top_left"}
COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

# (row heights, column widths).  Query four naturally extends one chamber
# dimension to seven so the separate parametric grammar reaches exact 30x30;
# the unchanged production validator tops out at 29x29 (4*6 + 5 walls).
_DEMO_PROFILES = (
    ((2, 3), (3, 4)),                 # 8x10 constructive teaching scene
    ((4, 4), (3, 3, 3)),              # 11x13 second teaching scene
    ((3, 3, 3), (4, 5)),              # 13x12 aspect-ratio transfer
    ((4, 4, 4), (4, 5, 5)),           # 16x18 blockers and offsets
    ((5, 5, 6), (5, 6, 6)),           # 20x21 denser lesson
    ((5, 5, 5, 4), (5, 5, 5, 5)),     # 24x25 maximum demo count
)
_QUERY_PROFILES = (
    ((3, 3), (4, 4)),                 # 9x11 ordinary transfer
    ((4, 3, 4), (4, 4, 5)),           # 15x17 different lattice topology
    ((4, 5, 5, 4), (5, 6, 5, 6)),     # 23x27 boundary/blocker case
    ((7, 6, 6, 6), (7, 6, 6, 6)),     # exact 30x30 substantive stress
)
_PAIR_PALETTES = ((1, 8), (2, 9), (3, 6), (4, 7))
_TRIPLE_PALETTES = ((1, 4, 9), (2, 6, 8), (3, 7, 9), (1, 6, 8))


def _phase_anchor(settings: dict) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"phase_anchor"}
        or type(settings["phase_anchor"]) is not str
        or settings["phase_anchor"] not in ("bbox_top_left", "minimum_marker")
    ):
        raise ValueError(
            "settings require phase_anchor=bbox_top_left|minimum_marker"
        )
    return settings["phase_anchor"]


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid dimensions must lie in 1..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with literal ARC colors 0..9")
    return deepcopy(grid)


def _regions(grid: list[list[int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 5
    }
    regions: list[tuple[tuple[int, int], ...]] = []
    while remaining:
        start = min(remaining)
        pending = [start]
        region: set[tuple[int, int]] = set()
        while pending:
            row, col = pending.pop()
            if (row, col) in region:
                continue
            region.add((row, col))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = row + dr, col + dc
                if neighbor in remaining and neighbor not in region:
                    pending.append(neighbor)
        remaining.difference_update(region)
        regions.append(tuple(sorted(region)))
    return tuple(regions)


def _transform(
    grid: object,
    *,
    anchor_mode: str,
    palette_mode: str = "min_max",
) -> list[list[int]]:
    source = _grid(grid)
    output = [[5 if value == 5 else 0 for value in row] for row in source]
    for region in _regions(source):
        markers = sorted(
            (row, col, source[row][col])
            for row, col in region
            if source[row][col] not in (0, 5)
        )
        colors = sorted({value for _row, _col, value in markers})
        if not colors:
            fill = 0
            for row, col in region:
                output[row][col] = fill
            continue
        low = colors[0]
        if len(colors) == 1 or palette_mode == "solid_minimum":
            for row, col in region:
                output[row][col] = low
            continue
        high = colors[1] if palette_mode == "two_smallest" else colors[-1]
        top = min(row for row, _col in region)
        left = min(col for _row, col in region)
        if anchor_mode == "bbox_top_left":
            anchor = top, left
        elif anchor_mode == "minimum_marker":
            anchor = next((row, col) for row, col, value in markers if value == low)
        elif anchor_mode == "maximum_marker":
            anchor = next((row, col) for row, col, value in markers if value == colors[-1])
        elif anchor_mode == "row_major_first":
            anchor = markers[0][:2]
        elif anchor_mode == "row_major_last":
            anchor = markers[-1][:2]
        elif anchor_mode == "global_origin":
            anchor = 0, 0
        elif anchor_mode == "flipped_bbox":
            anchor = top, left + 1
        elif anchor_mode == "minimum_value_phase":
            anchor = top, left + (low % 2)
        else:
            raise ValueError(f"unknown anchor mode: {anchor_mode}")
        for row, col in region:
            output[row][col] = (
                low
                if (row - anchor[0] + col - anchor[1]) % 2 == 0
                else high
            )
    return output


def reference(grid: object, settings: dict) -> list[list[int]]:
    return _transform(grid, anchor_mode=_phase_anchor(settings))


_MINIMUM_MARKER_PROGRAM = """(rule!
  (let ((dummy 0))
    (define (chamber-cells start)
      (connected-region g (first start) (second start)
        (lambda (r c v) (not (= v 5)))
        4))
    (define (paint-chamber out region)
      (let* ((colors (sort (remove-duplicates
                             (filter (lambda (v) (and (not (= v 0)) (not (= v 5))))
                                     (map (lambda (p) (at g (first p) (second p))) region)))
                           <))
             (bb (bbox-of-cells region))
             (min-marker
               (if (empty? colors)
                   bb
                   (first
                     (filter
                       (lambda (p) (= (at g (first p) (second p)) (first colors)))
                       region))))
             (anchor (if (empty? colors) bb min-marker)))
        (cond [(empty? colors) (paint-cells out region 0)]
              [(= (length colors) 1) (paint-cells out region (first colors))]
              [else
               (for/fold ([acc out]) ([p (in-list region)])
                 (set-cell acc (first p) (second p)
                           (if (= (modulo (+ (- (first p) (first anchor))
                                               (- (second p) (second anchor))) 2) 0)
                               (first colors)
                               (last colors))))])))
    (let loop ([remaining (filter-cells g (lambda (r c v) (not (= v 5))))]
               [out (keep-only g 5)])
      (if (empty? remaining)
          out
          (let ((region (chamber-cells (first remaining))))
            (loop (filter (lambda (p) (not (member? p region))) remaining)
                  (paint-chamber out region)))))))"""


def program(settings: dict) -> str:
    mode = _phase_anchor(settings)
    if mode == "bbox_top_left":
        return (HOME / "canonical.rkt").read_text(encoding="utf-8")
    return _MINIMUM_MARKER_PROGRAM


def _stable_rng(seed: int, role: str, index: int) -> random.Random:
    body = f"f1c8ea826b10|phase-anchor-v1|{seed}|{role}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(body).digest()[:16], "big"))


def _lattice(
    row_heights: tuple[int, ...],
    col_widths: tuple[int, ...],
) -> tuple[list[list[int]], tuple[int, ...], tuple[int, ...]]:
    height = sum(row_heights) + len(row_heights) + 1
    width = sum(col_widths) + len(col_widths) + 1
    if height > 30 or width > 30:
        raise ValueError("profile exceeds ARC bounds")
    grid = [[5] * width for _ in range(height)]
    tops: list[int] = []
    cursor = 1
    for size in row_heights:
        tops.append(cursor)
        cursor += size + 1
    lefts: list[int] = []
    cursor = 1
    for size in col_widths:
        lefts.append(cursor)
        cursor += size + 1
    for chamber_row, top in enumerate(tops):
        for chamber_col, left in enumerate(lefts):
            for local_row in range(row_heights[chamber_row]):
                for local_col in range(col_widths[chamber_col]):
                    grid[top + local_row][left + local_col] = 0
    return grid, tuple(tops), tuple(lefts)


def _pick(
    cells: list[tuple[int, int]],
    parity: int,
    *,
    last: bool,
    used: set[tuple[int, int]],
) -> tuple[int, int]:
    candidates = [cell for cell in cells if cell not in used and sum(cell) % 2 == parity]
    if not candidates:
        candidates = [cell for cell in cells if cell not in used]
    if not candidates:
        raise ValueError("chamber has no free marker cell")
    candidates.sort()
    return candidates[-1] if last else candidates[0]


def _palette(
    seed_offset: int,
    scene_index: int,
    chamber_index: int,
    arity: int,
    *,
    min_parity: int | None = None,
) -> tuple[int, ...]:
    offset = seed_offset + scene_index * 3 + chamber_index
    if arity == 1:
        return (COLORS[offset % len(COLORS)],)
    pool = _PAIR_PALETTES if arity == 2 else _TRIPLE_PALETTES
    # The first multi-color chamber is a constructive anti-shortcut witness:
    # marker parity and numeric color parity deliberately disagree.
    if chamber_index % 4 == 0 and min_parity is not None:
        pool = tuple(palette for palette in pool if palette[0] % 2 != min_parity)
    return pool[offset % len(pool)]


def _build_scene(
    seed: int,
    role: str,
    scene_index: int,
    profile: tuple[tuple[int, ...], tuple[int, ...]],
) -> list[list[int]]:
    row_heights, col_widths = profile
    grid, tops, lefts = _lattice(row_heights, col_widths)
    rng = _stable_rng(seed, role, scene_index)
    seed_offset = rng.randrange(10_000)
    chamber_index = 0
    for chamber_row, top in enumerate(tops):
        for chamber_col, left in enumerate(lefts):
            height = row_heights[chamber_row]
            width = col_widths[chamber_col]
            local_cells = [
                (row, col)
                for row in range(height)
                for col in range(width)
            ]
            # An edge/corner blocker retains a single connected non-wall region.
            blocker: tuple[int, int] | None = None
            if height >= 3 and width >= 3 and (seed_offset + scene_index + chamber_index) % 4 == 0:
                blocker = (height - 1, width - 1)
                grid[top + blocker[0]][left + blocker[1]] = 5
            cells = [cell for cell in local_cells if cell != blocker]
            if chamber_index % 5 == 2:
                arity = 1
            elif chamber_index % 4 == 0:
                arity = 3
            else:
                arity = 2
            min_parity = (chamber_index + scene_index) % 2
            colors = _palette(
                seed_offset,
                scene_index,
                chamber_index,
                arity,
                min_parity=min_parity if arity >= 2 else None,
            )
            used: set[tuple[int, int]] = set()
            if arity == 1:
                marker = _pick(
                    cells,
                    (chamber_index + scene_index) % 2,
                    last=(chamber_index + scene_index) % 3 == 0,
                    used=used,
                )
                grid[top + marker[0]][left + marker[1]] = colors[0]
            else:
                min_late = (chamber_index + scene_index) % 3 == 0
                minimum = _pick(cells, min_parity, last=min_late, used=used)
                used.add(minimum)
                max_parity = 1 - min_parity if chamber_index % 2 == 0 else min_parity
                maximum = _pick(cells, max_parity, last=not min_late, used=used)
                used.add(maximum)
                grid[top + minimum[0]][left + minimum[1]] = colors[0]
                grid[top + maximum[0]][left + maximum[1]] = colors[-1]
                if arity == 3:
                    middle = _pick(
                        cells,
                        1 - min_parity,
                        last=(scene_index + chamber_index) % 2 == 0,
                        used=used,
                    )
                    used.add(middle)
                    grid[top + middle[0]][left + middle[1]] = colors[1]
            chamber_index += 1
    return grid


def _plan(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [
        _build_scene(seed, "demo", index, profile)
        for index, profile in enumerate(_DEMO_PROFILES)
    ]
    queries = [
        _build_scene(seed, "query", index, profile)
        for index, profile in enumerate(_QUERY_PROFILES)
    ]
    return demos, queries


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    _phase_anchor(settings)
    demo_inputs, query_inputs = _plan(seed)
    return {
        "train": [
            {"input": deepcopy(grid), "output": reference(grid, settings)}
            for grid in demo_inputs[:demos]
        ],
        "test": [
            {"input": deepcopy(grid), "output": reference(grid, settings)}
            for grid in query_inputs[:queries]
        ],
        "program_solution": program(settings),
        "sampling": {
            "schema": "f1c8ea826b10-phase-anchor-sampling-v1",
            "matched_inputs_across_settings": True,
            "prefix_stable_counts": True,
            "full_demo_count": 6,
            "full_query_count": 4,
        },
    }


def rivals(settings: dict) -> tuple[str, ...]:
    mode = _phase_anchor(settings)
    other = "minimum_marker" if mode == "bbox_top_left" else "bbox_top_left"
    return (
        f"setting:{other}",
        "maximum_marker",
        "row_major_first",
        "row_major_last",
        "global_origin",
        "flipped_bbox",
        "minimum_value_phase",
        "two_smallest",
        "solid_minimum",
    )


def rival_reference(grid: object, settings: dict, name: str) -> list[list[int]]:
    mode = _phase_anchor(settings)
    if name not in rivals(settings):
        raise ValueError("undeclared rival")
    if name.startswith("setting:"):
        return reference(grid, {"phase_anchor": name.split(":", 1)[1]})
    if name in {
        "maximum_marker",
        "row_major_first",
        "row_major_last",
        "global_origin",
        "flipped_bbox",
        "minimum_value_phase",
    }:
        return _transform(grid, anchor_mode=name)
    if name == "two_smallest":
        return _transform(grid, anchor_mode=mode, palette_mode="two_smallest")
    if name == "solid_minimum":
        return _transform(grid, anchor_mode=mode, palette_mode="solid_minimum")
    raise AssertionError(name)



def _variant_program(anchor_mode: str, palette_mode: str = "min_max") -> str:
    anchor = {
        "bbox_top_left": "bb",
        "minimum_marker": "min-marker",
        "maximum_marker": "max-marker",
        "row_major_first": "(first ordered-markers)",
        "row_major_last": "(last ordered-markers)",
        "global_origin": "(list 0 0)",
        "flipped_bbox": "(list (first bb) (+ (second bb) 1))",
        "minimum_value_phase": (
            "(if (empty? colors) bb "
            "(list (first bb) (+ (second bb) (modulo (first colors) 2))))"
        ),
    }.get(anchor_mode)
    if anchor is None:
        raise ValueError(f"unknown anchor mode: {anchor_mode}")
    high = "(second colors)" if palette_mode == "two_smallest" else "(last colors)"
    if palette_mode == "solid_minimum":
        multi = "(paint-cells out region (first colors))"
    elif palette_mode == "min_max" or palette_mode == "two_smallest":
        multi = f"""(for/fold ([acc out]) ([p (in-list region)])
                 (set-cell acc (first p) (second p)
                           (if (= (modulo (+ (- (first p) (first anchor))
                                               (- (second p) (second anchor))) 2) 0)
                               (first colors)
                               {high})))"""
    else:
        raise ValueError(f"unknown palette mode: {palette_mode}")
    return f"""(rule!
  (let ((dummy 0))
    (define (chamber-cells start)
      (connected-region g (first start) (second start)
        (lambda (r c v) (not (= v 5)))
        4))
    (define (paint-chamber out region)
      (let* ((colors (sort (remove-duplicates
                             (filter (lambda (v) (and (not (= v 0)) (not (= v 5))))
                                     (map (lambda (p) (at g (first p) (second p))) region)))
                           <))
             (bb (bbox-of-cells region))
             (ordered-markers
               (sort
                 (filter (lambda (p) (not (= (at g (first p) (second p)) 0))) region)
                 (lambda (a b)
                   (or (< (first a) (first b))
                       (and (= (first a) (first b)) (< (second a) (second b)))))))
             (min-marker
               (if (empty? colors)
                   bb
                   (first (filter
                     (lambda (p) (= (at g (first p) (second p)) (first colors)))
                     region))))
             (max-marker
               (if (empty? colors)
                   bb
                   (first (filter
                     (lambda (p) (= (at g (first p) (second p)) (last colors)))
                     region))))
             (anchor {anchor}))
        (cond [(empty? colors) (paint-cells out region 0)]
              [(= (length colors) 1) (paint-cells out region (first colors))]
              [else {multi}])))
    (let loop ([remaining (filter-cells g (lambda (r c v) (not (= v 5))))]
               [out (keep-only g 5)])
      (if (empty? remaining)
          out
          (let ((region (chamber-cells (first remaining))))
            (loop (filter (lambda (p) (not (member? p region))) remaining)
                  (paint-chamber out region)))))))"""


def rival_program(settings: dict, name: str) -> str:
    mode = _phase_anchor(settings)
    if name not in rivals(settings):
        raise ValueError("undeclared rival")
    if name.startswith("setting:"):
        return program({"phase_anchor": name.split(":", 1)[1]})
    if name in {
        "maximum_marker",
        "row_major_first",
        "row_major_last",
        "global_origin",
        "flipped_bbox",
        "minimum_value_phase",
    }:
        return _variant_program(name)
    if name == "two_smallest":
        return _variant_program(mode, "two_smallest")
    if name == "solid_minimum":
        return _variant_program(mode, "solid_minimum")
    raise AssertionError(name)

def _full_wall_lines(grid: list[list[int]]) -> tuple[list[int], list[int]]:
    rows = [index for index, values in enumerate(grid) if all(value == 5 for value in values)]
    cols = [
        col
        for col in range(len(grid[0]))
        if all(grid[row][col] == 5 for row in range(len(grid)))
    ]
    return rows, cols


def scene_summary(grid: object) -> dict:
    source = _grid(grid)
    regions = _regions(source)
    solid = checker = triples = even = odd = 0
    for region in regions:
        markers = sorted(
            (row, col, source[row][col])
            for row, col in region
            if source[row][col] not in (0, 5)
        )
        colors = sorted({value for _row, _col, value in markers})
        if len(colors) == 1:
            solid += 1
        elif len(colors) >= 2:
            checker += 1
            triples += len(colors) == 3
            top = min(row for row, _col in region)
            left = min(col for _row, col in region)
            row, col, _ = next(item for item in markers if item[2] == colors[0])
            if (row - top + col - left) % 2:
                odd += 1
            else:
                even += 1
    wall_rows, wall_cols = _full_wall_lines(source)
    blocked = 0
    for top, bottom in zip(wall_rows, wall_rows[1:]):
        for left, right in zip(wall_cols, wall_cols[1:]):
            if any(
                source[row][col] == 5
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
            ):
                blocked += 1
    return {
        "shape": [len(source), len(source[0])],
        "regions": len(regions),
        "solid_regions": solid,
        "checker_regions": checker,
        "three_color_regions": triples,
        "blocked_regions": blocked,
        "minimum_marker_even_regions": even,
        "minimum_marker_odd_regions": odd,
    }

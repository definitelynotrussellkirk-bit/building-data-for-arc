"""Generator for ARC task 7d1f7ee8 / content hash d7c15b2e56ec.

Rule: every non-background component adopts the color of the largest connected
component whose bounding box contains it.  Canonical scenes express this with
one or more independent rectangular-frame nesting groups plus occasional
uncontained distractors.
"""
from __future__ import annotations

from dataclasses import dataclass

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "d7c15b2e56ec"
TASK_ID = "d7c15b2e56ec"
VERSION = "2.0.0"
RULE_HASH = "0c27de3a540b"
SUMMARY = (
    "Recolor every nested component to the color of its outermost enclosing "
    "rectangular frame; preserve independent uncontained components."
)

INVARIANTS = [
    "background is color 0",
    "at least one rectangular frame strictly contains another component",
    "each containment group has a unique outermost rectangular frame",
    "at least one contained component initially differs from its outer frame",
    "independent groups and uncontained distractors keep separate color roles",
]

PALETTE_KINDS = ("warm", "cool", "broad")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw over 12..30",
        "valid": "12..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw over 12..30",
        "valid": "12..30",
    },
    "group_count": {
        "type": "int",
        "default": "largest feasible difficulty-aware draw",
        "valid": "1..3",
    },
    "max_depth": {
        "type": "int",
        "default": "largest feasible difficulty-aware draw",
        "valid": "2..4",
    },
    "distractor_count": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "0..3",
    },
    "include_solid": {
        "type": "bool",
        "default": "keyed true|false draw",
        "valid": "false|true",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed palette draw",
        "valid": "warm|cool|broad",
    },
}


@dataclass(frozen=True)
class _Component:
    color: int
    cells: tuple[tuple[int, int], ...]
    bbox: tuple[int, int, int, int]

    @property
    def area(self) -> int:
        r0, c0, r1, c1 = self.bbox
        return (r1 - r0 + 1) * (c1 - c0 + 1)


def _min_outer_size(depth: int) -> int:
    """Minimum square outer frame for ``depth`` levels with blank gaps."""
    return 2 + 4 * (depth - 1)


def _layout_kinds(h: int, w: int, group_count: int, max_depth: int) -> list[str]:
    big = _min_outer_size(max_depth)
    small = _min_outer_size(2)
    usable_h, usable_w = h - 2, w - 2
    if group_count == 1:
        return ["single"] if usable_h >= big and usable_w >= big else []

    kinds: list[str] = []
    if group_count == 2:
        if usable_w >= big + 2 + small and usable_h >= max(big, small):
            kinds.append("vertical2")
        if usable_h >= big + 2 + small and usable_w >= max(big, small):
            kinds.append("horizontal2")
        return kinds

    if group_count == 3:
        if (usable_w >= big + 2 + small
                and usable_h >= max(big, small + 2 + small)):
            kinds.append("vertical3")
        if (usable_h >= big + 2 + small
                and usable_w >= max(big, small + 2 + small)):
            kinds.append("horizontal3")
    return kinds


def _max_feasible_groups(h: int, w: int, depth: int) -> int:
    for count in (3, 2, 1):
        if _layout_kinds(h, w, count, depth):
            return count
    return 0


def _max_feasible_depth(h: int, w: int, group_count: int) -> int:
    for depth in (4, 3, 2):
        if _layout_kinds(h, w, group_count, depth):
            return depth
    return 0


def _requested_min_dimension(overrides: dict) -> int:
    """Raise default canvas size when a single semantic override needs room."""
    group_count = int(overrides.get("group_count", 1))
    max_depth = int(overrides.get("max_depth", 2))
    if group_count not in (1, 2, 3):
        raise ValueError("group_count must be in 1..3")
    if max_depth not in (2, 3, 4):
        raise ValueError("max_depth must be in 2..4")
    big = _min_outer_size(max_depth)
    if group_count == 1:
        return max(12, big + 2)
    if group_count == 2:
        return max(16, big + _min_outer_size(2) + 4)
    return max(16, big + _min_outer_size(2) + 4)


def _split_extra(total: int, rng) -> tuple[int, int]:
    left = rng.randint(0, total)
    return left, total - left


def _slot_layout(h: int, w: int, group_count: int, max_depth: int, rng):
    kinds = _layout_kinds(h, w, group_count, max_depth)
    if not kinds:
        raise ValueError(
            f"cannot fit group_count={group_count}, max_depth={max_depth} "
            f"in {h}x{w}"
        )
    kind = rng.choice(kinds)
    big = _min_outer_size(max_depth)
    small = _min_outer_size(2)
    uh, uw = h - 2, w - 2

    if kind == "single":
        return [(1, 1, h - 2, w - 2)]

    if kind.startswith("vertical"):
        extra_w = uw - (big + 2 + small)
        big_extra, small_extra = _split_extra(extra_w, rng)
        big_w, small_w = big + big_extra, small + small_extra
        big_left = bool(rng.getrandbits(1))
        if big_left:
            big_cols = (1, big_w)
            small_cols = (big_w + 3, w - 2)
        else:
            small_cols = (1, small_w)
            big_cols = (small_w + 3, w - 2)
        if group_count == 2:
            slots = [
                (1, big_cols[0], h - 2, big_cols[1]),
                (1, small_cols[0], h - 2, small_cols[1]),
            ]
        else:
            extra_h = uh - (small + 2 + small)
            top_extra, bottom_extra = _split_extra(extra_h, rng)
            top_h, bottom_h = small + top_extra, small + bottom_extra
            slots = [
                (1, big_cols[0], h - 2, big_cols[1]),
                (1, small_cols[0], top_h, small_cols[1]),
                (top_h + 3, small_cols[0], h - 2, small_cols[1]),
            ]
    else:
        extra_h = uh - (big + 2 + small)
        big_extra, small_extra = _split_extra(extra_h, rng)
        big_h, small_h = big + big_extra, small + small_extra
        big_top = bool(rng.getrandbits(1))
        if big_top:
            big_rows = (1, big_h)
            small_rows = (big_h + 3, h - 2)
        else:
            small_rows = (1, small_h)
            big_rows = (small_h + 3, h - 2)
        if group_count == 2:
            slots = [
                (big_rows[0], 1, big_rows[1], w - 2),
                (small_rows[0], 1, small_rows[1], w - 2),
            ]
        else:
            extra_w = uw - (small + 2 + small)
            left_extra, right_extra = _split_extra(extra_w, rng)
            left_w, right_w = small + left_extra, small + right_extra
            slots = [
                (big_rows[0], 1, big_rows[1], w - 2),
                (small_rows[0], 1, small_rows[1], left_w),
                (small_rows[0], left_w + 3, small_rows[1], w - 2),
            ]

    # The maximum-depth group is always first. Shuffle only the small slots.
    if len(slots) == 3 and rng.getrandbits(1):
        slots[1], slots[2] = slots[2], slots[1]
    return slots


def _choose_bbox(slot, depth: int, rng):
    sr0, sc0, sr1, sc1 = slot
    sh, sw = sr1 - sr0 + 1, sc1 - sc0 + 1
    minimum = _min_outer_size(depth)
    if sh < minimum or sw < minimum:
        raise ValueError(f"slot {slot} cannot support depth {depth}")
    rh = rng.randint(minimum, sh)
    rw = rng.randint(minimum, sw)
    r0 = rng.randint(sr0, sr1 - rh + 1)
    c0 = rng.randint(sc0, sc1 - rw + 1)
    return r0, c0, r0 + rh - 1, c0 + rw - 1


def _child_bbox(parent, min_h: int, min_w: int, rng):
    r0, c0, r1, c1 = parent
    ph, pw = r1 - r0 + 1, c1 - c0 + 1
    max_h, max_w = ph - 4, pw - 4
    if max_h < min_h or max_w < min_w:
        raise ValueError(f"parent {parent} cannot fit child {min_h}x{min_w}")
    ch = rng.randint(min_h, max_h)
    cw = rng.randint(min_w, max_w)
    spare_h, spare_w = ph - ch, pw - cw
    top = rng.randint(2, spare_h - 2)
    left = rng.randint(2, spare_w - 2)
    return r0 + top, c0 + left, r0 + top + ch - 1, c0 + left + cw - 1


def _palette(kind: str, rng) -> list[int]:
    pools = {
        "warm": [2, 3, 4, 6, 9, 1, 5],
        "cool": [1, 5, 7, 8, 2, 4, 9],
        "broad": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    }
    pool = list(pools[kind])
    rng.shuffle(pool)
    return pool


class _Colors:
    def __init__(self, pool: list[int]):
        self.pool = pool
        self.index = 0

    def take(self, *, exclude=()) -> int:
        excluded = set(exclude)
        for offset in range(len(self.pool)):
            color = self.pool[(self.index + offset) % len(self.pool)]
            if color not in excluded:
                self.index += offset + 1
                return color
        raise ValueError("palette cannot satisfy color exclusion")


def _draw_shape(grid, bbox, color: int, kind: str) -> None:
    r0, c0, r1, c1 = bbox
    if kind == "frame":
        draw_frame(grid, r0, c0, r1, c1, color)
    elif kind == "bar":
        for c in range(c0, c1 + 1):
            grid[r0][c] = color
    elif kind == "plus":
        mr, mc = (r0 + r1) // 2, (c0 + c1) // 2
        for r in range(r0, r1 + 1):
            grid[r][mc] = color
        for c in range(c0, c1 + 1):
            grid[mr][c] = color
    else:
        raise ValueError(f"unknown shape kind {kind!r}")


def _is_clear(grid, cells, *, require_zero_neighbors=True) -> bool:
    h, w = len(grid), len(grid[0])
    cell_set = set(cells)
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
            return False
        if require_zero_neighbors:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if (nr, nc) in cell_set:
                    continue
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
                    return False
    return True


def _place_sibling(grid, outer, blocked_bboxes, color: int, rng) -> bool:
    r0, c0, r1, c1 = outer
    candidates = []
    for size in (3, 2):
        for rr in range(r0 + 2, r1 - size + 1):
            for cc in range(c0 + 2, c1 - size + 1):
                bbox = (rr, cc, rr + size - 1, cc + size - 1)
                if any(
                    not (
                        bbox[2] < b[0]
                        or b[2] < bbox[0]
                        or bbox[3] < b[1]
                        or b[3] < bbox[1]
                    )
                    for b in blocked_bboxes[1:]
                ):
                    continue
                cells = [
                    (r, c)
                    for r in range(bbox[0], bbox[2] + 1)
                    for c in range(bbox[1], bbox[3] + 1)
                    if r in (bbox[0], bbox[2]) or c in (bbox[1], bbox[3])
                ]
                if _is_clear(grid, cells):
                    candidates.append((bbox, cells))
    if not candidates:
        return False
    bbox, _ = rng.choice(candidates)
    _draw_shape(grid, bbox, color, "frame")
    return True


def _place_distractor(grid, root_bboxes, color: int, rng, shape_kind: str) -> bool:
    h, w = len(grid), len(grid[0])
    candidates = []
    if shape_kind == "bar":
        shapes = [((r, c), (r, c + 1)) for r in range(h) for c in range(w - 1)]
        shapes += [((r, c), (r + 1, c)) for r in range(h - 1) for c in range(w)]
    else:
        shapes = [((r, c),) for r in range(h) for c in range(w)]
    for cells in shapes:
        if any(
            rb[0] <= r <= rb[2] and rb[1] <= c <= rb[3]
            for r, c in cells for rb in root_bboxes
        ):
            continue
        if _is_clear(grid, cells):
            candidates.append(cells)
    if not candidates:
        return False
    for r, c in rng.choice(candidates):
        grid[r][c] = color
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    min_dim = _requested_min_dimension(overrides)
    h = ctx.draw_int_diff("grid_h", min_dim, 30)
    w = ctx.draw_int_diff("grid_w", min_dim, 30)

    requested_depth = int(overrides["max_depth"]) if "max_depth" in overrides else 2
    max_groups = _max_feasible_groups(h, w, requested_depth)
    if max_groups < 1:
        raise ValueError(f"no nested layout fits in {h}x{w}")
    group_count = ctx.draw_int_diff("group_count", 1, max_groups)

    feasible_depth = _max_feasible_depth(h, w, group_count)
    if feasible_depth < 2:
        raise ValueError(f"group_count={group_count} has no valid depth in {h}x{w}")
    max_depth = ctx.draw_int_diff("max_depth", 2, feasible_depth)
    distractor_count = ctx.draw_int_diff("distractor_count", 0, 3)
    include_solid = ctx.draw_choice("include_solid", [False, True])
    palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))

    layout_rng = ctx.draw_rng("layout")
    slots = _slot_layout(h, w, group_count, max_depth, layout_rng)
    grid = full_grid(h, w, 0)
    colors = _Colors(_palette(palette_kind, ctx.draw_rng("colors")))
    root_bboxes = []

    for group_index, slot in enumerate(slots):
        slot_h = slot[2] - slot[0] + 1
        slot_w = slot[3] - slot[1] + 1
        if group_index == 0:
            depth = max_depth
        else:
            slot_max = min(3, _max_feasible_depth(slot_h + 2, slot_w + 2, 1))
            depth = layout_rng.randint(2, min(max_depth, slot_max))
        outer = _choose_bbox(slot, depth, layout_rng)
        root_bboxes.append(outer)
        outer_color = colors.take()
        _draw_shape(grid, outer, outer_color, "frame")
        chain = [outer]
        parent = outer
        parent_color = outer_color

        for level in range(1, depth):
            is_deepest = level == depth - 1
            solid_here = include_solid and group_index == 0 and is_deepest
            if solid_here:
                parent_h = parent[2] - parent[0] + 1
                parent_w = parent[3] - parent[1] + 1
                plus_fits = parent_h >= 7 and parent_w >= 7
                if not plus_fits or layout_rng.getrandbits(1):
                    min_h, min_w, kind = 1, 2, "bar"
                else:
                    min_h, min_w, kind = 3, 3, "plus"
            else:
                remaining = depth - level
                minimum = _min_outer_size(remaining)
                min_h = min_w = minimum
                kind = "frame"
            child = _child_bbox(parent, min_h, min_w, layout_rng)
            child_color = colors.take(exclude={parent_color, outer_color})
            _draw_shape(grid, child, child_color, kind)
            chain.append(child)
            parent, parent_color = child, child_color

        # Canonical rows contain both pure chains and siblings nested directly
        # under an outer frame. Add those only when they fit without creating a
        # second accidental depth branch.
        sibling_target = 0
        if difficulty == "hard":
            sibling_target = 2
        elif difficulty == "medium" or layout_rng.random() < 0.65:
            sibling_target = 1
        for _ in range(sibling_target):
            sibling_color = colors.take(exclude={outer_color})
            if not _place_sibling(grid, outer, chain, sibling_color, layout_rng):
                break

    for index in range(distractor_count):
        distractor_color = colors.take()
        kind = "bar" if index == 0 and layout_rng.getrandbits(1) else "dot"
        placed = _place_distractor(
            grid, root_bboxes, distractor_color, layout_rng, kind
        )
        if not placed and kind == "bar":
            placed = _place_distractor(
                grid, root_bboxes, distractor_color, layout_rng, "dot"
            )
        if not placed:
            raise ValueError(
                f"cannot place distractor {index + 1}/{distractor_count} "
                f"outside {group_count} nesting groups in {h}x{w}"
            )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"internal construction failed self_check: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "group_count": group_count,
        "max_depth": max_depth,
        "distractor_count": distractor_count,
        "include_solid": include_solid,
    }
    mismatches = {
        key: (value, observed.get(key))
        for key, value in expected.items()
        if observed.get(key) != value
    }
    if mismatches:
        raise ValueError(f"internal observable mismatch: {mismatches}")
    return grid


def _components(grid) -> list[_Component]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    result: list[_Component] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            result.append(
                _Component(
                    color=color,
                    cells=tuple(cells),
                    bbox=(min(rs), min(cs), max(rs), max(cs)),
                )
            )
    return result


def _rect_frame_bbox(component: _Component):
    r0, c0, r1, c1 = component.bbox
    height, width = r1 - r0 + 1, c1 - c0 + 1
    if height < 2 or width < 2:
        return None
    wanted = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return component.bbox if set(component.cells) == wanted else None


def _strictly_contains(outer: _Component, inner: _Component) -> bool:
    if outer is inner:
        return False
    r0, c0, r1, c1 = outer.bbox
    ir0, ic0, ir1, ic1 = inner.bbox
    return r0 < ir0 and c0 < ic0 and ir1 < r1 and ic1 < c1


def _relations(components: list[_Component]):
    containers = {
        index: [
            outer_index
            for outer_index, outer in enumerate(components)
            if _strictly_contains(outer, component)
        ]
        for index, component in enumerate(components)
    }
    roots = [index for index, values in containers.items() if not values]
    descendants = {
        index: [
            child_index
            for child_index, child in enumerate(components)
            if _strictly_contains(component, child)
        ]
        for index, component in enumerate(components)
    }
    return containers, roots, descendants


def _max_depth(components: list[_Component], descendants) -> int:
    memo: dict[int, int] = {}

    def depth(index: int) -> int:
        if index not in memo:
            memo[index] = 1 + max(
                (depth(child) for child in descendants[index]), default=0
            )
        return memo[index]

    return max((depth(i) for i in range(len(components))), default=0)


def rule_mirror(grid):
    """Python parity mirror used only by focused tests and evidence tooling."""
    components = _components(grid)
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            containing = [
                component
                for component in components
                if (
                    component.bbox[0] <= r <= component.bbox[2]
                    and component.bbox[1] <= c <= component.bbox[3]
                )
            ]
            largest_area = max(component.area for component in containing)
            largest = [
                component for component in containing if component.area == largest_area
            ]
            if len(largest) != 1:
                raise ValueError("tied largest enclosing bboxes")
            output[r][c] = largest[0].color
    return output


def observe_overrides(grid) -> dict:
    components = _components(grid)
    containers, roots, descendants = _relations(components)
    group_roots = [
        index
        for index in roots
        if _rect_frame_bbox(components[index]) is not None
        and descendants[index]
    ]
    contained = [index for index, values in containers.items() if values]
    return {
        "group_count": len(group_roots),
        "max_depth": _max_depth(components, descendants),
        "distractor_count": len(roots) - len(group_roots),
        "include_solid": any(
            _rect_frame_bbox(components[index]) is None for index in contained
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is not a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged or has zero width"]
    if len(grid) > 30 or width > 30:
        errors.append("grid exceeds 30x30")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains invalid ARC colors")
        return errors

    components = _components(grid)
    if len(components) < 2:
        errors.append("fewer than two non-background components")
        return errors
    containers, roots, descendants = _relations(components)
    group_roots = [
        index
        for index in roots
        if _rect_frame_bbox(components[index]) is not None
        and descendants[index]
    ]
    if not group_roots:
        errors.append("no rectangular root frame contains another component")

    # Crossing bounding boxes are not a canonical nesting relation and can make
    # bbox-based recoloring look like spatial overlap rather than enclosure.
    for left in range(len(components)):
        a = components[left].bbox
        for right in range(left + 1, len(components)):
            b = components[right].bbox
            intersects = not (
                a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]
            )
            if intersects and not (
                _strictly_contains(components[left], components[right])
                or _strictly_contains(components[right], components[left])
            ):
                errors.append("component bounding boxes cross without nesting")
                break
        if errors and errors[-1] == "component bounding boxes cross without nesting":
            break

    changed = 0
    for index, component in enumerate(components):
        candidates = containers[index] + [index]
        largest_area = max(components[candidate].area for candidate in candidates)
        largest = [
            candidate
            for candidate in candidates
            if components[candidate].area == largest_area
        ]
        if len(largest) != 1:
            errors.append("a component has tied largest enclosing bboxes")
            continue
        outermost = components[largest[0]]
        if containers[index] and _rect_frame_bbox(outermost) is None:
            errors.append("a contained component's outermost container is not a frame")
        if outermost.color != component.color:
            changed += 1
    if changed == 0:
        errors.append("no component would change to an outer-frame color")

    return list(dict.fromkeys(errors))

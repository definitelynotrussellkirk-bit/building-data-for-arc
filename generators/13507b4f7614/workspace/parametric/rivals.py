"""Independent finite rectangle-rule diagnostics, never a label authority.

This helper may rank lawful demonstration inputs. Authoritative episode labels
and causal counterfactual labels must still execute through protected Racket.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Rectangle:
    top: int
    left: int
    bottom: int
    right: int

    @property
    def h(self):
        return self.bottom - self.top + 1

    @property
    def w(self):
        return self.right - self.left + 1

    @property
    def area(self):
        return self.h * self.w

    @property
    def odd(self):
        return self.h % 2 == self.w % 2 == 1

    @property
    def center(self):
        return (self.top + self.bottom, self.left + self.right)


def rectangles(grid):
    """Independent connected-component extraction, requiring solid rectangles."""
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4}
    result = []
    while cells:
        start = min(cells)
        cells.remove(start)
        component, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in cells:
                    cells.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        rows, cols = zip(*component)
        rect = Rectangle(min(rows), min(cols), max(rows), max(cols))
        if len(component) != rect.area:
            raise ValueError("diagnostic rival input has a nonsolid component")
        result.append(rect)
    return sorted(result)


def paint(grid, chosen):
    output = [row[:] for row in grid]
    for rect in chosen:
        middle_r = (rect.top + rect.bottom) // 2
        middle_c = (rect.left + rect.right) // 2
        for r in range(rect.top, rect.bottom + 1):
            for c in range(rect.left, rect.right + 1):
                output[r][c] = 4 if r == middle_r or c == middle_c else 0
    return output


def choose(items, key, *, largest=False):
    """Explicit reading-order tie break makes heuristic rivals total functions."""
    return sorted(items, key=lambda obj: (key(obj), obj), reverse=largest)[0]


def diagnostic(grid, name):
    """Python-only finite rival semantics; never used to create Racket labels."""
    if name not in RIVALS and name not in ("cascade_correct", "cascade_intended"):
        raise ValueError(f"unknown diagnostic rule: {name}")
    objects = rectangles(grid)
    odds = [obj for obj in objects if obj.odd]
    if name == "identity":
        return paint(grid, [])
    if name == "all_odd":
        return paint(grid, odds)
    if name == "all_rectangles_ignore_parity":
        return paint(grid, objects)
    if name == "height_odd_only":
        return paint(grid, [obj for obj in objects if obj.h % 2])
    if name == "width_odd_only":
        return paint(grid, [obj for obj in objects if obj.w % 2])
    if not odds:
        return paint(grid, [])
    anchor = choose(odds, lambda obj: obj.area, largest=True)
    if name == "largest_odd_only":
        return paint(grid, [anchor])
    if name == "smallest_odd_only":
        return paint(grid, [choose(odds, lambda obj: obj.area)])
    if name == "cascade_wrong_anchor_smallest":
        anchor = choose(odds, lambda obj: obj.area)
    remaining = [obj for obj in odds if obj != anchor]
    target_area = anchor.h + anchor.w - 1
    metric = {
        "cascade_count_h_plus_w": anchor.h + anchor.w,
        "cascade_count_original_area": anchor.area,
        "cascade_count_height": anchor.h,
        "cascade_count_width": anchor.w,
        "cascade_count_perimeter": 2 * (anchor.h + anchor.w) - 4,
        "cascade_count_half_perimeter": anchor.h + anchor.w - 2,
    }
    target_area = metric.get(name, target_area)
    if name.startswith("cascade_fixed_area_"):
        target_area = int(name.rsplit("_", 1)[1])
    target = [obj for obj in remaining if obj.area == target_area]
    if remaining:
        ar, ac = anchor.center
        selectors = {
            "cascade_target_first": lambda: min(remaining),
            "cascade_target_last": lambda: max(remaining),
            "cascade_target_second": lambda: sorted(remaining)[min(1, len(remaining) - 1)],
            "cascade_target_smallest": lambda: choose(remaining, lambda obj: obj.area),
            "cascade_target_largest": lambda: choose(remaining, lambda obj: obj.area, largest=True),
            "cascade_target_nearest": lambda: choose(remaining, lambda obj: (obj.center[0] - ar) ** 2 + (obj.center[1] - ac) ** 2),
            "cascade_target_farthest": lambda: choose(remaining, lambda obj: (obj.center[0] - ar) ** 2 + (obj.center[1] - ac) ** 2, largest=True),
            "cascade_target_tallest": lambda: choose(remaining, lambda obj: obj.h, largest=True),
            "cascade_target_widest": lambda: choose(remaining, lambda obj: obj.w, largest=True),
            "cascade_target_narrowest": lambda: choose(remaining, lambda obj: obj.w),
            "cascade_target_most_square": lambda: choose(remaining, lambda obj: abs(obj.h - obj.w)),
            "cascade_target_aspect_nearest": lambda: choose(remaining, lambda obj: abs(obj.h / obj.w - anchor.h / anchor.w)),
            "cascade_target_aspect_farthest": lambda: choose(remaining, lambda obj: abs(obj.h / obj.w - anchor.h / anchor.w), largest=True),
            "cascade_target_height_nearest": lambda: choose(remaining, lambda obj: abs(obj.h - anchor.h)),
            "cascade_target_width_nearest": lambda: choose(remaining, lambda obj: abs(obj.w - anchor.w)),
        }
        if name in selectors:
            target = [selectors[name]()]
        if name == "cascade_same_orientation":
            target = [obj for obj in remaining if (obj.h >= obj.w) == (anchor.h >= anchor.w)]
    if name == "cascade_skip_a":
        return paint(grid, target)
    return paint(grid, [anchor] + target)


RIVALS = (
    "identity", "all_odd", "all_rectangles_ignore_parity", "height_odd_only",
    "width_odd_only", "largest_odd_only", "smallest_odd_only",
    "cascade_fixed_area_9", "cascade_fixed_area_15", "cascade_fixed_area_21", "cascade_fixed_area_25",
    "cascade_target_first", "cascade_target_last", "cascade_target_second",
    "cascade_target_smallest", "cascade_target_largest", "cascade_target_nearest", "cascade_target_farthest",
    "cascade_target_tallest", "cascade_target_widest", "cascade_target_narrowest", "cascade_target_most_square",
    "cascade_target_aspect_nearest", "cascade_target_aspect_farthest",
    "cascade_target_height_nearest", "cascade_target_width_nearest", "cascade_same_orientation",
    "cascade_count_h_plus_w", "cascade_count_original_area", "cascade_count_height",
    "cascade_count_width", "cascade_count_perimeter", "cascade_count_half_perimeter",
    "cascade_skip_a", "cascade_wrong_anchor_smallest",
)


"""Direction-parametric marker-count crop-and-rotation family.

The default ``clockwise`` setting is the exact canonical Racket program.  The
alternate ``counterclockwise`` setting preserves marker counting, marker
removal, tight cropping, and whole-scene rotation while reversing the direction
chosen from the input-dependent marker count.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from typing import Callable

TASK_ID = "ffcd7510821d"
DIRECTIONS = ("clockwise", "counterclockwise")

CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (let* ((turns (modulo (count-where (lambda (v) (= v 9)) (row g 0)) 4)) (clean (grid-from-fn (rows g) (cols g) (lambda (r c) (if (and (= r 0) (= (at g r c) 9)) 0 (at g r c))))) (obj (crop-to-content clean))) (cond ((= turns 1) (rotate-cw obj)) ((= turns 2) (rotate-180 obj)) ((= turns 3) (rotate-ccw obj)) (else obj)))))"
COUNTERCLOCKWISE_PROGRAM = "(rule! (let ((dummy 0)) (let* ((turns (modulo (count-where (lambda (v) (= v 9)) (row g 0)) 4)) (clean (grid-from-fn (rows g) (cols g) (lambda (r c) (if (and (= r 0) (= (at g r c) 9)) 0 (at g r c))))) (obj (crop-to-content clean))) (cond ((= turns 1) (rotate-ccw obj)) ((= turns 2) (rotate-180 obj)) ((= turns 3) (rotate-cw obj)) (else obj)))))"

# height, width, row-0 markers, distinct blobs/colors, target cells per blob
DEMO_PROFILES: tuple[tuple[int, int, int, int, int], ...] = (
    (9, 10, 1, 2, 5),
    (10, 13, 3, 3, 5),
    (12, 11, 2, 2, 7),
    (14, 14, 4, 4, 7),
    (16, 18, 1, 3, 9),
    (20, 17, 3, 4, 10),
)
QUERY_PROFILES: tuple[tuple[int, int, int, int, int], ...] = (
    (15, 20, 2, 3, 8),
    (21, 16, 4, 4, 10),
    (25, 28, 1, 4, 12),
    (30, 30, 3, 4, 15),
)
PROFILES = DEMO_PROFILES + QUERY_PROFILES
_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _validate_direction(direction: str) -> str:
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError("direction must be clockwise or counterclockwise")
    return direction


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    return seed


def _validate_grid(grid: list[list[int]]) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be a rectangular 1..30 exact-integer ARC grid")
    return grid


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _rotate(grid: list[list[int]], turns: int) -> list[list[int]]:
    out = _copy_grid(grid)
    for _ in range(turns % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def orbit_size(grid: list[list[int]]) -> int:
    _validate_grid(grid)
    return len({_freeze(_rotate(grid, turns)) for turns in range(4)})


def marker_turns(grid: list[list[int]]) -> int:
    _validate_grid(grid)
    return grid[0].count(9) % 4


def _clean_markers(grid: list[list[int]]) -> list[list[int]]:
    _validate_grid(grid)
    return [
        [0 if row_index == 0 and value == 9 else value for value in row]
        for row_index, row in enumerate(grid)
    ]


def content_crop(grid: list[list[int]], *, selected_color: int | None = None) -> list[list[int]]:
    clean = _clean_markers(grid)
    if selected_color is not None:
        if type(selected_color) is not int or not 1 <= selected_color <= 8:
            raise ValueError("selected_color must be an exact content color 1..8")
        clean = [[value if value == selected_color else 0 for value in row] for row in clean]
    cells = [(r, c) for r, row in enumerate(clean) for c, value in enumerate(row) if value]
    if not cells:
        raise ValueError("grid has no content after clearing row-0 markers")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in clean[r0 : r1 + 1]]


def _physical_turns(direction: str, turns: int) -> int:
    _validate_direction(direction)
    if type(turns) is not int:
        raise ValueError("turns must be an exact integer")
    return turns % 4 if direction == "clockwise" else (-turns) % 4


def apply_with_forced_turns(grid: list[list[int]], direction: str, turns: int) -> list[list[int]]:
    return _rotate(content_crop(grid), _physical_turns(direction, turns))


def apply_rule(grid: list[list[int]], direction: str) -> list[list[int]]:
    return apply_with_forced_turns(grid, direction, marker_turns(grid))


def program_for(direction: str) -> str:
    direction = _validate_direction(direction)
    return CANONICAL_PROGRAM if direction == "clockwise" else COUNTERCLOCKWISE_PROGRAM


def fixed_turn_program(direction: str, turns: int) -> str:
    """Counterfactual Racket rule using a forced marker-count intermediate."""
    direction = _validate_direction(direction)
    if type(turns) is not int or not 0 <= turns <= 3:
        raise ValueError("turns must be an exact integer in 0..3")
    physical = _physical_turns(direction, turns)
    operation = {
        0: "obj",
        1: "(rotate-cw obj)",
        2: "(rotate-180 obj)",
        3: "(rotate-ccw obj)",
    }[physical]
    return (
        "(rule! (let ((dummy 0)) (let* ((clean (grid-from-fn (rows g) (cols g) "
        "(lambda (r c) (if (and (= r 0) (= (at g r c) 9)) 0 (at g r c))))) "
        f"(obj (crop-to-content clean))) {operation})))"
    )


def _derived_rng(seed: int, slot: int) -> random.Random:
    payload = f"{TASK_ID}:direction-v1:{seed}:{slot}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _rectangular(cells: set[tuple[int, int]]) -> bool:
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1) == len(cells)


def _frontier(cells: set[tuple[int, int]], height: int, width: int) -> list[tuple[int, int]]:
    return sorted(
        {
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _DIR4
            if 0 <= r + dr < height and 0 <= c + dc < width
        }
        - cells
    )


def _corner_seed(height: int, width: int, corner: str) -> set[tuple[int, int]]:
    if height < 2 or width < 2:
        raise ValueError("blob slots must be at least 2x2")
    if corner == "tl":
        return {(0, 0), (1, 0), (0, 1)}
    if corner == "tr":
        return {(0, width - 1), (1, width - 1), (0, width - 2)}
    if corner == "bl":
        return {(height - 1, 0), (height - 2, 0), (height - 1, 1)}
    if corner == "br":
        return {
            (height - 1, width - 1),
            (height - 2, width - 1),
            (height - 1, width - 2),
        }
    raise ValueError("unknown corner")


def _grow_blob(
    rng: random.Random,
    height: int,
    width: int,
    target: int,
    corner: str,
) -> set[tuple[int, int]]:
    target = min(max(target, 4), height * width - 1)
    attempt_seeds = [rng.getrandbits(64) for _ in range(64)]
    for attempt_seed in attempt_seeds:
        local = random.Random(attempt_seed)
        cells = set(_corner_seed(height, width, corner))
        while len(cells) < target:
            candidates = _frontier(cells, height, width)
            if not candidates:
                break
            cells.add(local.choice(candidates))
        if len(cells) == target and not _rectangular(cells):
            return cells
    # The inward L is already connected, anchored, asymmetric, and nonrectangular.
    return _corner_seed(height, width, corner)


def _halves(total: int) -> tuple[tuple[int, int], tuple[int, int]]:
    left = (total - 1) // 2
    right_start = left + 1
    return (0, left), (right_start, total)


def _slots(height: int, width: int, count: int, *, vertical_two: bool):
    body_h = height - 2
    rows = _halves(body_h)
    cols = _halves(width)
    if count == 1:
        return [(2, 0, body_h, width, "tl")]
    if count == 2 and vertical_two:
        return [
            (2, cols[0][0], body_h, cols[0][1] - cols[0][0], "tl"),
            (2, cols[1][0], body_h, cols[1][1] - cols[1][0], "tr"),
        ]
    if count == 2:
        return [
            (2 + rows[0][0], 0, rows[0][1] - rows[0][0], width, "tl"),
            (2 + rows[1][0], 0, rows[1][1] - rows[1][0], width, "bl"),
        ]
    quadrants = [
        (2 + rows[0][0], cols[0][0], rows[0][1] - rows[0][0], cols[0][1] - cols[0][0], "tl"),
        (2 + rows[0][0], cols[1][0], rows[0][1] - rows[0][0], cols[1][1] - cols[1][0], "tr"),
        (2 + rows[1][0], cols[0][0], rows[1][1] - rows[1][0], cols[0][1] - cols[0][0], "bl"),
        (2 + rows[1][0], cols[1][0], rows[1][1] - rows[1][0], cols[1][1] - cols[1][0], "br"),
    ]
    return quadrants[:count]


def _validate_input(grid: list[list[int]], profile: tuple[int, int, int, int, int]) -> None:
    height, width, markers, blobs, _ = profile
    _validate_grid(grid)
    if (len(grid), len(grid[0])) != (height, width):
        raise RuntimeError("generated dimensions differ from profile")
    if any(value not in (0, 9) for value in grid[0]) or grid[0].count(9) != markers:
        raise RuntimeError("generated marker row differs from profile")
    if any(grid[1]) or any(9 in row for row in grid[1:]):
        raise RuntimeError("generated separator/content marker invariant failed")
    colors = {value for row in grid[2:] for value in row if value}
    if len(colors) != blobs or not colors <= set(range(1, 9)):
        raise RuntimeError("generated blob/color count differs from profile")
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        todo = [next(iter(cells))]
        seen = {todo[0]}
        while todo:
            r, c = todo.pop()
            for dr, dc in _DIR4:
                candidate = (r + dr, c + dc)
                if candidate in cells and candidate not in seen:
                    seen.add(candidate)
                    todo.append(candidate)
        if seen != cells or _rectangular(cells):
            raise RuntimeError("generated colored blob is disconnected or rectangular")
    if orbit_size(content_crop(grid)) != 4:
        raise RuntimeError("generated whole-scene crop lacks four observable rotations")


def build_input(seed: int, slot: int) -> list[list[int]]:
    _validate_seed(seed)
    if type(slot) is not int or not 0 <= slot < len(PROFILES):
        raise ValueError(f"slot must be an exact integer in 0..{len(PROFILES) - 1}")
    profile = PROFILES[slot]
    height, width, markers, blobs, target = profile
    rng = _derived_rng(seed, slot)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for column in rng.sample(range(width), markers):
        grid[0][column] = 9
    colors = rng.sample(list(range(1, 9)), blobs)
    slots = _slots(height, width, blobs, vertical_two=(seed + slot) % 2 == 0)
    # Slot order is geometry-fixed so the 30x30 profile reaches all four
    # quadrants/boundaries. Colors and growth remain seed-dependent.
    for color, (r0, c0, slot_h, slot_w, corner) in zip(colors, slots):
        cells = _grow_blob(rng, slot_h, slot_w, target, corner)
        for r, c in cells:
            grid[r0 + r][c0 + c] = color
    _validate_input(grid, profile)
    return grid


def _validate_episode_request(seed: int, direction: str, demos: int, queries: int) -> None:
    _validate_seed(seed)
    _validate_direction(direction)
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def generate_episode(
    seed: int,
    *,
    direction: str,
    demos: int = 3,
    queries: int = 4,
) -> dict:
    _validate_episode_request(seed, direction, demos, queries)

    def pair(slot: int) -> dict:
        grid = build_input(seed, slot)
        return {"input": grid, "output": apply_rule(grid, direction)}

    train = [pair(slot) for slot in range(demos)]
    test = [pair(slot) for slot in range(len(DEMO_PROFILES), len(PROFILES))]
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"direction": direction},
        "counts": {"demos": demos, "queries": queries},
        "train": train,
        "test": test,
        "program_solution": program_for(direction),
    }


def public_challenge(episode: dict) -> dict:
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in test],
    }


def _content_colors(grid: list[list[int]]) -> list[int]:
    return sorted({value for row in grid[1:] for value in row if value not in (0, 9)})


def _largest_blob_only(grid: list[list[int]], direction: str) -> list[list[int]]:
    colors = _content_colors(grid)
    counts = {color: sum(row.count(color) for row in grid) for color in colors}
    selected = max(colors, key=lambda color: (counts[color], -color))
    crop = content_crop(grid, selected_color=selected)
    return _rotate(crop, _physical_turns(direction, marker_turns(grid)))


def _rotate_uncropped(grid: list[list[int]], direction: str) -> list[list[int]]:
    return _rotate(_clean_markers(grid), _physical_turns(direction, marker_turns(grid)))


def _mirror_output(grid: list[list[int]], direction: str) -> list[list[int]]:
    return [row[::-1] for row in apply_rule(grid, direction)]


def audit_episode(episode: dict) -> dict:
    direction = episode.get("settings", {}).get("direction")
    _validate_direction(direction)
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode lacks train/test lists")
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        "clockwise": lambda grid: apply_rule(grid, "clockwise"),
        "counterclockwise": lambda grid: apply_rule(grid, "counterclockwise"),
        "crop_only": lambda grid: apply_with_forced_turns(grid, "clockwise", 0),
        "always_clockwise": lambda grid: apply_with_forced_turns(grid, "clockwise", 1),
        "always_half_turn": lambda grid: apply_with_forced_turns(grid, "clockwise", 2),
        "always_counterclockwise": lambda grid: apply_with_forced_turns(grid, "clockwise", 3),
        "count_content_colors": lambda grid: apply_with_forced_turns(
            grid, direction, len(_content_colors(grid))
        ),
        "marker_count_plus_one": lambda grid: apply_with_forced_turns(
            grid, direction, marker_turns(grid) + 1
        ),
        "largest_blob_only": lambda grid: _largest_blob_only(grid, direction),
        "rotate_uncropped": lambda grid: _rotate_uncropped(grid, direction),
        "mirror_after_rotation": lambda grid: _mirror_output(grid, direction),
    }
    rows = []
    for name, transform in rivals.items():
        demo_mismatches = [
            index for index, pair in enumerate(train)
            if transform(pair["input"]) != pair["output"]
        ]
        query_mismatches = [
            index for index, pair in enumerate(test)
            if transform(pair["input"]) != pair["output"]
        ]
        rows.append(
            {
                "name": name,
                "demo_mismatches": demo_mismatches,
                "query_mismatches": query_mismatches,
            }
        )
    setting_survivors = [
        row["name"] for row in rows
        if row["name"] in DIRECTIONS and not row["demo_mismatches"]
    ]
    ambiguous = [
        row["name"] for row in rows
        if row["name"] != direction
        and not row["demo_mismatches"]
        and row["query_mismatches"]
    ]
    equivalent = [
        row["name"] for row in rows
        if row["name"] != direction
        and not row["demo_mismatches"]
        and not row["query_mismatches"]
    ]
    return {
        "schema": "ffcd7510821d-direction-shortcut-audit-v1",
        "chosen": direction,
        "setting_survivors": setting_survivors,
        "ambiguous_query_changers": ambiguous,
        "surviving_equivalent_rivals": equivalent,
        "rivals": rows,
        "limits": (
            "Finite Python-mirror rivals on one deterministic episode; protected "
            "Racket qualification remains authoritative for declared setting programs."
        ),
    }

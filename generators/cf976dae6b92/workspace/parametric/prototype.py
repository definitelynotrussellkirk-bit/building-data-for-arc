"""Episode-level fixed/nearest relay family for cf976dae6b92.

The canonical setting preserves the selected Racket program byte-for-byte.  The
nearby setting first selects whichever of colors 3 and 4 has the smaller
Manhattan distance from color 2, then uses that input-derived relay to choose
the route order.  Both legs retain the source puzzle's horizontal-then-vertical
gray routing and preserve all three marker cells.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

from reviewer_support import canonical_path, find_root

TASK_ID = "cf976dae6b92"
PARAMETER = "relay_policy"
POLICIES = ("fixed_4", "nearest_to_2")
DEFAULT_SETTINGS = {PARAMETER: "fixed_4"}
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parent
NEAREST_PROGRAM = HOME / "nearest.rkt"

# The first two profiles form the constructive minimum lesson.  In A,
# Manhattan selects 3 while Euclidean/Chebyshev/row-only select 4.  In B,
# Manhattan selects 4 while Euclidean/Chebyshev/column-only select 3.
_A_SMALL = {2: (0, 0), 3: (5, 1), 4: (3, 4)}
_B_SMALL = {2: (0, 0), 4: (1, 5), 3: (4, 3)}
_A_MEDIUM = {2: (0, 0), 3: (10, 2), 4: (6, 8)}
_B_MEDIUM = {2: (0, 0), 4: (2, 10), 3: (8, 6)}
_B_BIG = {2: (0, 0), 4: (4, 20), 3: (16, 12)}
_A_LARGE = {2: (0, 0), 3: (29, 2), 4: (15, 20)}
_B_LARGE = {2: (0, 0), 4: (2, 29), 3: (20, 15)}

# (height, width, points, placement).  Query profiles are independent of demo
# count, so requesting two or six demonstrations preserves the same four tests.
_TRAIN_PROFILES = (
    (11, 11, _A_SMALL, "center_pair"),
    (11, 11, _B_SMALL, "center_pair"),
    (13, 15, _A_MEDIUM, "boundary"),
    (15, 13, _B_MEDIUM, "interior"),
    (7, 7, _A_SMALL, "boundary"),
    (24, 25, _B_BIG, "boundary"),
)
_QUERY_PROFILES = (
    (7, 7, _B_SMALL, "boundary"),
    (18, 17, _A_MEDIUM, "interior"),
    (30, 30, _A_LARGE, "boundary"),
    (30, 30, _B_LARGE, "boundary"),
)
_CARDINAL_COLORS = (2, 4, 3)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _policy(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"{PARAMETER} must be one of {POLICIES!r}")
    return value


def canonical_program(*, root: Path = ROOT) -> str:
    programs: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError("canonical record has no Racket program")
                programs.add(source)
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, got {len(programs)}")
    return programs.pop()


def program(settings: dict[str, str]) -> str:
    selected = _policy(settings)
    if selected == "fixed_4":
        return canonical_program()
    return NEAREST_PROGRAM.read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        raise ValueError("grid dimensions must each be in 7..30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    return len(grid), width


def analyze_input(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    unexpected = sorted({value for row in grid for value in row if value not in (0, 2, 3, 4)})
    if unexpected:
        raise ValueError(f"only background 0 and marker colors 2,3,4 are admitted; got {unexpected}")
    found = {color: [] for color in _CARDINAL_COLORS}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value in found:
                found[value].append((row_index, col_index))
    counts = {color: len(cells) for color, cells in found.items()}
    if any(counts[color] != 1 for color in _CARDINAL_COLORS):
        raise ValueError(f"input needs exactly one marker of each color 2,4,3; got {counts}")
    positions = {color: found[color][0] for color in _CARDINAL_COLORS}
    if len({positions[color][0] for color in _CARDINAL_COLORS}) != 3:
        raise ValueError("marker rows must be pairwise distinct")
    if len({positions[color][1] for color in _CARDINAL_COLORS}) != 3:
        raise ValueError("marker columns must be pairwise distinct")
    r2, c2 = positions[2]
    distances = {
        color: abs(positions[color][0] - r2) + abs(positions[color][1] - c2)
        for color in (3, 4)
    }
    if distances[3] == distances[4]:
        raise ValueError("nearest relay grammar requires unequal Manhattan distances from color 2")
    return {
        "height": height,
        "width": width,
        "positions": positions,
        "manhattan": distances,
        "nearest": 3 if distances[3] < distances[4] else 4,
    }


def relay_choice(grid: list[list[int]], relay_policy: str) -> int:
    if type(relay_policy) is not str or relay_policy not in POLICIES:
        raise ValueError(f"relay_policy must be one of {POLICIES!r}")
    facts = analyze_input(grid)
    return 4 if relay_policy == "fixed_4" else int(facts["nearest"])


def _paint_horizontal(grid: list[list[int]], row: int, start: int, end: int, color: int) -> None:
    for col in range(min(start, end), max(start, end) + 1):
        grid[row][col] = color


def _paint_vertical(grid: list[list[int]], col: int, start: int, end: int, color: int) -> None:
    for row in range(min(start, end), max(start, end) + 1):
        grid[row][col] = color


def _connect(
    grid: list[list[int]],
    sequence: tuple[int, int, int],
    *,
    horizontal_first: bool = True,
    line_color: int = 5,
    legs: int = 2,
) -> list[list[int]]:
    facts = analyze_input(grid)
    positions = facts["positions"]
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for source, destination in tuple(zip(sequence, sequence[1:]))[:legs]:
        sr, sc = positions[source]
        dr, dc = positions[destination]
        if horizontal_first:
            _paint_horizontal(output, sr, sc, dc, line_color)
            _paint_vertical(output, dc, sr, dr, line_color)
        else:
            _paint_vertical(output, sc, sr, dr, line_color)
            _paint_horizontal(output, dr, sc, dc, line_color)
    for marker, (row, col) in positions.items():
        output[row][col] = marker
    return output


def apply_rule(grid: list[list[int]], relay_policy: str) -> list[list[int]]:
    relay = relay_choice(grid, relay_policy)
    other = 3 if relay == 4 else 4
    return _connect(grid, (2, relay, other))


def _normalize(points: dict[int, tuple[int, int]]) -> dict[int, tuple[int, int]]:
    r0 = min(row for row, _ in points.values())
    c0 = min(col for _, col in points.values())
    return {color: (row - r0, col - c0) for color, (row, col) in points.items()}


def _rotate(points: dict[int, tuple[int, int]]) -> dict[int, tuple[int, int]]:
    normalized = _normalize(points)
    height = max(row for row, _ in normalized.values()) + 1
    return _normalize({color: (col, height - 1 - row) for color, (row, col) in normalized.items()})


def _reflect(points: dict[int, tuple[int, int]]) -> dict[int, tuple[int, int]]:
    normalized = _normalize(points)
    width = max(col for _, col in normalized.values()) + 1
    return _normalize({color: (row, width - 1 - col) for color, (row, col) in normalized.items()})


def _variant(points: dict[int, tuple[int, int]], index: int) -> dict[int, tuple[int, int]]:
    current = _normalize(points)
    if index >= 4:
        current = _reflect(current)
    for _ in range(index % 4):
        current = _rotate(current)
    return _normalize(current)


def _rng(seed: int, split: str, index: int, label: str) -> random.Random:
    raw = f"{TASK_ID}|relay-v1|{seed}|{split}|{index}|{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _place(
    height: int,
    width: int,
    points: dict[int, tuple[int, int]],
    placement: str,
    rng: random.Random,
) -> dict[int, tuple[int, int]]:
    normalized = _normalize(points)
    shape_h = max(row for row, _ in normalized.values()) + 1
    shape_w = max(col for _, col in normalized.values()) + 1
    if shape_h > height or shape_w > width:
        raise ValueError("profile points do not fit requested grid")
    row_room = height - shape_h
    col_room = width - shape_w
    if placement == "boundary":
        top = rng.choice((0, row_room))
        left = rng.choice((0, col_room))
    elif placement == "center_pair":
        top = row_room // 2
        left = col_room // 2
    elif placement == "interior":
        top = 0 if row_room == 0 else rng.randint(0, row_room)
        left = 0 if col_room == 0 else rng.randint(0, col_room)
        if row_room >= 2:
            top = min(max(top, 1), row_room - 1)
        if col_room >= 2:
            left = min(max(left, 1), col_room - 1)
    else:
        raise ValueError(f"unknown placement {placement!r}")
    return {color: (row + top, col + left) for color, (row, col) in normalized.items()}


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _strict_int("seed", seed, 0, MAX_SEED)
    if split not in {"train", "test"}:
        raise ValueError("split must be 'train' or 'test'")
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    _strict_int("index", index, 0, len(profiles) - 1)
    height, width, base, placement = profiles[index]
    # The first two demonstrations deliberately share one transform so their
    # opposite relay choices cannot be inferred from dimensions or orientation.
    transform_rng = _rng(seed, "train-pair" if split == "train" and index < 2 else split, 0 if split == "train" and index < 2 else index, "transform")
    transformed = _variant(base, transform_rng.randrange(8))
    placed = _place(height, width, transformed, placement, _rng(seed, split, index, "placement"))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, (row, col) in placed.items():
        grid[row][col] = color
    analyze_input(grid)
    return grid


def digest_grid(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _selector_sequence(grid: list[list[int]], selector: str) -> tuple[int, int, int]:
    facts = analyze_input(grid)
    positions = facts["positions"]
    r2, c2 = positions[2]
    if selector == "fixed_4":
        relay = 4
    elif selector == "fixed_3":
        relay = 3
    elif selector == "nearest_manhattan":
        relay = facts["nearest"]
    elif selector == "farthest_manhattan":
        relay = 4 if facts["nearest"] == 3 else 3
    else:
        metrics: dict[str, Callable[[int], int]] = {
            "nearest_euclidean": lambda color: (positions[color][0] - r2) ** 2 + (positions[color][1] - c2) ** 2,
            "nearest_chebyshev": lambda color: max(abs(positions[color][0] - r2), abs(positions[color][1] - c2)),
            "nearest_row": lambda color: abs(positions[color][0] - r2),
            "nearest_col": lambda color: abs(positions[color][1] - c2),
            "topmost": lambda color: positions[color][0],
            "bottommost": lambda color: -positions[color][0],
            "leftmost": lambda color: positions[color][1],
            "rightmost": lambda color: -positions[color][1],
        }
        if selector not in metrics:
            raise ValueError(f"unknown selector rival {selector!r}")
        relay = min((3, 4), key=lambda color: (metrics[selector](color), color == 3))
    return (2, relay, 3 if relay == 4 else 4)


# A two-example shared lesson cannot falsify every arbitrary coordinate selector
# for both declared settings at once.  For example, if the nearest-Manhattan
# winner switches 3 -> 4, one of the row/column projections must agree with that
# switch somewhere.  The audit therefore uses a declared, setting-specific
# hypothesis class rather than pretending to prove unrestricted uniqueness.
RIVAL_SCOPE_LIMITS = {
    "fixed_4": (
        "Coordinate-only and absolute-extreme selectors are intentionally out of "
        "scope for the two-demo shared lesson; the lesson instead falsifies the "
        "declared nearest policy, its opposite, and the two standard 2-D norms."
    ),
    "nearest_to_2": (
        "The bounded bank covers fixed, farthest, Euclidean, Chebyshev, row/column, "
        "absolute-extreme, and route-construction shortcuts; unrestricted programs "
        "remain outside any finite audit."
    ),
}


def _rival_rules(intended_policy: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    if intended_policy not in POLICIES:
        raise ValueError(f"relay_policy must be one of {POLICIES!r}")
    intended_selector = "fixed_4" if intended_policy == "fixed_4" else "nearest_manhattan"
    if intended_policy == "fixed_4":
        selector_names = (
            "fixed_3", "nearest_manhattan", "farthest_manhattan",
            "nearest_euclidean", "nearest_chebyshev",
        )
    else:
        selector_names = (
            "fixed_4", "fixed_3", "farthest_manhattan",
            "nearest_euclidean", "nearest_chebyshev", "nearest_row", "nearest_col",
            "topmost", "bottommost", "leftmost", "rightmost",
        )
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}
    for name in selector_names:
        rivals[f"selector:{name}"] = lambda grid, selected=name: _connect(grid, _selector_sequence(grid, selected))
    intended_sequence = lambda grid: _selector_sequence(grid, intended_selector)
    rivals.update(
        {
            "route:vertical_first": lambda grid: _connect(grid, intended_sequence(grid), horizontal_first=False),
            "route:first_leg_only": lambda grid: _connect(grid, intended_sequence(grid), legs=1),
            "route:path_color_2": lambda grid: _connect(grid, intended_sequence(grid), line_color=2),
            "route:identity": lambda grid: deepcopy(grid),
        }
    )
    # Coordinate-sorted routes are a useful attack on the input-derived setting,
    # where the crossed minimum lesson can falsify them.  On the fixed setting one
    # of the two sorts can be extensionally identical on any particular two-scene
    # orientation, so reporting it as a learnability failure would be misleading.
    if intended_policy == "nearest_to_2":
        rivals.update(
            {
                "route:row_sorted": lambda grid: _connect(grid, tuple(sorted((2, 3, 4), key=lambda color: analyze_input(grid)["positions"][color][0]))),
                "route:col_sorted": lambda grid: _connect(grid, tuple(sorted((2, 3, 4), key=lambda color: analyze_input(grid)["positions"][color][1]))),
            }
        )
    return rivals


def lesson_rival_survivors(demos: Iterable[dict[str, Any]], intended_policy: str) -> list[str]:
    if intended_policy not in POLICIES:
        raise ValueError(f"relay_policy must be one of {POLICIES!r}")
    pairs = list(demos)
    if not pairs:
        raise ValueError("at least one demonstration is required")
    survivors = []
    for name, rival in _rival_rules(intended_policy).items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in pairs):
                survivors.append(name)
        except (KeyError, TypeError, ValueError, IndexError):
            continue
    return survivors


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    selected = _policy(settings)
    train_inputs = [sample_input(seed, "train", index) for index in range(demos)]
    test_inputs = [sample_input(seed, "test", index) for index in range(queries)]
    inputs = [*train_inputs, *test_inputs]
    digests = [digest_grid(grid) for grid in inputs]
    if len(digests) != len(set(digests)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    train = [{"input": grid, "output": apply_rule(grid, selected)} for grid in train_inputs]
    test = [{"input": grid, "output": apply_rule(grid, selected)} for grid in test_inputs]
    survivors = lesson_rival_survivors(train, selected)
    if survivors:
        raise RuntimeError(f"minimum lesson leaves plausible rivals: {survivors}")
    return {
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "settings": deepcopy(settings),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < QUERY_COUNT:
        raise ValueError("query_index must be an exact integer in 0..3")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != QUERY_COUNT:
        raise ValueError("episode must contain a four-query bank")
    return {
        "train": deepcopy(train),
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }

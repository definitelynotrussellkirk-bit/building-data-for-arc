"""Proposed contact-mode episode family for 7f2dafa2bee4.

The hidden episode parameter changes only how distinct same-color 4-connected
objects are considered to touch:

* ``cardinal``: an edge exists across a shared side (the exact ARC rule).
* ``eight_neighbor``: an edge also exists across a shared corner.

Inputs are sampled independently of the selected setting.  Every demonstration
contains at least one corner-only contact, so fitting the demonstrations alone
eliminates the other declared setting.  This module is an authoring prototype;
qualification re-executes all labels with the retained Racket programs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "7f2dafa2bee4"
HERE = Path(__file__).resolve().parent
SCHEMA = "7f2dafa2bee4-contact-mode-prototype-v1"

PARAMETERS = {"contact_mode": ("cardinal", "eight_neighbor")}
DEFAULT_SETTINGS = {"contact_mode": "cardinal"}
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

Grid = list[list[int]]
Cell = tuple[int, int]
Object = tuple[Cell, ...]

_CARDINAL: tuple[Cell, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT: tuple[Cell, ...] = _CARDINAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))

# Each profile is (canvas height, canvas width, distinct 4-connected objects).
# Demos deliberately cover several graph changes, rather than repeating one
# diagonal pair: isolates become a pair, a diagonal bridge becomes degree two,
# and a corner fan creates the saturated degree-3+ output color.
_PROFILES: dict[str, tuple[int, int, tuple[Object, ...]]] = {
    "demo_diag_pair": (
        11,
        14,
        (
            ((1, 1), (1, 2)),
            ((2, 3), (3, 3)),
            ((5, 1), (5, 2)),
            ((5, 3),),
            ((8, 6), (9, 6)),
        ),
    ),
    "demo_diag_bridge": (
        12,
        15,
        (
            ((2, 1),),
            ((2, 3),),
            ((1, 2),),
            ((5, 1), (6, 1)),
            ((6, 2), (6, 3)),
            ((9, 6),),
        ),
    ),
    "demo_corner_fan": (
        12,
        16,
        (
            ((2, 2),),
            ((1, 1),),
            ((1, 3),),
            ((3, 1),),
            ((3, 3),),
            ((6, 1), (6, 2)),
            ((6, 3),),
        ),
    ),
    "demo_mixed_path": (
        13,
        17,
        (
            ((1, 1),),
            ((1, 2),),
            ((2, 3),),
            ((3, 2),),
            ((3, 1),),
            ((6, 5), (7, 5)),
        ),
    ),
    "demo_boundary_fan": (
        14,
        18,
        (
            ((0, 0), (0, 1)),
            ((1, 2),),
            ((2, 1),),
            ((3, 0),),
            ((0, 5),),
            ((0, 6),),
        ),
    ),
    "demo_double_motif": (
        15,
        19,
        (
            ((1, 1),),
            ((2, 2),),
            ((3, 1),),
            ((1, 6), (1, 7)),
            ((2, 8),),
            ((6, 2),),
            ((6, 3),),
        ),
    ),
    # The first query is intentionally a substantive 30x30 canvas.  Its three
    # separated motifs occupy the boundary, center, and far corner.
    "query_large_30": (
        30,
        30,
        (
            ((14, 14), (14, 15)),
            ((13, 13),),
            ((13, 16),),
            ((15, 13),),
            ((15, 16),),
            ((0, 0), (1, 0)),
            ((2, 1),),
            ((26, 25), (26, 26)),
            ((26, 27),),
        ),
    ),
    "query_zigzag": (
        21,
        25,
        (
            ((2, 2),),
            ((2, 3),),
            ((3, 4),),
            ((4, 3),),
            ((4, 2),),
            ((5, 1),),
            ((10, 12), (11, 12)),
            ((14, 18),),
        ),
    ),
    "query_two_fans": (
        24,
        30,
        (
            ((4, 4),),
            ((3, 3),),
            ((3, 5),),
            ((5, 3),),
            ((5, 5),),
            ((14, 18), (14, 19)),
            ((13, 20),),
            ((15, 20),),
            ((20, 2),),
        ),
    ),
    "query_ladder": (
        18,
        22,
        (
            ((2, 2), (3, 2)),
            ((3, 3),),
            ((4, 4),),
            ((5, 4),),
            ((6, 3),),
            ((6, 2),),
            ((10, 10),),
            ((11, 11),),
        ),
    ),
}

_DEMO_PROFILES = (
    "demo_diag_pair",
    "demo_diag_bridge",
    "demo_corner_fan",
    "demo_mixed_path",
    "demo_boundary_fan",
    "demo_double_motif",
)
_QUERY_PROFILES = (
    "query_large_30",
    "query_zigzag",
    "query_two_fans",
    "query_ladder",
)


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"contact_mode"}:
        raise ValueError("settings must contain exactly contact_mode")
    mode = settings["contact_mode"]
    if type(mode) is not str or mode not in PARAMETERS["contact_mode"]:
        raise ValueError("contact_mode must be cardinal or eight_neighbor")
    return {"contact_mode": mode}


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def choose_settings(seed: int) -> dict[str, str]:
    """Choose one fixed setting deterministically without affecting inputs."""
    _exact_int(seed, "seed", 0, 2**63 - 1)
    modes = PARAMETERS["contact_mode"]
    return {"contact_mode": modes[seed % len(modes)]}


def program(settings: dict[str, str]) -> str:
    """Materialize the retained Racket rule for one validated setting."""
    mode = _settings(settings)["contact_mode"]
    filename = "contact-cardinal.rkt" if mode == "cardinal" else "contact-eight-neighbor.rkt"
    return (HERE / "rules" / filename).read_text(encoding="utf-8")


def _grid(grid: Any) -> Grid:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _objects(grid: Grid) -> list[list[Cell]]:
    """Return nonzero same-color four-connected objects in stable order."""
    _grid(grid)
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    found: list[list[Cell]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        pending = [start]
        cells: list[Cell] = []
        while pending:
            row, col = pending.pop()
            cells.append((row, col))
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
        found.append(sorted(cells))
    return sorted(found, key=lambda cells: cells[0])


def _deltas(mode: str) -> tuple[Cell, ...]:
    if mode == "cardinal":
        return _CARDINAL
    if mode == "eight_neighbor":
        return _EIGHT
    raise ValueError("contact_mode must be cardinal or eight_neighbor")


def _touching(first: Iterable[Cell], second: Iterable[Cell], deltas: tuple[Cell, ...]) -> bool:
    other = set(second)
    return any((row + dr, col + dc) in other for row, col in first for dr, dc in deltas)


def contact_degrees(grid: Grid, mode: str) -> list[int]:
    """Compute object-graph degrees under the selected contact neighborhood."""
    objects = _objects(grid)
    deltas = _deltas(mode)
    return [
        sum(index != other and _touching(obj, objects[other], deltas) for other in range(len(objects)))
        for index, obj in enumerate(objects)
    ]


def apply_python(grid: Grid, mode: str) -> Grid:
    """Independent Python mirror used for generation and qualification checks."""
    source = _grid(grid)
    objects = _objects(source)
    degrees = contact_degrees(source, mode)
    output = [[0 for _ in row] for row in source]
    for obj, degree in zip(objects, degrees):
        color = 1 if degree == 0 else 2 if degree == 1 else 3 if degree == 2 else 4
        for row, col in obj:
            output[row][col] = color
    return output


def _profile_rng(seed: int, profile: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}\0{seed}\0{profile}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _normalize(objects: list[list[Cell]]) -> list[list[Cell]]:
    min_row = min(row for obj in objects for row, _ in obj)
    min_col = min(col for obj in objects for _, col in obj)
    return [[(row - min_row, col - min_col) for row, col in obj] for obj in objects]


def _transform(objects: tuple[Object, ...], rng: random.Random) -> list[list[Cell]]:
    transformed = [[tuple(cell) for cell in obj] for obj in objects]
    if rng.randrange(2):
        transformed = [[(col, row) for row, col in obj] for obj in transformed]
    transformed = _normalize(transformed)
    max_row = max(row for obj in transformed for row, _ in obj)
    max_col = max(col for obj in transformed for _, col in obj)
    if rng.randrange(2):
        transformed = [[(max_row - row, col) for row, col in obj] for obj in transformed]
    if rng.randrange(2):
        transformed = [[(row, max_col - col) for row, col in obj] for obj in transformed]
    return [sorted(obj) for obj in _normalize(transformed)]


def render_profile(seed: int, profile: str) -> Grid:
    """Render a seed-varied input; the result is independent of contact_mode."""
    _exact_int(seed, "seed", 0, 2**63 - 1)
    if profile not in _PROFILES:
        raise ValueError(f"unknown profile {profile!r}")
    height, width, source_objects = _PROFILES[profile]
    rng = _profile_rng(seed, profile)
    objects = _transform(source_objects, rng)
    object_count = len(objects)
    if object_count > 9:
        raise AssertionError("profile requires more than nine distinct colors")
    template_height = max(row for obj in objects for row, _ in obj) + 1
    template_width = max(col for obj in objects for _, col in obj) + 1
    if template_height > height or template_width > width:
        raise AssertionError(f"profile {profile} does not fit its declared canvas")
    row_offset = rng.randrange(height - template_height + 1)
    col_offset = rng.randrange(width - template_width + 1)
    colors = rng.sample(range(1, 10), object_count)
    grid = [[0] * width for _ in range(height)]
    for obj, color in zip(objects, colors):
        for row, col in obj:
            target = (row + row_offset, col + col_offset)
            if grid[target[0]][target[1]] != 0:
                raise AssertionError(f"profile {profile} contains overlapping objects")
            grid[target[0]][target[1]] = color
    # This assertion protects the teaching contract from later profile edits.
    if apply_python(grid, "cardinal") == apply_python(grid, "eight_neighbor"):
        raise AssertionError(f"profile {profile} does not distinguish contact modes")
    return grid


def lesson_certificate(challenge: dict[str, Any]) -> dict[str, Any]:
    """Fit only demonstrations against the two declared settings."""
    train = challenge.get("train") if isinstance(challenge, dict) else None
    test = challenge.get("test") if isinstance(challenge, dict) else None
    if type(train) is not list or not train or type(test) is not list or not test:
        raise ValueError("challenge must contain nonempty train/test lists")
    survivors: list[str] = []
    eliminated: dict[str, int] = {}
    for mode in PARAMETERS["contact_mode"]:
        mismatch = next(
            (
                index
                for index, pair in enumerate(train)
                if apply_python(pair["input"], mode) != pair["output"]
            ),
            None,
        )
        if mismatch is None:
            survivors.append(mode)
        else:
            eliminated[mode] = mismatch
    query_predictions = {
        mode: [apply_python(pair["input"], mode) for pair in test]
        for mode in survivors
    }
    return {
        "schema": "declared-contact-mode-certificate-v1",
        "survivors": survivors,
        "elimination_demo_indices": eliminated,
        "query_predictions": query_predictions,
        "identified": len(survivors) == 1,
        "scope": "two declared settings; demonstration fit only",
    }


def generate_episode(
    seed: int,
    *,
    settings: dict[str, str] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    """Generate one fixed-setting episode with count-independent projections."""
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    _exact_int(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    selected = choose_settings(seed) if settings is None else _settings(settings)
    mode = selected["contact_mode"]

    # Build the complete named streams first and slice only at the public count
    # boundary.  Thus adding later queries cannot change any earlier pair.
    demo_inputs = [render_profile(seed, name) for name in _DEMO_PROFILES]
    query_inputs = [render_profile(seed, name) for name in _QUERY_PROFILES]
    train = [
        {"input": copy.deepcopy(grid), "output": apply_python(grid, mode)}
        for grid in demo_inputs[:demos]
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": apply_python(grid, mode)}
        for grid in query_inputs[:queries]
    ]
    episode = {
        "schema": SCHEMA,
        "status": "proposed",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "demo_count": demos,
        "query_count": queries,
        "profiles": {
            "train": list(_DEMO_PROFILES[:demos]),
            "test": list(_QUERY_PROFILES[:queries]),
        },
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }
    errors = episode_errors(episode)
    if errors:
        raise RuntimeError("generated invalid episode: " + "; ".join(errors))
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Project one visible ARC turn, excluding settings, rules, and answers."""
    if not isinstance(episode, dict) or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    tests = episode.get("test")
    if type(tests) is not list:
        raise ValueError("episode must contain a test list")
    _exact_int(query_index, "query_index", 0, len(tests) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(tests[query_index]["input"])}],
    }


def public_id(episode: dict[str, Any], query_index: int) -> str:
    """Hash exactly the visible turn bytes, never private settings or labels."""
    visible = public_turn(episode, query_index)
    payload = (
        json.dumps(visible, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def episode_errors(episode: Any) -> list[str]:
    """Return bounded structural, label, uniqueness, and teaching failures."""
    errors: list[str] = []
    if not isinstance(episode, dict):
        return ["episode must be a dictionary"]
    try:
        settings = _settings(episode.get("settings"))
    except (TypeError, ValueError) as error:
        return [str(error)]
    mode = settings["contact_mode"]
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not MIN_DEMOS <= len(train) <= MAX_DEMOS:
        errors.append(f"train must contain {MIN_DEMOS}..{MAX_DEMOS} pairs")
    if type(test) is not list or not MIN_QUERIES <= len(test) <= MAX_QUERIES:
        errors.append(f"test must contain {MIN_QUERIES}..{MAX_QUERIES} pairs")
    if errors:
        return errors
    if episode.get("demo_count") != len(train):
        errors.append("demo_count does not match train length")
    if episode.get("query_count") != len(test):
        errors.append("query_count does not match test length")
    if episode.get("program_solution") != program(settings):
        errors.append("program_solution does not match the selected setting")

    frozen_inputs: set[str] = set()
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or set(pair) != {"input", "output"}:
                errors.append(f"{split}[{index}] must contain exactly input/output")
                continue
            try:
                source = _grid(pair["input"])
                output = _grid(pair["output"])
            except ValueError as error:
                errors.append(f"{split}[{index}]: {error}")
                continue
            if len(source) != len(output) or len(source[0]) != len(output[0]):
                errors.append(f"{split}[{index}] output shape differs from input")
                continue
            expected = apply_python(source, mode)
            if output != expected:
                errors.append(f"{split}[{index}] output does not match {mode}")
            key = json.dumps(source, separators=(",", ":"), ensure_ascii=False)
            if key in frozen_inputs:
                errors.append(f"{split}[{index}] duplicates an earlier input")
            frozen_inputs.add(key)

    rival = "eight_neighbor" if mode == "cardinal" else "cardinal"
    for index, pair in enumerate(train):
        if isinstance(pair, dict) and set(pair) == {"input", "output"}:
            try:
                if apply_python(pair["input"], rival) == pair["output"]:
                    errors.append(f"train[{index}] does not refute {rival}")
            except ValueError:
                pass
    if not errors:
        certificate = lesson_certificate({"train": train, "test": test})
        if certificate["survivors"] != [mode]:
            errors.append("demonstrations do not uniquely identify the selected setting")
    return errors


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--contact-mode", choices=PARAMETERS["contact_mode"])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--public-query", type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    settings = (
        {"contact_mode": args.contact_mode}
        if args.contact_mode is not None
        else choose_settings(args.seed)
    )
    episode = generate_episode(
        args.seed,
        settings=settings,
        demos=args.demos,
        queries=args.queries,
    )
    payload: Any = episode
    if args.public_query is not None:
        payload = public_turn(episode, args.public_query)
    text = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

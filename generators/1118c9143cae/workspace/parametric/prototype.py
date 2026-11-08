"""Episode-fixed echo-scope family for ARC task 1118c9143cae.

``echo_scope=all`` is the exact selected canonical program.  The alternate
setting first counts the nonzero colors, selects the uniquely rarest color,
and then echoes only cells of that input-derived color through the same
180-degree point reflection.  Input scenes are shared byte-for-byte across
settings and are constructed so the rarest-color intermediate is nontrivial.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import hashlib
from functools import lru_cache
import importlib.util
from pathlib import Path
import random
from typing import Any


TASK_ID = "1118c9143cae"
ECHO_SCOPES = ("all", "rarest_color")
DEFAULT_SCOPE = "all"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4

HERE = Path(__file__).resolve().parent
_GENERATOR_PATH = HERE.parents[1] / "generator.py"
_GENERATOR_SPEC = importlib.util.spec_from_file_location(
    "_1118c9143cae_parametric_base", _GENERATOR_PATH
)
if _GENERATOR_SPEC is None or _GENERATOR_SPEC.loader is None:
    raise ImportError(f"cannot load task generator at {_GENERATOR_PATH}")
GEN = importlib.util.module_from_spec(_GENERATOR_SPEC)
_GENERATOR_SPEC.loader.exec_module(GEN)

CANONICAL_PROGRAM = GEN.CANONICAL_PROGRAM
RAREST_COLOR_PROGRAM = """(rule!
 ;; Step A: count every present nonzero color and select the unique rarest.
 ;; Step B: preserve the input and echo only that selected color by a half-turn.
 (let* ((colors (filter (lambda (color) (> (count-color g color) 0))
                        (range 1 10)))
        (rarest (first
                 (sort colors
                       (lambda (left right)
                         (< (count-color g left)
                            (count-color g right)))))))
   (for*/fold ((out g))
              ((r (range 0 (rows g)))
               (c (range 0 (cols g))))
     (if (= (at g r c) rarest)
         (set-cell out
                   (- (rows g) 1 r)
                   (- (cols g) 1 c)
                   rarest)
         out))))"""

# Scene counts support both a two-cell and a three-cell unique rare color.
# All common colors occur strictly more often, with one separate unique mode.
# Varying both the rare color and its count blocks fixed-color/fixed-count bypasses.
_DEMO_SPECS = (
    (9, 11, 12, 3, "interior"),
    (10, 14, 12, 3, "boundary"),
    (13, 13, 16, 4, "fixed_point"),
    (14, 19, 20, 5, "interior"),
    (18, 21, 20, 5, "boundary"),
    (21, 23, 24, 6, "fixed_point"),
)
_QUERY_SPECS = (
    (7, 8, 12, 3, "interior"),
    (12, 17, 16, 4, "boundary"),
    (17, 19, 20, 5, "fixed_point"),
    (30, 30, 40, 6, "boundary"),
)


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"echo_scope"}:
        raise ValueError("settings must contain exactly echo_scope")
    scope = settings["echo_scope"]
    if type(scope) is not str or scope not in ECHO_SCOPES:
        raise ValueError(f"echo_scope must be one of {ECHO_SCOPES}")
    return scope


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise ValueError("seed must be an exact integer (not bool)")
    return seed


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    return demos, queries


def program(settings: dict[str, str]) -> str:
    """Return exact Racket source for one validated episode setting."""
    scope = _validate_settings(settings)
    return CANONICAL_PROGRAM if scope == "all" else RAREST_COLOR_PROGRAM


def _grid_errors(grid: Any) -> list[str]:
    if type(grid) is not list or not grid:
        return ["grid must be a nonempty list"]
    if type(grid[0]) is not list or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid must fit within 30x30"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be exact ARC integer colors 0..9"]
    return []


def color_counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row if value != 0)


def rarest_color(grid: list[list[int]]) -> int:
    """Step A: return the uniquely least frequent nonzero color."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = color_counts(grid)
    if not counts:
        raise ValueError("rarest_color requires at least one nonzero color")
    minimum = min(counts.values())
    candidates = sorted(color for color, count in counts.items() if count == minimum)
    if len(candidates) != 1:
        raise ValueError("rarest_color requires a unique rarest nonzero color")
    return candidates[0]


def _echo_selected(
    grid: list[list[int]], predicate: Callable[[int], bool]
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value != 0 and predicate(value):
                output[height - 1 - row][width - 1 - col] = value
    return output


def apply_python(grid: list[list[int]], echo_scope: str) -> list[list[int]]:
    """Independent Python claim labels; protected Racket remains authority."""
    if echo_scope not in ECHO_SCOPES:
        raise ValueError(f"echo_scope must be one of {ECHO_SCOPES}")
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if echo_scope == "all":
        return GEN.rule_mirror(grid)
    selected = rarest_color(grid)
    return _echo_selected(grid, lambda value: value == selected)


def scene_errors(grid: Any) -> list[str]:
    """Validate the shared grammar and the non-collapsing count intermediate."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    errors.extend(GEN.strict_canonical_like(grid))
    if errors:
        return errors
    counts = color_counts(grid)
    frequencies = sorted(counts.values())
    if len(counts) < 3:
        errors.append("scene needs at least three nonzero colors")
    if frequencies and frequencies[0] not in (2, 3):
        errors.append("the unique rarest color must occur exactly two or three times")
    if frequencies and frequencies.count(frequencies[0]) != 1:
        errors.append("scene needs one unique rarest color")
    if any(count == 1 for count in counts.values()):
        errors.append("singleton colors are forbidden so rarity cannot collapse to singleton detection")
    if frequencies and frequencies.count(frequencies[-1]) != 1:
        errors.append("scene needs one unique most-frequent color")
    try:
        selected = rarest_color(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    ordered = [value for row in grid for value in row if value != 0]
    if selected == min(counts):
        errors.append("rarest color must not be the numerically smallest color")
    if ordered and ordered[0] == selected:
        errors.append("first visible color must not be the rarest")
    if ordered and ordered[-1] == selected:
        errors.append("last visible color must not be the rarest")
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            if grid[row][col] == selected and (row, col) == (
                height - 1 - row,
                width - 1 - col,
            ):
                errors.append("rarest-color cells must not be half-turn fixed points")
                break
    if apply_python(grid, "all") == apply_python(grid, "rarest_color"):
        errors.append("both settings must produce visibly different labels")
    return errors


def _stable_seed(seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{label}".encode()).digest()
    return int.from_bytes(digest[:16], "big")


def _palette_for_scene(seed: int, n_colors: int) -> tuple[int, tuple[int, ...]]:
    """Choose a varying non-minimum rare color and ordered common palette."""
    rng = random.Random(_stable_seed(seed, "palette"))
    selected = rng.sample(list(range(1, 10)), n_colors)
    minimum = min(selected)
    rare = rng.choice([color for color in selected if color != minimum])
    remaining = [color for color in selected if color != rare and color != minimum]
    rng.shuffle(remaining)
    return rare, (minimum, *remaining)


def _recolor_for_intermediate(
    grid: list[list[int]], *, seed: int, n_colors: int
) -> list[list[int]]:
    positions = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )
    if n_colors < 3 or n_colors > 6:
        raise ValueError("n_colors must be in 3..6")
    # Use a digest bit without involving process-global randomness.
    rare_count = 2 + (_stable_seed(seed, "rare-count") & 1)
    minimum_count = rare_count + (rare_count + 1) * (n_colors - 1) + 1
    if len(positions) < minimum_count:
        raise ValueError("cell_count is too small for a non-collapsing frequency lesson")

    height, width = len(grid), len(grid[0])
    fixed = (height // 2, width // 2) if height % 2 and width % 2 else None
    rare_candidates = [
        index
        for index, position in enumerate(positions)
        if index not in (0, len(positions) - 1) and position != fixed
    ]
    rng = random.Random(_stable_seed(seed, "recolor"))
    rare_indices = set(rng.sample(rare_candidates, rare_count))

    rare, commons = _palette_for_scene(seed, n_colors)
    # Every common color occurs at least rare_count+1 times.  The first common
    # color receives all surplus and is therefore the unique most frequent one.
    common_counts = {color: rare_count + 1 for color in commons}
    common_counts[commons[0]] += (
        len(positions) - rare_count - (rare_count + 1) * len(commons)
    )
    if common_counts[commons[0]] <= rare_count + 1:
        raise AssertionError("scene specification must leave a unique most frequent color")

    assignments: dict[int, int] = {index: rare for index in rare_indices}
    assignments[0] = commons[0]
    assignments[len(positions) - 1] = commons[0]
    common_counts[commons[0]] -= 2
    remaining_values = [
        color
        for color, count in common_counts.items()
        for _ in range(count)
    ]
    rng.shuffle(remaining_values)
    remaining_indices = [
        index
        for index in range(len(positions))
        if index not in assignments
    ]
    if len(remaining_values) != len(remaining_indices):
        raise AssertionError("recolor accounting mismatch")
    assignments.update(zip(remaining_indices, remaining_values))

    output = [[0 for _ in row] for row in grid]
    for index, (row, col) in enumerate(positions):
        output[row][col] = assignments[index]
    return output


def _scene(
    seed: int,
    *,
    slot: int,
    query: bool,
    attempt: int,
) -> list[list[int]]:
    specs = _QUERY_SPECS if query else _DEMO_SPECS
    height, width, cell_count, n_colors, profile = specs[slot]
    geometry_seed = _stable_seed(seed, f"geometry|{query}|{slot}|{attempt}")
    base = GEN.generate(
        geometry_seed,
        slot,
        grid_h=height,
        grid_w=width,
        cell_count=cell_count,
        n_colors=n_colors,
        scene_profile=profile,
    )
    grid = _recolor_for_intermediate(
        base,
        seed=_stable_seed(seed, f"colors|{query}|{slot}|{attempt}"),
        n_colors=n_colors,
    )
    errors = scene_errors(grid)
    if errors:
        raise AssertionError(f"constructed invalid scene: {errors}")
    return grid


def _echo_color(grid: list[list[int]], color: int) -> list[list[int]]:
    return _echo_selected(grid, lambda value: value == color)


def _fixed_min_color(grid: list[list[int]]) -> list[list[int]]:
    return _echo_color(grid, min(color_counts(grid)))


def _first_visible_color(grid: list[list[int]]) -> list[list[int]]:
    color = next(value for row in grid for value in row if value != 0)
    return _echo_color(grid, color)


def _last_visible_color(grid: list[list[int]]) -> list[list[int]]:
    color = next(value for row in reversed(grid) for value in reversed(row) if value != 0)
    return _echo_color(grid, color)


def _singleton_only(grid: list[list[int]]) -> list[list[int]]:
    counts = color_counts(grid)
    singleton = {color for color, count in counts.items() if count == 1}
    return _echo_selected(grid, lambda value: value in singleton)


def _most_frequent(grid: list[list[int]]) -> list[list[int]]:
    counts = color_counts(grid)
    maximum = max(counts.values())
    color = min(color for color, count in counts.items() if count == maximum)
    return _echo_color(grid, color)


def _horizontal_echo(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value != 0:
                output[row][width - 1 - col] = value
    return output


def _vertical_echo(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value != 0:
                output[height - 1 - row][col] = value
    return output


def _rotate_only(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _fixed_color(color: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def apply(grid: list[list[int]]) -> list[list[int]]:
        return _echo_color(grid, color) if color in color_counts(grid) else _identity(grid)
    return apply


def _fixed_count(count: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def apply(grid: list[list[int]]) -> list[list[int]]:
        counts = color_counts(grid)
        selected = {color for color, frequency in counts.items() if frequency == count}
        return _echo_selected(grid, lambda value: value in selected)
    return apply


def _fixed_color_rank(rank: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def apply(grid: list[list[int]]) -> list[list[int]]:
        colors = sorted(color_counts(grid))
        return _echo_color(grid, colors[rank]) if rank < len(colors) else _identity(grid)
    return apply


SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "echo_all": lambda grid: apply_python(grid, "all"),
    "echo_rarest": lambda grid: apply_python(grid, "rarest_color"),
    "fixed_min_color": _fixed_min_color,
    "first_visible_color": _first_visible_color,
    "last_visible_color": _last_visible_color,
    "singleton_only": _singleton_only,
    "most_frequent": _most_frequent,
    "horizontal_echo": _horizontal_echo,
    "vertical_echo": _vertical_echo,
    "rotate_only": _rotate_only,
    "identity": _identity,
}
SHORTCUTS.update({f"fixed_color_{color}": _fixed_color(color) for color in range(1, 10)})
SHORTCUTS.update({f"fixed_count_{count}": _fixed_count(count) for count in (2, 3)})
SHORTCUTS.update({f"fixed_color_rank_{rank}": _fixed_color_rank(rank) for rank in range(3)})
_OFFICIAL_SHORTCUT = {"all": "echo_all", "rarest_color": "echo_rarest"}


def _bank_is_distinguishing(demos: list[list[list[int]]]) -> bool:
    core = demos[:2]
    intermediates = [
        (rarest_color(grid), color_counts(grid)[rarest_color(grid)])
        for grid in core
    ]
    if intermediates[0][0] == intermediates[1][0]:
        return False
    if intermediates[0][1] == intermediates[1][1]:
        return False
    for scope in ECHO_SCOPES:
        labels = [apply_python(grid, scope) for grid in core]
        survivors = [
            name
            for name, rival in SHORTCUTS.items()
            if all(rival(grid) == label for grid, label in zip(core, labels))
        ]
        if survivors != [_OFFICIAL_SHORTCUT[scope]]:
            return False
    return True


@lru_cache(maxsize=256)
def _build_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    for attempt in range(64):
        demos = [
            _scene(seed, slot=slot, query=False, attempt=attempt)
            for slot in range(len(_DEMO_SPECS))
        ]
        queries = [
            _scene(seed, slot=slot, query=True, attempt=attempt)
            for slot in range(len(_QUERY_SPECS))
        ]
        keys = {
            tuple(tuple(row) for row in grid)
            for grid in demos + queries
        }
        if len(keys) != len(demos) + len(queries):
            continue
        if not _bank_is_distinguishing(demos):
            continue
        return demos, queries
    raise AssertionError("could not construct a two-demo distinguishing scene bank")


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def validate_episode(episode: Any, settings: Any) -> list[str]:
    """Reject malformed, stale, duplicate, forged, or ambiguous private material."""
    errors: list[str] = []
    try:
        scope = _validate_settings(settings)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if type(episode) is not dict or set(episode) != {"train", "test", "program_solution"}:
        return ["episode must contain exactly train, test, and program_solution"]
    if episode.get("program_solution") != program({"echo_scope": scope}):
        errors.append("program_solution does not match the selected setting program")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        errors.append("episode demos must contain an exact count in 2..6")
    if type(test) is not list or len(test) != 4:
        errors.append("episode queries must contain exactly four pairs")
    if errors and (type(train) is not list or type(test) is not list):
        return errors

    seen: set[tuple[tuple[int, ...], ...]] = set()
    structurally_valid: list[dict[str, Any]] = []
    for split_name, pairs in (("train", train), ("test", test)):
        if type(pairs) is not list:
            continue
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or set(pair) != {"input", "output"}:
                errors.append(f"{split_name}[{index}] must contain exactly input and output")
                continue
            grid = pair["input"]
            grid_problems = scene_errors(grid)
            if grid_problems:
                errors.extend(f"{split_name}[{index}] input: {problem}" for problem in grid_problems)
                continue
            output_problems = _grid_errors(pair["output"])
            if output_problems:
                errors.extend(f"{split_name}[{index}] output: {problem}" for problem in output_problems)
                continue
            key = _grid_key(grid)
            if key in seen:
                errors.append(f"duplicate input: {split_name}[{index}] is not distinct")
            seen.add(key)
            expected = apply_python(grid, scope)
            if pair["output"] != expected:
                errors.append(f"forged or stale label at {split_name}[{index}]")
            structurally_valid.append(pair)

    if (
        not errors
        and type(train) is list
        and type(test) is list
        and len(train) >= 2
        and len(test) == 4
        and all(type(pair) is dict and set(pair) == {"input", "output"} for pair in train + test)
    ):
        for name, rival in SHORTCUTS.items():
            try:
                survives = all(rival(pair["input"]) == pair["output"] for pair in train)
                changes_query = any(rival(pair["input"]) != pair["output"] for pair in test)
            except (TypeError, ValueError, StopIteration):
                continue
            if survives and changes_query:
                errors.append(f"ambiguous lesson: shortcut {name} fits all demos but changes a query")
    return errors


def generate(
    seed: int,
    settings: dict[str, str],
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
) -> dict[str, Any]:
    """Build one deterministic private episode with matched setting inputs."""
    seed = _validate_seed(seed)
    scope = _validate_settings(settings)
    demos, queries = _validate_counts(demos, queries)
    demo_bank, query_bank = _build_bank(seed)
    train = [
        {"input": [row[:] for row in grid], "output": apply_python(grid, scope)}
        for grid in demo_bank[:demos]
    ]
    test = [
        {"input": [row[:] for row in grid], "output": apply_python(grid, scope)}
        for grid in query_bank[:queries]
    ]
    episode = {
        "train": train,
        "test": test,
        "program_solution": program({"echo_scope": scope}),
    }
    errors = validate_episode(episode, {"echo_scope": scope})
    if errors:
        raise AssertionError(f"generated invalid episode: {errors}")
    return episode

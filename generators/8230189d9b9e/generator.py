"""Generator for arc_puzzle_bank_fourteenth21:H93 — prototype dictionary lookup.

Row 0 contains distinct key markers.  The 3x3 block immediately below each
marker is that key's prototype.  The nonzero values in the last row form a
left-to-right query; the answer copies the referenced 3x3 blocks, top-aligned,
with one blank column between blocks.

Ordinary four-sample windows deliberately contain (1) a canonical-scale
matched-colour anchor, (2) a label/body-colour decoupling counterexample,
(3) a repeated query, and (4) a query that omits a library entry.  Together
these defeat recolour-by-key, deduplicate-query, library-order, and tight-crop
shortcuts while preserving the selected Racket rule as sole output authority.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8230189d9b9e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b313e3795954"

SUMMARY = (
    "Read distinct key markers from row 0, use each marker's fixed 3x3 block "
    "as a dictionary value, then read the last-row key sequence and pack the "
    "referenced blocks left-to-right with one zero column gap.  Four-sample "
    "windows mix canonical anchors with decoupled colours, repeated keys, and "
    "subset queries so labels, order, multiplicity, and 3x3 padding all matter."
)

INVARIANTS = [
    "row 0 has 2..5 distinct key markers whose 3x3 bands do not overlap",
    "rows 1..3 contain one 3..7-cell monochrome prototype per key and no other cells",
    "all rows between the prototype library and the final query row are blank",
    "the last row contains 2..5 keys, all present in row 0, in answer order",
    "prototype colours are either all matched to their keys or all decoupled",
    "every four consecutive ordinary samples cover all semantic schedule profiles",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 6..8", "valid": "6..8"},
    "n_keys": {"type": "int", "default": "scheduled 2..5", "valid": "2..5"},
    "query_len": {"type": "int", "default": "scheduled 2..5", "valid": "2..5"},
    "prototype_color_mode": {
        "type": "str",
        "default": "scheduled",
        "valid": "matched|decoupled",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15
SCHEDULE_PROFILES = (0, 1, 2, 3)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_SPOTS = tuple((row, col) for row in range(3) for col in range(3))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    """Every four consecutive samples cover the full teaching schedule."""
    del seed, difficulty
    return int(sample_index) % 4


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "n_keys", "query_len"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer")
    if (
        "prototype_color_mode" in overrides
        and overrides["prototype_color_mode"] is not None
        and type(overrides["prototype_color_mode"]) is not str
    ):
        raise ValueError("prototype_color_mode must be a string")


def _draw_scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _draw_scheduled_choice(ctx, name: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(name) is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (scheduled,)))


def _scheduled_defaults(profile: int, difficulty: Any) -> tuple[int, int, int, str]:
    """Return grid_h, n_keys, query_len, colour mode for one schedule profile."""
    band = "medium" if difficulty is None else difficulty
    if profile == 0:
        # Exact canonical (h, w, palette) anchor in every difficulty band.
        return 6, 3, 3, "matched"
    if profile == 1:
        return (6 if band == "easy" else 7), 3, 3, "decoupled"
    if profile == 2:
        return (7 if band != "hard" else 8), (3 if band == "easy" else 4), 5, "matched"
    return (7 if band == "easy" else 8), (3 if band == "easy" else 5), 2, "decoupled"


def _connected(cells: frozenset[tuple[int, int]]) -> bool:
    todo = [next(iter(cells))]
    seen = {todo[0]}
    while todo:
        row, col = todo.pop()
        for drow, dcol in _CARDINAL:
            nxt = (row + drow, col + dcol)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return len(seen) == len(cells)


def _mask_pool() -> tuple[tuple[tuple[int, int], ...], ...]:
    masks: list[tuple[tuple[int, int], ...]] = []
    for size in range(3, 8):
        for cells in combinations(_SPOTS, size):
            frozen = frozenset(cells)
            if _connected(frozen):
                masks.append(tuple(cells))
    return tuple(masks)


_MASK_POOL = _mask_pool()
_WIDTH_PADDED_MASKS = tuple(
    mask
    for mask in _MASK_POOL
    if max(col for _, col in mask) - min(col for _, col in mask) < 2
)


def _key_layout(n_keys: int, profile: int, rng) -> tuple[list[int], int]:
    if profile in (0, 1) and n_keys == 3:
        return [1, 5, 9], 11
    left_margin = rng.randint(1, 2)
    columns = [left_margin]
    for _ in range(1, n_keys):
        columns.append(columns[-1] + rng.randint(4, 6))
    width = columns[-1] + rng.randint(2, 3)
    return columns, width


def _prototype_masks(n_keys: int, rng) -> list[tuple[tuple[int, int], ...]]:
    """Distinct connected masks, including one query-visible padded mask."""
    first = rng.choice(_WIDTH_PADDED_MASKS)
    remaining = [mask for mask in _MASK_POOL if mask != first]
    rng.shuffle(remaining)
    return [first, *remaining[: n_keys - 1]]


def _query_for_profile(keys: list[int], query_len: int, profile: int, rng) -> list[int]:
    """Build a query that always includes key 0 and realizes the schedule profile."""
    if profile == 0:
        # Canonical anchor: all three keys, but never library order.
        base = list(reversed(keys))
    elif profile == 1:
        base = keys[1:] + keys[:1]
    elif profile == 2:
        # Repetition is guaranteed even when query_len <= n_keys.
        base = [keys[0], keys[-1], keys[0]] + list(reversed(keys[1:-1]))
    else:
        # Omit at least one library entry on the ordinary scheduled path.
        kept = [keys[0], keys[-1]] if len(keys) > 2 else list(reversed(keys))
        base = kept

    query = list(base[:query_len])
    while len(query) < query_len:
        if profile == 2:
            query.append(keys[0] if len(query) % 2 == 0 else keys[-1])
        else:
            query.append(rng.choice(keys))
    if keys[0] not in query:
        query[0] = keys[0]
    if profile in (0, 1) and query == keys[: len(query)] and len(query) > 1:
        query[0], query[1] = query[1], query[0]
    return query


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; Racket remains the output authority."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_n, default_q, default_mode = _scheduled_defaults(profile, difficulty)
    height = _draw_scheduled_int(ctx, "grid_h", 6, 8, default_h)
    n_keys = _draw_scheduled_int(ctx, "n_keys", 2, 5, default_n)
    query_len = _draw_scheduled_int(ctx, "query_len", 2, 5, default_q)
    color_mode = _draw_scheduled_choice(
        ctx, "prototype_color_mode", ("matched", "decoupled"), default_mode
    )

    layout_rng = ctx.draw_rng("layout")
    shape_rng = ctx.draw_rng("prototype_shapes")
    color_rng = ctx.draw_rng("colors")
    query_rng = ctx.draw_rng("query")
    key_columns, width = _key_layout(n_keys, profile, layout_rng)
    keys = color_rng.sample(list(range(1, 10)), n_keys)
    masks = _prototype_masks(n_keys, shape_rng)

    if color_mode == "matched":
        body_colors = list(keys)
    else:
        # Reuse the same palette but rotate ownership: body colour is never its
        # own key.  This isolates label/body decoupling without confounding it
        # with a larger palette and preserves canonical-profile anchors.
        shift = color_rng.randint(1, n_keys - 1)
        body_colors = keys[shift:] + keys[:shift]

    grid = full_grid(height, width, 0)
    for column, key, body_color, mask in zip(key_columns, keys, body_colors, masks):
        grid[0][column] = key
        for row_offset, col_offset in mask:
            grid[1 + row_offset][column - 1 + col_offset] = body_color

    query = _query_for_profile(keys, query_len, profile, query_rng)
    query_columns = sorted(query_rng.sample(range(width), query_len))
    for column, key in zip(query_columns, query):
        grid[-1][column] = key

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("constructed invalid prototype dictionary: " + "; ".join(errors))
    return grid


def _analysis(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "key_columns": [],
        "keys": [],
        "prototypes": [],
        "query": [],
        "color_mode": None,
    }
    errors: list[str] = result["errors"]
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid must be a non-empty list of non-empty rows")
        return result
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(type(value) is not int or not (0 <= value <= 9) for row in grid for value in row):
        errors.append("grid cells must be integer ARC colours 0..9")
        return result

    height = len(grid)
    result["height"], result["width"] = height, width
    if not (6 <= height <= 8):
        errors.append("grid height must be 6..8")
    key_columns = [column for column, value in enumerate(grid[0]) if value != 0]
    keys = [grid[0][column] for column in key_columns]
    result["key_columns"], result["keys"] = key_columns, keys
    if not (2 <= len(keys) <= 5):
        errors.append("row 0 must contain 2..5 key markers")
    if len(set(keys)) != len(keys):
        errors.append("row-0 key values must be distinct")
    if any(column == 0 or column == width - 1 for column in key_columns):
        errors.append("every key must have a full 3-column prototype band")
    if any(right - left < 4 for left, right in zip(key_columns, key_columns[1:])):
        errors.append("prototype bands must not overlap")

    bands = {
        column: {(row, col) for row in range(1, min(height, 4)) for col in range(column - 1, column + 2)}
        for column in key_columns
        if 0 < column < width - 1
    }
    allowed_library = set().union(*bands.values()) if bands else set()
    stray_library = [
        (row, col)
        for row in range(1, min(height, 4))
        for col in range(width)
        if grid[row][col] != 0 and (row, col) not in allowed_library
    ]
    if stray_library:
        errors.append("rows 1..3 contain cells outside the keyed prototype bands")

    prototypes: list[dict[str, Any]] = []
    modes: list[str] = []
    masks: list[tuple[tuple[int, int], ...]] = []
    for column, key in zip(key_columns, keys):
        if column not in bands:
            continue
        cells = [
            (row, col, grid[row][col])
            for row in range(1, min(height, 4))
            for col in range(column - 1, column + 2)
            if grid[row][col] != 0
        ]
        colors = {value for _, _, value in cells}
        if not (3 <= len(cells) <= 7):
            errors.append(f"prototype under key {key} must contain 3..7 cells")
        if len(colors) != 1:
            errors.append(f"prototype under key {key} must be monochrome")
            body_color = None
        else:
            body_color = next(iter(colors))
            modes.append("matched" if body_color == key else "decoupled")
        mask = tuple(sorted((row - 1, col - (column - 1)) for row, col, _ in cells))
        masks.append(mask)
        prototypes.append(
            {"key": key, "column": column, "body_color": body_color, "mask": mask}
        )
    if len(set(masks)) != len(masks):
        errors.append("prototype masks must be pairwise distinct")
    if modes and all(mode == "matched" for mode in modes):
        result["color_mode"] = "matched"
    elif modes and all(mode == "decoupled" for mode in modes):
        result["color_mode"] = "decoupled"
    elif modes:
        errors.append("prototype colours must be uniformly matched or uniformly decoupled")
        result["color_mode"] = "mixed"
    result["prototypes"] = prototypes

    for row in range(4, max(4, height - 1)):
        if any(grid[row][col] != 0 for col in range(width)):
            errors.append("rows between the prototype library and query must be blank")
            break

    query = [value for value in grid[-1] if value != 0]
    result["query"] = query
    if not (2 <= len(query) <= 5):
        errors.append("the final-row query must contain 2..5 keys")
    if any(value not in set(keys) for value in query):
        errors.append("the query contains a key absent from row 0")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding prototype-dictionary scenes."""
    del difficulty, meta
    return sorted(set(_analysis(grid)["errors"]))


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "n_keys": len(analysis["keys"]),
        "query_len": len(analysis["query"]),
        "prototype_color_mode": analysis["color_mode"],
    }


def _pieces_by_key(grid: list[list[int]]) -> tuple[list[int], dict[int, list[list[int]]], list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid prototype dictionary: " + "; ".join(analysis["errors"]))
    keys = analysis["keys"]
    pieces = {
        prototype["key"]: [
            row[prototype["column"] - 1 : prototype["column"] + 2]
            for row in grid[1:4]
        ]
        for prototype in analysis["prototypes"]
    }
    return keys, pieces, analysis["query"]


def _pack(pieces: list[list[list[int]]]) -> list[list[int]]:
    if not pieces:
        return [[0]]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        for row in range(len(piece)):
            for col in range(len(piece[0])):
                if piece[row][col] != 0:
                    output[row][left + col] = piece[row][col]
        left += len(piece[0]) + 1
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; the Racket program is authoritative."""
    _keys, pieces, query = _pieces_by_key(grid)
    return _pack([pieces[key] for key in query])


def _recolor_by_query_color(grid: list[list[int]]) -> list[list[int]]:
    _keys, pieces, query = _pieces_by_key(grid)
    recolored = []
    for key in query:
        recolored.append([[key if value else 0 for value in row] for row in pieces[key]])
    return _pack(recolored)


def _deduplicate_query(grid: list[list[int]]) -> list[list[int]]:
    _keys, pieces, query = _pieces_by_key(grid)
    seen: set[int] = set()
    unique_query = [key for key in query if not (key in seen or seen.add(key))]
    return _pack([pieces[key] for key in unique_query])


def _library_order(grid: list[list[int]]) -> list[list[int]]:
    keys, pieces, _query = _pieces_by_key(grid)
    return _pack([pieces[key] for key in keys])


def _tight_crop(grid: list[list[int]]) -> list[list[int]]:
    _keys, pieces, query = _pieces_by_key(grid)
    crops: list[list[list[int]]] = []
    for key in query:
        piece = pieces[key]
        occupied = [(row, col) for row in range(3) for col in range(3) if piece[row][col] != 0]
        top = min(row for row, _ in occupied)
        bottom = max(row for row, _ in occupied)
        left = min(col for _, col in occupied)
        right = max(col for _, col in occupied)
        crops.append([row[left : right + 1] for row in piece[top : bottom + 1]])
    return _pack(crops)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "recolor_by_query_color": _recolor_by_query_color,
    "deduplicate_repeated_query": _deduplicate_query,
    "ignore_query_use_library_order": _library_order,
    "tight_crop_each_prototype": _tight_crop,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"recolor_by_query_color": _recolor_by_query_color}


def _lawful_analysis(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _lawful_analysis(grid)
    return False if analysis is None else bool(predicate(analysis))


def _query_order_differs(analysis: dict[str, Any]) -> bool:
    keys = analysis["keys"]
    query = analysis["query"]
    return query != keys[: len(query)]


def _queried_padded_prototype(analysis: dict[str, Any]) -> bool:
    by_key = {prototype["key"]: prototype for prototype in analysis["prototypes"]}
    for key in analysis["query"]:
        mask = by_key[key]["mask"]
        rows = [row for row, _ in mask]
        cols = [col for _, col in mask]
        if max(rows) - min(rows) < 2 or max(cols) - min(cols) < 2:
            return True
    return False


SEMANTIC_WITNESSES = {
    "decoupled_key_and_body_colors": lambda grid: _witness(
        grid, lambda analysis: analysis["color_mode"] == "decoupled"
    ),
    "repeated_query_key": lambda grid: _witness(
        grid, lambda analysis: len(set(analysis["query"])) < len(analysis["query"])
    ),
    "query_omits_library_key": lambda grid: _witness(
        grid, lambda analysis: set(analysis["query"]) < set(analysis["keys"])
    ),
    "query_order_differs_from_library": lambda grid: _witness(grid, _query_order_differs),
    "queried_prototype_has_fixed_3x3_padding": lambda grid: _witness(
        grid, _queried_padded_prototype
    ),
}

WITNESS_RIVALS = {
    "decoupled_key_and_body_colors": ["recolor_by_query_color"],
    "repeated_query_key": ["deduplicate_repeated_query"],
    "query_omits_library_key": ["ignore_query_use_library_order"],
    "query_order_differs_from_library": ["ignore_query_use_library_order"],
    "queried_prototype_has_fixed_3x3_padding": ["tight_crop_each_prototype"],
}


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked canonical layout, palette relation, and query grammar."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) != (6, 11):
        reasons.append("canonical inputs are 6x11")
    if analysis["key_columns"] != [1, 5, 9]:
        reasons.append("canonical keys occupy columns 1, 5, and 9")
    if analysis["color_mode"] != "matched":
        reasons.append("canonical prototype bodies use their key colours")
    if len(set(value for row in grid for value in row)) != 4:
        reasons.append("canonical inputs use background plus three key colours")
    if len(analysis["query"]) not in (3, 4):
        reasons.append("canonical queries contain three or four entries")
    return reasons


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives and changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons: list[str] = []
    checked_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        try:
            truth = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} input is invalid: {exc}")
            continue
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the dictionary rule")
        checked_demos.append(demo)
    try:
        query_truth = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query input is invalid: {exc}")
        return sorted(set(reasons))

    for name, rival in SEMANTIC_RIVALS.items():
        survives = all(rival(demo["input"]) == demo["output"] for demo in checked_demos)
        if survives and rival(query["input"]) != query_truth:
            reasons.append(f"competing rule '{name}' fits every demo but changes the query answer")
    return sorted(set(reasons))

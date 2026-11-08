"""Input grammar and deterministic claims for the 2a6aac780e6d family.

The alternate setting adds a key row ``8 ... 5 ... 8``.  Step A measures
how many columns separate the left key endpoint and selector cell, producing a
1-based rank.  Step B uses that intermediate to choose one qualifying payload
row in top-to-bottom order and fills only that row.  The canonical setting
ignores the key and fills every qualifying row exactly as the selected source
rule does.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

TASK_ID = "2a6aac780e6d"
HERE = Path(__file__).resolve().parent
SCOPES = ("all_qualifying", "key_selected")
PAYLOAD_COLORS = (1, 2, 3, 4, 6, 7, 9)

# height, width, payload count, selector rank, guard count
_DEMO_PROFILES = (
    (9, 13, 3, 1, 2),
    (11, 15, 4, 2, 2),
    (12, 17, 4, 3, 3),
    (14, 18, 5, 2, 3),
    (16, 20, 6, 4, 3),
    (18, 22, 6, 3, 4),
)
_QUERY_PROFILES = (
    (15, 19, 5, 5, 3),
    (19, 23, 6, 1, 4),
    (23, 27, 7, 4, 4),
    (30, 30, 8, 6, 5),
)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"fill_scope"}:
        raise ValueError("settings must contain exactly fill_scope")
    scope = value["fill_scope"]
    if type(scope) is not str or scope not in SCOPES:
        raise ValueError(f"fill_scope must be one of {SCOPES!r}")
    return {"fill_scope": scope}


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact colors 0..9")
    return [row[:] for row in value]


def _row_nonzero(row: list[int]) -> list[tuple[int, int]]:
    return [(c, value) for c, value in enumerate(row) if value != 0]


def _is_payload(row: list[int]) -> bool:
    nonzero = _row_nonzero(row)
    if len(nonzero) != 2 or nonzero[0][1] != nonzero[1][1]:
        return False
    left, right = nonzero[0][0], nonzero[1][0]
    return all(row[c] == 0 for c in range(left + 1, right))


def _key_record(row_index: int, row: list[int]) -> dict[str, int] | None:
    nonzero = _row_nonzero(row)
    if len(nonzero) != 3:
        return None
    eights = [c for c, value in nonzero if value == 8]
    selectors = [c for c, value in nonzero if value == 5]
    if len(eights) != 2 or len(selectors) != 1:
        return None
    left, right = eights
    selector = selectors[0]
    if not left < selector < right:
        return None
    return {
        "row": row_index,
        "left": left,
        "selector": selector,
        "right": right,
        "rank": selector - left,
    }


def analyze(value: object) -> dict[str, object]:
    grid = _grid(value)
    keys = [record for r, row in enumerate(grid) if (record := _key_record(r, row))]
    if len(keys) != 1:
        raise ValueError(f"expected exactly one 8/5/8 key row, got {len(keys)}")
    payload_rows = [r for r, row in enumerate(grid) if _is_payload(row)]
    if len(payload_rows) < 2:
        raise ValueError("parametric grammar needs at least two qualifying payload rows")
    key = keys[0]
    rank = key["rank"]
    if not 1 <= rank <= len(payload_rows):
        raise ValueError("selector rank must identify a payload row")
    nonblank = [r for r, row in enumerate(grid) if any(row)]
    guards = [r for r in nonblank if r != key["row"] and r not in payload_rows]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "key_row": key["row"],
        "key_left": key["left"],
        "selector_col": key["selector"],
        "key_right": key["right"],
        "selector_rank": rank,
        "payload_rows": payload_rows,
        "selected_row": payload_rows[rank - 1],
        "guard_rows": guards,
        "guard_count": len(guards),
    }


def _fill_row(output: list[list[int]], source: list[list[int]], row_index: int) -> None:
    nonzero = _row_nonzero(source[row_index])
    left, color = nonzero[0]
    right = nonzero[1][0]
    for c in range(left, right + 1):
        output[row_index][c] = color


def canonical_output(value: object) -> list[list[int]]:
    source = _grid(value)
    output = [row[:] for row in source]
    for row_index, row in enumerate(source):
        if _is_payload(row):
            _fill_row(output, source, row_index)
    return output


def key_selected_output(value: object) -> list[list[int]]:
    source = _grid(value)
    info = analyze(source)
    output = [row[:] for row in source]
    _fill_row(output, source, int(info["selected_row"]))
    return output


def apply_scope(value: object, scope: str) -> list[list[int]]:
    if scope == "all_qualifying":
        return canonical_output(value)
    if scope == "key_selected":
        return key_selected_output(value)
    raise ValueError(f"unknown fill_scope: {scope!r}")


def program(settings: object) -> str:
    scope = normalize_settings(settings)["fill_scope"]
    filename = "canonical.rkt" if scope == "all_qualifying" else "key_selected.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def counterfactual_program() -> str:
    return (HERE / "always_first.rkt").read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:key-row-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _payload_spec(rng: random.Random, width: int, index: int) -> tuple[int, int, int]:
    color = PAYLOAD_COLORS[index % len(PAYLOAD_COLORS)]
    # Deliberately decorrelate row rank from color and gap length.
    gap = 2 + ((index * 3 + rng.randrange(max(2, width - 6))) % max(2, width - 5))
    gap = min(gap, width - 3)
    left = rng.randrange(0, width - gap - 1)
    right = left + gap + 1
    return left, right, color


def _guard_specs(rng: random.Random, width: int, count: int) -> list[list[int]]:
    guards: list[list[int]] = []
    kinds = ("mismatch", "single", "crowded")
    for index in range(count):
        row = [0] * width
        kind = kinds[index % len(kinds)]
        if kind == "single":
            row[rng.randrange(width)] = PAYLOAD_COLORS[(index + 4) % len(PAYLOAD_COLORS)]
        elif kind == "mismatch":
            left, right = sorted(rng.sample(range(width), 2))
            if right == left + 1:
                right = min(width - 1, right + 1)
                if right == left + 1:
                    left = max(0, left - 1)
            row[left] = PAYLOAD_COLORS[(index + 1) % len(PAYLOAD_COLORS)]
            row[right] = PAYLOAD_COLORS[(index + 2) % len(PAYLOAD_COLORS)]
            if row[left] == row[right]:
                row[right] = PAYLOAD_COLORS[(index + 3) % len(PAYLOAD_COLORS)]
        else:
            cols = sorted(rng.sample(range(width), 3))
            row[cols[0]] = PAYLOAD_COLORS[(index + 2) % len(PAYLOAD_COLORS)]
            row[cols[1]] = PAYLOAD_COLORS[(index + 3) % len(PAYLOAD_COLORS)]
            row[cols[2]] = PAYLOAD_COLORS[(index + 2) % len(PAYLOAD_COLORS)]
            # Never accidentally form the reserved 8/5/8 key signature.
            if [row[c] for c in cols] == [8, 5, 8]:
                row[cols[1]] = 4
        guards.append(row)
    return guards


def make_scene(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    if split == "train":
        if not 0 <= index < len(_DEMO_PROFILES):
            raise ValueError("train profile index out of range")
        height, width, payload_count, rank, guard_count = _DEMO_PROFILES[index]
    elif split == "test":
        if not 0 <= index < len(_QUERY_PROFILES):
            raise ValueError("test profile index out of range")
        height, width, payload_count, rank, guard_count = _QUERY_PROFILES[index]
    else:
        raise ValueError("split must be train or test")
    rng = _rng(seed, split, index)
    rows: list[list[int]] = []
    for payload_index in range(payload_count):
        row = [0] * width
        left, right, color = _payload_spec(rng, width, payload_index + index * 2)
        row[left] = color
        row[right] = color
        rows.append(row)
    rows.extend(_guard_specs(rng, width, guard_count))

    key = [0] * width
    max_left = max(0, width - rank - 4)
    left = rng.randint(0, max_left)
    selector = left + rank
    right_low = selector + 1
    right = rng.randint(right_low, width - 1)
    key[left] = 8
    key[selector] = 5
    key[right] = 8
    rows.append(key)

    rng.shuffle(rows)
    grid = [[0] * width for _ in range(height)]
    slots = sorted(rng.sample(range(height), len(rows)))
    for row_index, content in zip(slots, rows):
        grid[row_index] = content
    info = analyze(grid)
    if info["selector_rank"] != rank or len(info["payload_rows"]) != payload_count:
        raise AssertionError("internal key-row scene construction mismatch")
    return grid


def generate(seed: int, settings: object, demos: int, queries: int) -> dict[str, object]:
    _integer(seed, "seed", 0, 2**63 - 1)
    scope = normalize_settings(settings)["fill_scope"]
    _integer(demos, "demos", 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    train_inputs = [make_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [make_scene(seed, "test", index) for index in range(queries)]
    return {
        "train": [
            {"input": grid, "output": apply_scope(grid, scope)} for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": apply_scope(grid, scope)} for grid in test_inputs
        ],
        "program_solution": program({"fill_scope": scope}),
    }

"""Native recolor-scope family for ARC task 69cab6228fdc."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HOME = Path(__file__).resolve().parent
SETTINGS = ("all_sources", "most_frequent_source")
RIVALS = (
    "first_source_only",
    "last_source_only",
    "least_frequent_source",
    "largest_source_color",
    "zero_unmapped",
)
DEMO_PROFILES = (
    (9, 8, 2, 0.56),
    (12, 12, 3, 0.58),
    (15, 16, 4, 0.60),
    (18, 18, 2, 0.54),
    (22, 24, 3, 0.62),
    (26, 28, 4, 0.64),
)
QUERY_PROFILES = (
    (10, 10, 3, 0.55),
    (16, 20, 4, 0.60),
    (24, 27, 2, 0.58),
    (30, 30, 4, 0.64),
)


def _read_exact(name: str) -> str:
    value = (HOME / name).read_text(encoding="utf-8")
    if not value.strip():
        raise ValueError(f"empty Racket source: {name}")
    return value


CANONICAL_PROGRAM = _read_exact("canonical.rkt")
MOST_FREQUENT_PROGRAM = _read_exact("most_frequent_source.rkt")


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"recolor_scope"}:
        raise ValueError("settings must contain exactly recolor_scope")
    value = settings["recolor_scope"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"recolor_scope must be one of {SETTINGS}")
    return value


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if _setting(settings) == "all_sources" else MOST_FREQUENT_PROGRAM


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 7 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 7..30 rows")
    width = len(grid[0])
    if not 6 <= width <= 30:
        raise ValueError("grid must have 6..30 columns")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def analyze(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    if any(grid[2][col] != 0 for col in range(width)):
        raise ValueError("row 2 must be an all-zero separator")
    active = [col for col in range(width) if grid[0][col] != 0 or grid[1][col] != 0]
    if any((grid[0][col] == 0) != (grid[1][col] == 0) for col in active):
        raise ValueError("legend may not contain half-pairs")
    columns = [col for col in active if grid[0][col] != 0 and grid[1][col] != 0]
    if not 2 <= len(columns) <= 4:
        raise ValueError("legend must contain two through four pairs")
    sources = [grid[0][col] for col in columns]
    targets = [grid[1][col] for col in columns]
    if len(set(sources)) != len(sources) or len(set(targets)) != len(targets):
        raise ValueError("legend source and target colors must be distinct within each row")
    if set(sources) & set(targets):
        raise ValueError("legend source and target palettes must be disjoint")
    mapping = dict(zip(sources, targets, strict=True))
    body = grid[3:]
    values = [value for row in body for value in row]
    if any(value in set(targets) for value in values):
        raise ValueError("target colors must not appear in the input body")
    source_counts = {source: values.count(source) for source in sources}
    if any(count == 0 for count in source_counts.values()):
        raise ValueError("every legend source must appear in the body")
    maximum = max(source_counts.values())
    winners = [source for source, count in source_counts.items() if count == maximum]
    if len(winners) != 1:
        raise ValueError("the body must have one unique most-frequent legend source")
    passthrough = sorted(set(values) - {0, *sources, *targets})
    if not 1 <= len(passthrough) <= 2:
        raise ValueError("body must contain one or two unmapped passthrough colors")
    if any(values.count(color) < 2 for color in passthrough):
        raise ValueError("each passthrough color must appear at least twice")
    return {
        "height": height,
        "width": width,
        "pair_columns": columns,
        "n_pairs": len(columns),
        "sources": sources,
        "targets": targets,
        "mapping": mapping,
        "source_counts": source_counts,
        "most_frequent_source": winners[0],
        "passthrough_colors": passthrough,
        "body_nonzero": sum(value != 0 for value in values),
    }


def transform(grid: Any, recolor_scope: str) -> list[list[int]]:
    if type(recolor_scope) is not str or recolor_scope not in SETTINGS:
        raise ValueError(f"recolor_scope must be one of {SETTINGS}")
    facts = analyze(grid)
    selected = facts["most_frequent_source"]
    mapping = facts["mapping"]
    if recolor_scope == "all_sources":
        return [[mapping.get(value, value) for value in row] for row in grid[3:]]
    return [[mapping[value] if value == selected else value for value in row] for row in grid[3:]]


def _selected_for_rival(facts: dict[str, Any], name: str) -> int:
    if name == "first_source_only":
        return facts["sources"][0]
    if name == "last_source_only":
        return facts["sources"][-1]
    if name == "least_frequent_source":
        return min(facts["source_counts"], key=facts["source_counts"].get)
    if name == "largest_source_color":
        return max(facts["sources"])
    raise ValueError(name)


def rival_transform(grid: Any, name: str) -> list[list[int]]:
    if name not in RIVALS:
        raise ValueError(f"unknown rival: {name}")
    facts = analyze(grid)
    mapping = facts["mapping"]
    if name == "zero_unmapped":
        return [[mapping.get(value, 0) for value in row] for row in grid[3:]]
    selected = _selected_for_rival(facts, name)
    return [[mapping[value] if value == selected else value for value in row] for row in grid[3:]]


def _selector_program(expression: str) -> str:
    return f"""(rule! (let ((dummy 0))
  (define (t10-alist-ref pairs key default)
    (let ((hits (filter (lambda (p) (= (first p) key)) pairs)))
      (if (empty? hits) default (second (first hits)))))
  (define (t10-body-count color)
    (for*/sum ((r (range 3 (rows g))) (c (range 0 (cols g))))
      (if (= (at g r c) color) 1 0)))
  (let* ((pairs (filter (lambda (p) (and (not (= (first p) 0)) (not (= (second p) 0))))
                        (map list (row g 0) (row g 1))))
         (selected {expression}))
    (grid-from-fn (- (rows g) 3) (cols g)
      (lambda (r c)
        (let ((v (at g (+ r 3) c)))
          (if (= v selected) (t10-alist-ref pairs v v) v)))))))"""


def rival_program(name: str) -> str:
    if name not in RIVALS:
        raise ValueError(f"unknown rival: {name}")
    if name == "zero_unmapped":
        anchor = "(t10-alist-ref pairs v v)"
        if CANONICAL_PROGRAM.count(anchor) != 1:
            raise ValueError("canonical passthrough anchor changed")
        return CANONICAL_PROGRAM.replace(anchor, "(t10-alist-ref pairs v 0)")
    expression = {
        "first_source_only": "(first (first pairs))",
        "last_source_only": "(first (first (reverse pairs)))",
        "least_frequent_source": "(second (first (sort (map (lambda (p) (list (t10-body-count (first p)) (first p))) pairs) (lambda (a b) (< (first a) (first b))))))",
        "largest_source_color": "(max-list (map first pairs))",
    }[name]
    return _selector_program(expression)


def _rng(seed: int, split: str, index: int, label: str) -> random.Random:
    raw = f"69cab6228fdc|{seed}|{split}|{index}|{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _legend_columns(width: int, n_pairs: int, seed: int, split: str, index: int) -> list[int]:
    rng = _rng(seed, split, index, "columns")
    if index % 2 == 0:
        start = rng.randint(0, width - n_pairs)
        return list(range(start, start + n_pairs))
    candidates = list(range(width))
    rng.shuffle(candidates)
    return sorted(candidates[:n_pairs])


def _counts(total: int, n_pairs: int, selected_index: int, seed: int, split: str, index: int) -> list[int]:
    order = [value for value in range(n_pairs) if value != selected_index]
    _rng(seed, split, index, "count-ranks").shuffle(order)
    order.append(selected_index)
    bases = [3 + 2 * rank for rank in range(n_pairs)]
    if total < sum(bases):
        raise ValueError("body profile is too small for distinct source counts")
    quotient, remainder = divmod(total - sum(bases), n_pairs)
    ranked = [base + quotient + (1 if rank < remainder else 0) for rank, base in enumerate(bases)]
    result = [0] * n_pairs
    for rank, source_index in enumerate(order):
        result[source_index] = ranked[rank]
    if result[selected_index] != max(result) or result.count(max(result)) != 1:
        raise AssertionError("selected source is not the unique count maximum")
    return result


def _make_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    height, width, n_pairs, density = profiles[index]
    palette_rng = _rng(seed, split, index, "palette")
    palette = palette_rng.sample(range(1, 10), 2 * n_pairs)
    sources = palette[:n_pairs]
    targets = palette[n_pairs:]
    selected_index = index % n_pairs
    # Keep the intended selector visibly different from a color-order shortcut.
    if sources[selected_index] == max(sources):
        swap = next(position for position in range(n_pairs) if position != selected_index and sources[position] != max(sources))
        sources[selected_index], sources[swap] = sources[swap], sources[selected_index]
    unused = [color for color in range(1, 10) if color not in {*sources, *targets}]
    passthrough = unused[: min(2, len(unused))]
    if not passthrough:
        raise AssertionError("at least one passthrough color is required")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for column, source, target in zip(_legend_columns(width, n_pairs, seed, split, index), sources, targets, strict=True):
        grid[0][column] = source
        grid[1][column] = target

    body_positions = [(row, col) for row in range(3, height) for col in range(width)]
    occupied = max(sum(3 + 2 * rank for rank in range(n_pairs)) + 2 * len(passthrough), int(len(body_positions) * density))
    passthrough_counts = [max(2, len(body_positions) // (80 + 10 * position)) for position in range(len(passthrough))]
    source_total = occupied - sum(passthrough_counts)
    source_counts = _counts(source_total, n_pairs, selected_index, seed, split, index)
    values: list[int] = []
    for source, count in zip(sources, source_counts, strict=True):
        values.extend([source] * count)
    for color, count in zip(passthrough, passthrough_counts, strict=True):
        values.extend([color] * count)
    if len(values) > len(body_positions):
        raise AssertionError("body occupancy exceeds the canvas")
    rng = _rng(seed, split, index, "body")
    rng.shuffle(body_positions)
    rng.shuffle(values)
    for (row, col), value in zip(body_positions, values, strict=False):
        grid[row][col] = value
    facts = analyze(grid)
    if facts["most_frequent_source"] != sources[selected_index]:
        raise AssertionError("constructed most-frequent source changed")
    return grid


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    recolor_scope = _setting(settings)
    train_inputs = [_make_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_make_input(seed, "test", index) for index in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise AssertionError("generated inputs must be distinct")

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, recolor_scope)}

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(settings),
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(query_index) is not int or type(episode) is not dict:
        raise ValueError("query_index must be an exact integer")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("query_index is outside the available queries")
    try:
        return {
            "train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in train],
            "test": [{"input": deepcopy(test[query_index]["input"])}],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs are malformed") from error

"""Proposed finite-rival lesson gate for 6fde852adb54; no production hook.

The caller supplies the canonical predictor. Production use must provide the
pinned Racket rule or a cache of outputs verified by that exact rule. This gate
never reads query output, and a pass covers only the declared run-length rival.
"""
from __future__ import annotations

import hashlib
import importlib.util
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = TASK_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared/runtime"))
_SPEC = importlib.util.spec_from_file_location(
    "question_gate_generator_6fde852adb54", TASK_ROOT / "generator.py"
)
GENERATOR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GENERATOR)
RIVAL_ID = "longest_contiguous_vertical_run"
SCOPE = "one declared rival; not universal identifiability or training approval"


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _grid_size(grid):
    if not isinstance(grid, list) or not grid:
        return None
    if not all(isinstance(row, list) and row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    if any(not _integer(v) or not 0 <= v <= 9 for row in grid for v in row):
        return None
    return len(grid), width


def difference_cells(first, second):
    if _grid_size(first) is None or _grid_size(first) != _grid_size(second):
        raise ValueError("outputs must be equally sized rectangular ARC grids")
    return sum(a != b for ar, br in zip(first, second) for a, b in zip(ar, br))


def column_run_lengths(component):
    rows = defaultdict(list)
    for row, col in component:
        rows[col].append(row)
    scores = {}
    for col, values in rows.items():
        longest = length = 0
        previous = None
        for row in sorted(set(values)):
            length = length + 1 if previous is not None and row == previous + 1 else 1
            longest = max(longest, length)
            previous = row
        scores[col] = longest
    return scores


def rival_predict(grid):
    """Canonical mechanics except near-floor destination uses longest run.

    Ties still prefer the nearest column, then the lower column index. Shelf
    clearing still uses actual occupancy counts, so only the destination
    selection hypothesis changes. All components are read from the input.
    """
    parsed = GENERATOR._parse(grid)
    if parsed["errors"] or parsed["facts"] is None:
        raise ValueError("invalid scene: " + "; ".join(parsed["errors"]))
    facts = parsed["facts"]
    height, width = facts["height"], facts["width"]
    background, body, tip, obstacle = facts["palette"]
    output = [list(row) for row in grid]
    for col in facts["mover_cols"]:
        for row in range(3):
            output[row][col] = background
    for col in facts["mover_cols"]:
        hits = [row for row in range(3, height) if grid[row][col] == obstacle]
        if grid[2][col] == tip:
            land = hits[0] - 1 if hits else height - 1
            output[land - 2][col] = body
            output[land - 1][col] = body
            output[land][col] = tip
            continue
        landing_col = col
        if hits and hits[-1] >= height - 2:
            component = next(cells for cells in facts["obstacle_components"]
                             if (hits[-1], col) in cells)
            counts = Counter(cell_col for _, cell_col in component)
            scores = column_run_lengths(component)
            maximum = max(scores.values())
            candidates = [cell_col for cell_col, score in scores.items() if score == maximum]
            landing_col = min(candidates, key=lambda cc: (abs(cc - col), cc))
            if set(counts.values()) == {1}:
                bar_row = component[0][0]
                left = sum(cc < landing_col for cc in counts)
                right = sum(cc > landing_col for cc in counts)
                step = 1 if right >= left else -1
                for offset in range(1, len(facts["mover_cols"])):
                    cc = landing_col + step * offset
                    if 0 <= cc < width and grid[bar_row][cc] == obstacle:
                        output[bar_row][cc] = background
        for row in range(height - 3, height):
            output[row][landing_col] = body
    return output


def make_witness(*, height=14, width=14, start=3,
                 palette=(7, 9, 1, 5), reflected=False):
    """A lawful count-versus-run discriminator, with five obstacle components.

    The source body column has a run of three obstacle cells. Its neighbor has
    four obstacle cells in two separated runs, and wins the canonical count.
    The two remaining mover slices are tips and fall directly to the floor.
    This constructor belongs to this proposed question workspace, not generate().
    """
    if not _integer(height) or not 14 <= height <= 24:
        raise ValueError("height must be an integer in 14..24")
    if not _integer(width) or not 14 <= width <= 24:
        raise ValueError("width must be an integer in 14..24")
    if not _integer(start) or not 2 <= start <= width - 5:
        raise ValueError("start must leave space for the gapped component")
    if (not isinstance(palette, (tuple, list)) or len(palette) != 4
            or any(not _integer(v) or not 0 <= v <= 9 for v in palette)
            or len(set(palette)) != 4):
        raise ValueError("palette must contain four distinct integer ARC colors")
    if not isinstance(reflected, bool):
        raise ValueError("reflected must be a bool")
    background, body, tip, obstacle = palette
    grid = [[background] * width for _ in range(height)]
    for row in (0, 1):
        for col in range(start, start + 3):
            grid[row][col] = body
    grid[2][start:start + 3] = [tip, tip, body]
    source = start + 2
    component = {(height - offset, source) for offset in (3, 2, 1)}
    component.update((height - offset, source + 1) for offset in (6, 4, 3, 1))
    component.update((height - offset, source + 2) for offset in (6, 5, 4))
    component.update((row, 0) for row in (3, 5, 7, 9))
    for row, col in component:
        grid[row][col] = obstacle
    if reflected:
        grid = [list(reversed(row)) for row in grid]
    errors = GENERATOR.self_check(grid)
    if errors:
        raise RuntimeError("witness construction violated scene grammar: " + "; ".join(errors))
    return grid


def sample_witness(seed, sample_index):
    """Deterministic proposed witness sampler; every draw separates the rival."""
    if not _integer(seed) or not _integer(sample_index) or sample_index < 0:
        raise ValueError("seed must be an integer and sample_index a nonnegative integer")
    digest = hashlib.sha256(f"question-witness-v1|{seed}|{sample_index}".encode()).digest()
    rng = random.Random(digest)
    height, width = rng.randint(14, 24), rng.randint(14, 24)
    return make_witness(height=height, width=width, start=rng.randint(2, width - 5),
                        palette=rng.sample(range(10), 4), reflected=bool(rng.randrange(2)))


def lesson_gate(demos, query, *, canonical_predict):
    """Check query-relevant ambiguity against one explicit rival.

    Demonstration labels are verified through canonical_predict. Query labels
    and private metadata are ignored. Invalid data and a failed reference
    predictor cannot produce pass. A surviving rival is allowed when it gives
    the same query answer as the canonical predictor.
    """
    result = {"schema": "arcpuzzles-question-gate-v1", "status": "invalid",
              "rival_id": RIVAL_ID, "scope": SCOPE, "demo_matches": [],
              "query_difference_cells": None, "reasons": []}

    def invalid(reason):
        result["reasons"].append(reason)
        return result

    if not isinstance(query, Mapping) or "input" not in query:
        return invalid("query must contain input")
    query_grid = query["input"]
    if _grid_size(query_grid) is None:
        return invalid("query input must be a rectangular ARC grid")
    try:
        errors = GENERATOR.self_check(query_grid)
    except (ValueError, TypeError, IndexError, KeyError) as exc:
        return invalid("query validation failed: " + type(exc).__name__)
    if errors:
        return invalid("invalid query input: " + "; ".join(errors))
    if not isinstance(demos, (list, tuple)) or not demos:
        return invalid("at least one demonstration is required")
    for index, demo in enumerate(demos):
        if not isinstance(demo, Mapping) or "input" not in demo or "output" not in demo:
            return invalid(f"demo {index} requires input and output")
        if _grid_size(demo["input"]) is None:
            return invalid(f"demo {index} input is not a rectangular ARC grid")
        try:
            errors = GENERATOR.self_check(demo["input"])
        except (ValueError, TypeError, IndexError, KeyError) as exc:
            return invalid(f"demo {index} validation failed: {type(exc).__name__}")
        if errors:
            return invalid(f"demo {index} input is invalid: " + "; ".join(errors))
        if _grid_size(demo["output"]) != _grid_size(demo["input"]):
            return invalid(f"demo {index} output has invalid colors or dimensions")
    try:
        for index, demo in enumerate(demos):
            predicted = canonical_predict([list(row) for row in demo["input"]])
            if _grid_size(predicted) != _grid_size(demo["input"]):
                raise ValueError("reference returned an invalid output grid")
            if predicted != demo["output"]:
                return invalid(f"demo {index} output disagrees with the canonical predictor")
        query_prediction = canonical_predict([list(row) for row in query_grid])
        if _grid_size(query_prediction) != _grid_size(query_grid):
            raise ValueError("reference returned an invalid query output grid")
    except Exception as exc:
        result["status"] = "reference_error"
        result["reasons"].append("canonical predictor failed: " + type(exc).__name__)
        return result
    result["demo_matches"] = [rival_predict(demo["input"]) == demo["output"] for demo in demos]
    result["query_difference_cells"] = difference_cells(query_prediction, rival_predict(query_grid))
    if all(result["demo_matches"]) and result["query_difference_cells"]:
        result["status"] = "ambiguous"
        result["reasons"].append("rival fits every demonstration and changes the query answer")
    else:
        result["status"] = "pass"
    return result

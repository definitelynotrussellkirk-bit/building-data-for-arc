#!/usr/bin/env python3
"""Source-bound reasoning probe for public ARC evaluation task 16de56c4.

This is a separate proposed extension, not a replacement for generator
74a14031dc79.  It infers the dominant line orientation from repeated-color
anchor groups, completes each anchor arithmetic progression, and treats one
external different-color point on that progression as a recoloring endpoint.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from math import gcd
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id

PARENT_TASK_ID = "16de56c4"
CHALLENGE_SHA256 = "04f2c3b7aed8c16f787c41eb38d771d28bed8c54f4c649596974d8457a24edfd"
RACKET_SOURCE_SHA256 = "dc53ff9b90a291d3e35f56ca4cda17e1dcc66810787e2db2a15480ef67635593"
ORIENTATIONS = ("horizontal", "vertical")

EXTRA_QUERY_INPUTS = (
    (
        (9, 0, 9, 0, 0, 0, 6, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 1, 0, 0, 0, 0, 0, 0, 0),
    ),
    (
        (0, 2, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 2, 0, 0, 6),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 6),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    ),
)

Grid = list[list[int]]


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _grid_sha256(grid: Grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def racket_source() -> str:
    """Return the exact proposed Racket rule, guarded by its retained hash."""
    path = Path(__file__).with_name("rule.rkt")
    source = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(source.encode()).hexdigest()
    if digest != RACKET_SOURCE_SHA256:
        raise ValueError(f"public-focus Racket source drift: {digest}")
    return source


def _racket_callable(source: str) -> str:
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")\n"):
        raise ValueError("Racket source must be exactly one rule! form")
    return source[len(prefix) : -2]


def execute_racket(
    grids: Iterable[Any],
    *,
    bridge: RacketBridge | None = None,
) -> list[Grid]:
    """Execute the exact proposed rule over one or more grids in real Racket."""
    normalized = [_coerce_grid(grid) for grid in grids]
    if not normalized:
        raise ValueError("at least one grid is required")
    grid_literals = [
        "(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        for grid in normalized
    ]
    expression = (
        f"(map {_racket_callable(racket_source())} "
        + "'(" + " ".join(grid_literals) + "))"
    )
    if bridge is None:
        with RacketBridge() as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    return [_coerce_grid(grid) for grid in result]


def four_query_inputs(challenge: dict[str, Any]) -> list[Grid]:
    """Return the two public queries plus two distinct proposed support queries."""
    if not isinstance(challenge, dict) or not isinstance(challenge.get("test"), list):
        raise ValueError("challenge must contain a test list")
    if len(challenge["test"]) != 2:
        raise ValueError("the pinned public challenge must contain exactly two queries")
    queries = [_coerce_grid(pair["input"]) for pair in challenge["test"]]
    queries.extend(_coerce_grid(grid) for grid in EXTRA_QUERY_INPUTS)
    training = [_coerce_grid(pair["input"]) for pair in challenge.get("train", [])]
    hashes = [_grid_sha256(grid) for grid in training + queries]
    if len(hashes) != len(set(hashes)):
        raise AssertionError("four-query support contains a duplicate input")
    return queries


def _coerce_grid(grid: Any) -> Grid:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty sequence of rows")
    rows: Grid = []
    width: int | None = None
    for row in grid:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError("grid rows must be nonempty sequences")
        values: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("ARC cells must be integers in 0..9")
            values.append(value)
        if width is None:
            width = len(values)
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        rows.append(values)
    return rows


def _line_count(grid: Grid, orientation: str) -> int:
    return len(grid) if orientation == "horizontal" else len(grid[0])


def _position_count(grid: Grid, orientation: str) -> int:
    return len(grid[0]) if orientation == "horizontal" else len(grid)


def _cell(grid: Grid, orientation: str, line: int, position: int) -> int:
    if orientation == "horizontal":
        return grid[line][position]
    return grid[position][line]


def _set_cell(
    grid: Grid,
    orientation: str,
    line: int,
    position: int,
    color: int,
) -> None:
    if orientation == "horizontal":
        grid[line][position] = color
    else:
        grid[position][line] = color


def repeated_color_groups(grid: Any, orientation: str) -> list[dict[str, Any]]:
    """Return every same-color line group with at least two anchor cells."""
    original = _coerce_grid(grid)
    if orientation not in ORIENTATIONS:
        raise ValueError(f"orientation must be one of {ORIENTATIONS}")
    groups: list[dict[str, Any]] = []
    for line in range(_line_count(original, orientation)):
        positions_by_color: dict[int, list[int]] = defaultdict(list)
        for position in range(_position_count(original, orientation)):
            color = _cell(original, orientation, line, position)
            if color != 0:
                positions_by_color[color].append(position)
        for color, anchors in positions_by_color.items():
            if len(anchors) < 2:
                continue
            step = 0
            for left, right in zip(anchors, anchors[1:]):
                step = gcd(step, right - left)
            if step <= 0:
                raise ValueError("repeated anchors must occupy distinct positions")
            groups.append(
                {
                    "orientation": orientation,
                    "line": line,
                    "color": color,
                    "anchors": anchors,
                    "step": step,
                    "residue": anchors[0] % step,
                }
            )
    return groups


def analyze(grid: Any) -> dict[str, Any]:
    """Infer the dominant orientation and expose its anchor groups."""
    original = _coerce_grid(grid)
    horizontal = repeated_color_groups(original, "horizontal")
    vertical = repeated_color_groups(original, "vertical")
    counts = {"horizontal": len(horizontal), "vertical": len(vertical)}
    if counts["horizontal"] == counts["vertical"]:
        raise ValueError(
            "orientation is ambiguous: repeated-color group counts are tied "
            f"at {counts['horizontal']}"
        )
    orientation = (
        "horizontal"
        if counts["horizontal"] > counts["vertical"]
        else "vertical"
    )
    groups = horizontal if orientation == "horizontal" else vertical
    return {
        "orientation": orientation,
        "group_counts": counts,
        "groups": groups,
    }


def _planned_group_writes(
    original: Grid,
    group: dict[str, Any],
) -> list[tuple[int, int, int]]:
    orientation = group["orientation"]
    line = group["line"]
    color = group["color"]
    anchors = group["anchors"]
    step = group["step"]
    residue = group["residue"]
    position_count = _position_count(original, orientation)

    on_lattice_other_colors: list[tuple[int, int]] = []
    for position in range(position_count):
        value = _cell(original, orientation, line, position)
        if value not in (0, color) and position % step == residue:
            on_lattice_other_colors.append((position, value))

    anchor_low, anchor_high = min(anchors), max(anchors)
    external_markers = [
        marker
        for marker in on_lattice_other_colors
        if marker[0] < anchor_low or marker[0] > anchor_high
    ]
    internal_markers = [
        marker
        for marker in on_lattice_other_colors
        if anchor_low <= marker[0] <= anchor_high
    ]
    if internal_markers:
        raise ValueError(
            "an on-lattice different-color cell lies inside the anchor span; "
            "the public demonstrations do not identify that case"
        )
    if len(external_markers) > 1:
        raise ValueError(
            "multiple external on-lattice terminal markers are ambiguous"
        )

    if external_markers:
        terminal_position, paint = external_markers[0]
        low = min(anchor_low, terminal_position)
        high = max(anchor_high, terminal_position)
        positions: Iterable[int] = range(low, high + 1, step)
    else:
        paint = color
        positions = range(residue, position_count, step)

    writes: list[tuple[int, int, int]] = []
    for position in positions:
        row, col = (
            (line, position)
            if orientation == "horizontal"
            else (position, line)
        )
        writes.append((row, col, paint))
    return writes


def solve(grid: Any) -> Grid:
    """Apply the inferred progression/terminal-marker rule to one grid."""
    original = _coerce_grid(grid)
    analysis = analyze(original)
    planned: dict[tuple[int, int], int] = {}
    for group in analysis["groups"]:
        for row, col, color in _planned_group_writes(original, group):
            key = (row, col)
            previous = planned.get(key)
            if previous is not None and previous != color:
                raise ValueError(
                    f"conflicting progression writes at row {row}, col {col}: "
                    f"{previous} versus {color}"
                )
            planned[key] = color

    output = deepcopy(original)
    for (row, col), color in planned.items():
        output[row][col] = color
    return output


def solve_challenge(challenge: dict[str, Any]) -> dict[str, Any]:
    """Replay public demonstrations and predict all public query outputs."""
    if not isinstance(challenge, dict):
        raise ValueError("challenge must be an object")
    digest = hashlib.sha256(_canonical_json_bytes(challenge)).hexdigest()
    train = challenge.get("train")
    test = challenge.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("challenge must contain train and test lists")

    mismatches: list[dict[str, Any]] = []
    training_analysis: list[dict[str, Any]] = []
    for index, pair in enumerate(train):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            raise ValueError("every training pair must contain input and output")
        predicted = solve(pair["input"])
        if predicted != pair["output"]:
            mismatches.append(
                {
                    "index": index,
                    "predicted_sha256": _grid_sha256(predicted),
                    "expected_sha256": _grid_sha256(pair["output"]),
                }
            )
        row = analyze(pair["input"])
        training_analysis.append(
            {
                "index": index,
                "orientation": row["orientation"],
                "group_counts": row["group_counts"],
            }
        )

    predictions: list[Grid] = []
    query_analysis: list[dict[str, Any]] = []
    for index, pair in enumerate(test):
        if not isinstance(pair, dict) or "input" not in pair:
            raise ValueError("every test pair must contain input")
        predicted = solve(pair["input"])
        predictions.append(predicted)
        row = analyze(pair["input"])
        query_analysis.append(
            {
                "index": index,
                "orientation": row["orientation"],
                "group_counts": row["group_counts"],
                "prediction_sha256": _grid_sha256(predicted),
            }
        )

    return {
        "schema": "arcpuzzles-public-focus-probe-v1",
        "status": "verified_on_public_demonstrations" if not mismatches else "training_mismatch",
        "parent_task_id": PARENT_TASK_ID,
        "challenge_sha256": digest,
        "reasoning": {
            "orientation": (
                "Count row-wise and column-wise same-color groups with at least two "
                "anchors; use the orientation with the larger count."
            ),
            "progression": (
                "Use the gcd of anchor gaps as the lattice step. Without an external "
                "on-lattice different-color marker, extend that lattice to both grid edges."
            ),
            "terminal_marker": (
                "A unique external different-color marker on the same lattice becomes "
                "the paint color and terminal endpoint; recolor only the segment joining it "
                "to the anchors. Off-lattice cells remain unchanged."
            ),
        },
        "training_pairs_verified": len(train) - len(mismatches),
        "training_pair_count": len(train),
        "training_mismatches": mismatches,
        "training_analysis": training_analysis,
        "query_count": len(test),
        "query_analysis": query_analysis,
        "query_predictions": predictions,
        "limits": [
            "Only the three public demonstrations supervise the inferred rule.",
            "Equal horizontal/vertical evidence is rejected rather than guessed.",
            "Multiple external on-lattice markers or an internal marker are rejected.",
            "The public evaluation queries have no labels here, so predictions are unverified.",
            "The geometry is structurally unrelated to the selected 3+separator+3 occupancy family; no production transfer is claimed.",
        ],
    }


def build_evidence(
    challenge: dict[str, Any],
    *,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build a four-query, matching-Racket evidence record for the proposal."""
    report = solve_challenge(challenge)
    query_inputs = four_query_inputs(challenge)
    training_inputs = [_coerce_grid(pair["input"]) for pair in challenge["train"]]
    expected_training = [_coerce_grid(pair["output"]) for pair in challenge["train"]]
    racket_outputs = execute_racket(training_inputs + query_inputs, bridge=bridge)
    if racket_outputs[: len(training_inputs)] != expected_training:
        raise AssertionError("proposed Racket rule does not replay all public demonstrations")

    query_outputs = racket_outputs[len(training_inputs) :]
    python_query_outputs = [solve(grid) for grid in query_inputs]
    if query_outputs != python_query_outputs:
        raise AssertionError("Python reasoning probe and proposed Racket rule disagree")

    private_test = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(query_inputs, query_outputs)
    ]
    public = {
        "train": deepcopy(challenge["train"]),
        "test": [{"input": deepcopy(grid)} for grid in query_inputs],
    }
    source = racket_source()
    solver_path = Path(__file__)
    rule_path = solver_path.with_name("rule.rkt")
    report.update(
        {
            "status": "verified_on_public_demonstrations_with_matching_racket",
            "racket": {
                "source_path": (
                    "generators/74a14031dc79/workspace/"
                    "public_focus_16de56c4/rule.rkt"
                ),
                "source_sha256": RACKET_SOURCE_SHA256,
                "source": source,
                "labels_checked": len(racket_outputs),
                "public_demonstration_labels_checked": len(training_inputs),
                "query_labels_checked_under_proposed_rule": len(query_inputs),
                "python_parity": True,
            },
            "four_query_episode": {
                "train": deepcopy(challenge["train"]),
                "test": private_test,
                "demo_count": len(training_inputs),
                "query_count": len(query_inputs),
                "public_query_count": len(challenge["test"]),
                "support_query_count": len(EXTRA_QUERY_INPUTS),
                "query_provenance": [
                    "public_evaluation_unlabeled",
                    "public_evaluation_unlabeled",
                    "proposed_support_query",
                    "proposed_support_query",
                ],
            },
            "public_challenge": public,
            "public_challenge_id": public_challenge_id(public),
            "public_challenge_sha256": hashlib.sha256(
                public_challenge_bytes(public)
            ).hexdigest(),
            "sources": [
                {
                    "path": (
                        "generators/74a14031dc79/workspace/"
                        "public_focus_16de56c4/solver.py"
                    ),
                    "sha256": hashlib.sha256(solver_path.read_bytes()).hexdigest(),
                },
                {
                    "path": (
                        "generators/74a14031dc79/workspace/"
                        "public_focus_16de56c4/rule.rkt"
                    ),
                    "sha256": hashlib.sha256(rule_path.read_bytes()).hexdigest(),
                },
            ],
        }
    )
    report["limits"].append(
        "The two extra queries are proposed support cases, not hidden evaluation examples; all four outputs are labels under this proposed Racket rule only."
    )
    return report


def _default_source() -> Path:
    repo = Path(__file__).resolve().parents[4]
    return repo / "shared/data/raw/arc-agi_evaluation_challenges.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=_default_source())
    parser.add_argument("--task-id", default=PARENT_TASK_ID)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.task_id != PARENT_TASK_ID:
        raise ValueError(f"this source-bound probe only supports {PARENT_TASK_ID}")
    if args.out.exists():
        raise FileExistsError(args.out)
    all_challenges = json.loads(args.source.read_text(encoding="utf-8"))
    challenge = all_challenges[args.task_id]
    report = build_evidence(challenge)
    if report["challenge_sha256"] != CHALLENGE_SHA256:
        raise ValueError(
            "public challenge source drift: " + report["challenge_sha256"]
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "parent_task_id": PARENT_TASK_ID,
                "challenge_sha256": report["challenge_sha256"],
                "training_pairs_verified": report["training_pairs_verified"],
                "query_count": report["query_count"],
                "four_query_count": report["four_query_episode"]["query_count"],
                "racket_source_sha256": report["racket"]["source_sha256"],
                "prediction_sha256": [
                    row["prediction_sha256"] for row in report["query_analysis"]
                ],
                "out": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return (
        0
        if report["status"]
        == "verified_on_public_demonstrations_with_matching_racket"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Proposed episode-level spiral-direction variant for c1ae510562f9.

This task-local prototype is outside the selected production path. ``clockwise``
is the canonical rule byte-for-byte; ``counterclockwise`` changes only the 3x3
output traversal used after counting wholly empty container rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

TASK_ID = "c1ae510562f9"
SCHEMA = f"{TASK_ID}-spiral-direction-prototype-v1"
PUBLIC_SCHEMA = f"{TASK_ID}-spiral-direction-public-challenge-v1"
ALLOWED_DIRECTIONS = ("clockwise", "counterclockwise")
DEFAULT_DIRECTION = "clockwise"
Grid = list[list[int]]

_CLOCKWISE_SPIRAL = (
    (0, 0), (0, 1), (0, 2), (1, 2), (2, 2),
    (2, 1), (2, 0), (1, 0), (1, 1),
)
_COUNTERCLOCKWISE_SPIRAL = (
    (0, 0), (1, 0), (2, 0), (2, 1), (2, 2),
    (1, 2), (0, 2), (0, 1), (1, 1),
)
_SPIRALS = {
    "clockwise": _CLOCKWISE_SPIRAL,
    "counterclockwise": _COUNTERCLOCKWISE_SPIRAL,
}

# Exact canonical source. Keeping the default literal exact makes authority drift
# visible through the normalized hash check rather than silently regenerating it.
_CLOCKWISE_RULE = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((fives (find-color g 5))
                  (min-r (min-of fst fives))
                  (max-r (max-of fst fives))
                  (min-c (min-of snd fives))
                  (max-c (max-of snd fives))
                  (spiral (list (list 0 0)
                                (list 0 1)
                                (list 0 2)
                                (list 1 2)
                                (list 2 2)
                                (list 2 1)
                                (list 2 0)
                                (list 1 0)
                                (list 1 1)))
                  (empty (count-if (lambda (r)
                                     (for/and ((c (range (+ min-c 1) max-c)))
                                              (zero? (at g r c))))
                                   (range min-r max-r))))
             (build-grid 3
                         3
                         (r c)
                         (let ((idx (find-first (lambda (i)
                                                  (and
                                                    (= r (fst (nth spiral i)))
                                                    (= c (snd (nth spiral i)))))
                                                (range 0 9))))
                           (if (and idx (< idx empty)) 8 0)))))))"""

_COUNTERCLOCKWISE_RULE = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((fives (find-color g 5))
                  (min-r (min-of fst fives))
                  (max-r (max-of fst fives))
                  (min-c (min-of snd fives))
                  (max-c (max-of snd fives))
                  (spiral (list (list 0 0)
                                (list 1 0)
                                (list 2 0)
                                (list 2 1)
                                (list 2 2)
                                (list 1 2)
                                (list 0 2)
                                (list 0 1)
                                (list 1 1)))
                  (empty (count-if (lambda (r)
                                     (for/and ((c (range (+ min-c 1) max-c)))
                                              (zero? (at g r c))))
                                   (range min-r max-r))))
             (build-grid 3
                         3
                         (r c)
                         (let ((idx (find-first (lambda (i)
                                                  (and
                                                    (= r (fst (nth spiral i)))
                                                    (= c (snd (nth spiral i)))))
                                                (range 0 9))))
                           (if (and idx (< idx empty)) 8 0)))))))"""

_RULES = {
    "clockwise": _CLOCKWISE_RULE,
    "counterclockwise": _COUNTERCLOCKWISE_RULE,
}


def _validate_direction(direction: str) -> str:
    if direction not in ALLOWED_DIRECTIONS:
        raise ValueError(
            f"direction must be one of {ALLOWED_DIRECTIONS}, got {direction!r}"
        )
    return direction


def normalize_rule(source: str) -> str:
    if not isinstance(source, str) or not source.strip():
        raise ValueError("rule source must be a nonempty string")
    return " ".join(source.split())


def normalized_hash(source: str) -> str:
    return hashlib.sha256(normalize_rule(source).encode("utf-8")).hexdigest()[:12]


def materialize_rule(direction: str = DEFAULT_DIRECTION) -> str:
    return _RULES[_validate_direction(direction)]


def _validate_grid(grid: Any) -> Grid:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0]) if isinstance(grid[0], list) else 0
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        raise ValueError("grid must contain equal-width nonempty rows")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid values must be integer ARC colors 0..9")
    return [row[:] for row in grid]


def _gray_bounds(grid: Grid) -> tuple[int, int, int, int]:
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if not points:
        raise ValueError("grid must contain a gray container")
    return (
        min(r for r, _ in points),
        max(r for r, _ in points),
        min(c for _, c in points),
        max(c for _, c in points),
    )


def empty_row_count(grid: Any) -> int:
    source = _validate_grid(grid)
    top, floor, left, right = _gray_bounds(source)
    return sum(
        all(source[r][c] == 0 for c in range(left + 1, right))
        for r in range(top, floor)
    )


def python_mirror(grid: Any, direction: str = DEFAULT_DIRECTION) -> Grid:
    source = _validate_grid(grid)
    direction = _validate_direction(direction)
    count = min(9, empty_row_count(source))
    output = [[0] * 3 for _ in range(3)]
    for r, c in _SPIRALS[direction][:count]:
        output[r][c] = 8
    return output


def _make_container(
    empty_rows: int,
    interior_width: int,
    top_padding: int,
    left_padding: int,
) -> Grid:
    occupied_rows = 2
    interior_h = empty_rows + occupied_rows
    height = top_padding + interior_h + 2
    width = left_padding + interior_width + 3
    top = top_padding
    floor = top + interior_h
    left = left_padding
    right = left + interior_width + 1
    grid = [[0] * width for _ in range(height)]
    for r in range(top, floor + 1):
        grid[r][left] = 5
        grid[r][right] = 5
    for c in range(left, right + 1):
        grid[floor][c] = 5
    for c in range(interior_width):
        grid[top + empty_rows][left + 1 + c] = 8
    for c in range(interior_width):
        if c % 2 == 0 or interior_width == 1:
            grid[top + empty_rows + 1][left + 1 + c] = 8
    return grid


def fixtures() -> list[dict[str, Any]]:
    specs = (
        ("count-two", 2, 2, 0, 1),
        ("count-three", 3, 3, 1, 0),
        ("count-four", 4, 4, 0, 2),
        ("count-six", 6, 2, 1, 1),
        ("count-five-query", 5, 5, 0, 0),
    )
    return [
        {
            "name": name,
            "empty_rows": empty_rows,
            "input": _make_container(
                empty_rows, interior_width, top_padding, left_padding
            ),
        }
        for name, empty_rows, interior_width, top_padding, left_padding in specs
    ]


def choose_direction(seed: int) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    return random.Random(seed).choice(ALLOWED_DIRECTIONS)


def build_episode(seed: int, outputs: list[Grid] | None = None) -> dict[str, Any]:
    direction = choose_direction(seed)
    cases = fixtures()
    if outputs is None:
        outputs = [python_mirror(case["input"], direction) for case in cases]
    if len(outputs) != len(cases):
        raise ValueError("outputs must correspond one-to-one with fixtures")
    demonstrations = [
        {
            "name": case["name"],
            "empty_rows": case["empty_rows"],
            "input": case["input"],
            "output": output,
        }
        for case, output in zip(cases[:-1], outputs[:-1], strict=True)
    ]
    query_case = cases[-1]
    query = {
        "name": query_case["name"],
        "empty_rows": query_case["empty_rows"],
        "input": query_case["input"],
        "output": outputs[-1],
    }
    other = next(value for value in ALLOWED_DIRECTIONS if value != direction)
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"spiral_direction": direction},
        "racket": {
            "source": materialize_rule(direction),
            "normalized_hash": normalized_hash(materialize_rule(direction)),
        },
        "demonstrations": demonstrations,
        "query": query,
        "rival_predictions": {
            other: {
                "demonstrations": [
                    python_mirror(item["input"], other) for item in demonstrations
                ],
                "query": python_mirror(query["input"], other),
            }
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    if episode.get("task_id") != TASK_ID:
        raise ValueError("episode belongs to a different task")
    demonstrations = episode.get("demonstrations")
    query = episode.get("query")
    if not isinstance(demonstrations, list) or not isinstance(query, dict):
        raise ValueError("malformed private episode")
    return {
        "schema": PUBLIC_SCHEMA,
        "task_id": TASK_ID,
        "train": [
            {"input": item["input"], "output": item["output"]}
            for item in demonstrations
        ],
        "test": [{"input": query["input"]}],
    }


def _rule_body(source: str) -> str:
    normalized = normalize_rule(source)
    prefix = "(rule! "
    if not normalized.startswith(prefix) or not normalized.endswith(")"):
        raise ValueError("expected a complete (rule! BODY) form")
    body = normalized[len(prefix):-1]
    if not body.strip():
        raise ValueError("empty rule body")
    return body


def _grid_literal(grid: Any) -> str:
    clean = _validate_grid(grid)
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in clean)
    return "'(" + rows + ")"


def execute_racket(bridge: Any, source: str, grid: Any) -> Grid:
    expression = f"({_rule_body(source)} {_grid_literal(grid)})"
    return _validate_grid(bridge.eval_text(expression))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_prototype(out_dir: Path) -> dict[str, Any]:
    """Execute both settings with the packet Racket bridge and retain evidence."""
    from arc_repl.racket_bridge import RacketBridge

    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(__file__).resolve()
    task_dir = source_path.parents[2]
    generator_path = task_dir / "generator.py"
    if not generator_path.is_file():
        raise FileNotFoundError(generator_path)
    if normalized_hash(materialize_rule(DEFAULT_DIRECTION)) != "7a7c1a560527":
        raise AssertionError("default prototype no longer matches selected rule hash")

    for direction in ALLOWED_DIRECTIONS:
        rule_path = out_dir / "rules" / f"{direction}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(materialize_rule(direction) + "\n", encoding="utf-8")

    setting_seeds = {"clockwise": 1, "counterclockwise": 0}
    bridge = RacketBridge(timeout=30.0, startup_timeout=45.0)
    parity: list[dict[str, Any]] = []
    episodes: dict[str, dict[str, Any]] = {}
    episode_rows: list[dict[str, Any]] = []
    try:
        for direction in ALLOWED_DIRECTIONS:
            seed = setting_seeds[direction]
            if choose_direction(seed) != direction:
                raise AssertionError(f"seed {seed} no longer selects {direction}")
            source = materialize_rule(direction)
            outputs: list[Grid] = []
            for case in fixtures():
                actual = execute_racket(bridge, source, case["input"])
                expected = python_mirror(case["input"], direction)
                parity.append({
                    "direction": direction,
                    "fixture": case["name"],
                    "empty_rows": case["empty_rows"],
                    "input": case["input"],
                    "racket_output": actual,
                    "python_output": expected,
                    "passed": actual == expected,
                })
                if actual != expected:
                    raise AssertionError(
                        f"Racket/Python mismatch for {direction}/{case['name']}"
                    )
                outputs.append(actual)
            episode = build_episode(seed, outputs)
            episodes[direction] = episode
            private_path = out_dir / "episodes" / direction / "private.json"
            public_path = out_dir / "episodes" / direction / "public.json"
            _write_json(private_path, episode)
            _write_json(public_path, public_challenge(episode))
            other = next(value for value in ALLOWED_DIRECTIONS if value != direction)
            episode_rows.append({
                "direction": direction,
                "seed": seed,
                "private_path": str(private_path),
                "private_sha256": _sha256(private_path),
                "public_path": str(public_path),
                "public_sha256": _sha256(public_path),
                "all_demonstrations_distinguish_rival": all(
                    item["output"] != python_mirror(item["input"], other)
                    for item in episode["demonstrations"]
                ),
                "query_distinguishes_rival": (
                    episode["query"]["output"]
                    != python_mirror(episode["query"]["input"], other)
                ),
            })
    finally:
        bridge.close()

    public_safe = all(
        set(public_challenge(episode)) == {"schema", "task_id", "train", "test"}
        and "output" not in public_challenge(episode)["test"][0]
        and all(
            key not in public_challenge(episode)
            for key in ("parameter", "racket", "seed")
        )
        for episode in episodes.values()
    )
    checks = {
        "default_hash_matches_selected_rule": (
            normalized_hash(materialize_rule(DEFAULT_DIRECTION)) == "7a7c1a560527"
        ),
        "racket_python_parity": all(item["passed"] for item in parity),
        "all_demonstrations_distinguish_settings": all(
            row["all_demonstrations_distinguish_rival"] for row in episode_rows
        ),
        "all_queries_distinguish_settings": all(
            row["query_distinguishes_rival"] for row in episode_rows
        ),
        "public_records_hide_parameter_source_seed_and_query_answer": public_safe,
    }
    summary = {
        "schema": f"{TASK_ID}-spiral-direction-evidence-v1",
        "status": "proposed_prototype_not_selected",
        "task_id": TASK_ID,
        "passed": all(checks.values()),
        "parameter": {
            "name": "spiral_direction",
            "allowed_values": list(ALLOWED_DIRECTIONS),
            "original_default": DEFAULT_DIRECTION,
            "selection_scope": "one deterministic value per complete episode",
            "input_constraints": (
                "upright gray U-shaped container; retained counts 2..7 so "
                "clockwise and counterclockwise prefixes differ"
            ),
        },
        "selected_generator": {
            "path": str(generator_path),
            "sha256": _sha256(generator_path),
            "declared_rule_hash": "7a7c1a560527",
        },
        "prototype": {"path": str(source_path), "sha256": _sha256(source_path)},
        "rules": {
            direction: {
                "source": materialize_rule(direction),
                "normalized_hash": normalized_hash(materialize_rule(direction)),
                "racket_file": str(out_dir / "rules" / f"{direction}.rkt"),
            }
            for direction in ALLOWED_DIRECTIONS
        },
        "episodes": episode_rows,
        "checks": checks,
        "parity": parity,
        "limitations": [
            "This is task-local proposed evidence; the selected catalog rule remains clockwise.",
            "Evidence covers two retained episodes and five fixed inputs, not all seeds or all legal masks.",
            "Counts 0, 1, 8, 9, and above do not distinguish these traversals and are excluded from retained teaching episodes.",
        ],
        "replay": {
            "working_directory": "WORK/repo",
            "command": [
                "python3",
                f"generators/{TASK_ID}/workspace/parametric/spiral_direction.py",
                "--out-dir",
                f"../checks/parametric/{TASK_ID}-spiral-direction",
            ],
        },
    }
    _write_json(out_dir / "summary.json", summary)
    return summary


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = run_prototype(args.out_dir)
    print(json.dumps({
        "passed": summary["passed"],
        "summary": str(args.out_dir / "summary.json"),
    }, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

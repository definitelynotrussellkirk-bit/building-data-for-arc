#!/usr/bin/env python3
"""Executable prototype for an episode-level vertical-direction parameter.

This module is deliberately outside the selected generator's canonical path.
The default ``down`` materialization is byte-for-byte the selected rule.  The
``up`` materialization changes only the target direction and is chosen once per
prototype episode.  Public challenge records omit both the hidden parameter and
the query answer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "382eb0e592eb"
SCHEMA = f"{TASK_ID}-direction-prototype-v1"
PUBLIC_SCHEMA = f"{TASK_ID}-direction-public-challenge-v1"
ALLOWED_DIRECTIONS = ("down", "up")
DEFAULT_DIRECTION = "down"

# The default source is exact, not a paraphrase or regenerated equivalent.
_DOWN_RULE = "(rule! (let ((dummy 0)) (for*/fold ((out g)) ((r (in-range (- (rows g) 1))) (c (in-range (- (cols g) 1)))) (let ((v (at g r c))) (if (and (not (= v 0)) (= (at g r (+ c 1)) v)) (set-cell (set-cell out (+ r 1) c v) (+ r 1) (+ c 1) v) out)))))"
_UP_RULE = "(rule! (let ((dummy 0)) (for*/fold ((out g)) ((r (in-range 1 (rows g))) (c (in-range (- (cols g) 1)))) (let ((v (at g r c))) (if (and (not (= v 0)) (= (at g r (+ c 1)) v)) (set-cell (set-cell out (- r 1) c v) (- r 1) (+ c 1) v) out)))))"
_RULES = {"down": _DOWN_RULE, "up": _UP_RULE}

Grid = list[list[int]]


def _validate_direction(direction: str) -> str:
    if direction not in ALLOWED_DIRECTIONS:
        raise ValueError(
            f"direction must be one of {ALLOWED_DIRECTIONS}, got {direction!r}"
        )
    return direction


def _validate_grid(grid: Any) -> Grid:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    width: int | None = None
    clean: Grid = []
    for row in grid:
        if not isinstance(row, list) or not row:
            raise ValueError("each grid row must be a nonempty list")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("grid rows must have equal width")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid values must be integer ARC colors 0..9")
        clean.append(list(row))
    return clean


def normalize_rule(source: str) -> str:
    """Return the packet's stable single-line representation for rule hashing."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("rule source must be a nonempty string")
    return " ".join(source.split())


def normalized_hash(source: str) -> str:
    """Return the 12-hex rule identity used by selected generators."""
    return hashlib.sha256(normalize_rule(source).encode("utf-8")).hexdigest()[:12]


def materialize_rule(direction: str = DEFAULT_DIRECTION) -> str:
    """Materialize one complete Racket ``rule!`` source."""
    return _RULES[_validate_direction(direction)]


def choose_direction(seed: int) -> str:
    """Choose exactly one hidden parameter value for an entire episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    return random.Random(seed).choice(ALLOWED_DIRECTIONS)


def python_mirror(grid: Any, direction: str = DEFAULT_DIRECTION) -> Grid:
    """Independent executable mirror of either materialized rule.

    Trigger detection always reads the original input; writes can overlap in the
    copied output, matching the selected Racket rule's use of ``g`` for reads.
    """
    source = _validate_grid(grid)
    direction = _validate_direction(direction)
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    row_range: Iterable[int]
    delta: int
    if direction == "down":
        row_range, delta = range(height - 1), 1
    else:
        row_range, delta = range(1, height), -1
    for row in row_range:
        for col in range(width - 1):
            value = source[row][col]
            if value != 0 and source[row][col + 1] == value:
                output[row + delta][col] = value
                output[row + delta][col + 1] = value
    return output


def fixtures() -> list[dict[str, Any]]:
    """Return hand-authored grids where both settings act and disagree."""
    return [
        {
            "name": "single-middle-domino",
            "input": [
                [0, 0, 0, 0, 0],
                [0, 2, 2, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
            ],
        },
        {
            "name": "overlapping-length-three-run",
            "input": [
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 4, 4, 4, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
            ],
        },
        {
            "name": "two-colors-and-nonzero-targets",
            "input": [
                [0, 0, 0, 0, 0, 0],
                [0, 3, 3, 0, 0, 0],
                [0, 7, 0, 5, 5, 0],
                [0, 8, 8, 0, 6, 0],
                [0, 0, 0, 0, 0, 0],
            ],
        },
        {
            "name": "edge-touching-pairs",
            "input": [
                [0, 0, 0, 0, 0, 0],
                [9, 9, 0, 0, 0, 0],
                [0, 0, 0, 0, 6, 6],
                [0, 0, 0, 0, 0, 0],
            ],
        },
        {
            "name": "mixed-run-widths",
            "input": [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 3, 3, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ],
        },
    ]


def _rule_body(source: str) -> str:
    normalized = normalize_rule(source)
    prefix = "(rule! "
    if not normalized.startswith(prefix) or not normalized.endswith(")"):
        raise ValueError("expected a complete (rule! BODY) form")
    body = normalized[len(prefix) : -1]
    if not body.strip():
        raise ValueError("empty rule body")
    return body


def _grid_literal(grid: Any) -> str:
    clean = _validate_grid(grid)
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in clean)
    return "'(" + rows + ")"


def execute_racket(bridge: Any, source: str, grid: Any) -> Grid:
    """Apply one complete rule through the packet's actual Racket bridge."""
    expression = f"((lambda (g) {_rule_body(source)}) {_grid_literal(grid)})"
    return _validate_grid(bridge.eval_text(expression))


def build_episode(direction: str, outputs: list[Grid] | None = None) -> dict[str, Any]:
    """Build one complete private episode for a fixed direction setting."""
    direction = _validate_direction(direction)
    cases = fixtures()
    if outputs is None:
        outputs = [python_mirror(case["input"], direction) for case in cases]
    if len(outputs) != len(cases):
        raise ValueError("outputs must correspond one-to-one with fixtures")
    demonstrations = [
        {"name": case["name"], "input": case["input"], "output": output}
        for case, output in zip(cases[:-1], outputs[:-1])
    ]
    query = {
        "name": cases[-1]["name"],
        "input": cases[-1]["input"],
        "output": outputs[-1],
    }
    other = "up" if direction == "down" else "down"
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "parameter": {"direction": direction},
        "racket": {
            "source": materialize_rule(direction),
            "normalized_hash": normalized_hash(materialize_rule(direction)),
        },
        "demonstrations": demonstrations,
        "query": query,
        "rival_predictions": {
            other: python_mirror(query["input"], other),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the learner-facing view without parameter/source/query label."""
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


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _source_identity(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_prototype(out_dir: Path) -> dict[str, Any]:
    """Execute both parameter settings with Racket and retain replay evidence."""
    from arc_repl.racket_bridge import RacketBridge

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(__file__).resolve()
    task_dir = source_path.parents[2]
    generator_path = task_dir / "generator.py"
    if not generator_path.is_file():
        raise FileNotFoundError(generator_path)

    down_source = materialize_rule(DEFAULT_DIRECTION)
    if normalized_hash(down_source) != "03fbcf596117":
        raise AssertionError("default prototype no longer matches the selected rule hash")

    for direction in ALLOWED_DIRECTIONS:
        rule_path = out_dir / "racket" / f"{direction}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(materialize_rule(direction) + "\n", encoding="utf-8")

    bridge = RacketBridge(timeout=30.0, startup_timeout=45.0)
    episodes: dict[str, dict[str, Any]] = {}
    parity: list[dict[str, Any]] = []
    try:
        for direction in ALLOWED_DIRECTIONS:
            source = materialize_rule(direction)
            outputs: list[Grid] = []
            for case in fixtures():
                actual = execute_racket(bridge, source, case["input"])
                expected = python_mirror(case["input"], direction)
                same = actual == expected
                parity.append(
                    {
                        "direction": direction,
                        "fixture": case["name"],
                        "passed": same,
                        "input": case["input"],
                        "racket_output": actual,
                        "python_output": expected,
                    }
                )
                if not same:
                    raise AssertionError(
                        f"Racket/Python mismatch for {direction}/{case['name']}"
                    )
                outputs.append(actual)
            episode = build_episode(direction, outputs)
            episodes[direction] = episode
            _write_json(out_dir / "episodes" / direction / "private.json", episode)
            _write_json(
                out_dir / "episodes" / direction / "public.json",
                public_challenge(episode),
            )
    finally:
        bridge.close()

    generator_text = generator_path.read_text(encoding="utf-8")
    selected_hash_present = 'RULE_HASH = "03fbcf596117"' in generator_text
    distinguishing = all(
        python_mirror(case["input"], "down") != python_mirror(case["input"], "up")
        for case in fixtures()
    )
    public_safe = all(
        "parameter" not in public_challenge(episode)
        and "racket" not in public_challenge(episode)
        and "output" not in public_challenge(episode)["test"][0]
        for episode in episodes.values()
    )
    passed = (
        all(item["passed"] for item in parity)
        and selected_hash_present
        and distinguishing
        and public_safe
        and normalized_hash(down_source) == "03fbcf596117"
    )
    summary = {
        "schema": f"{TASK_ID}-direction-prototype-evidence-v1",
        "task_id": TASK_ID,
        "passed": passed,
        "parameter": {
            "name": "direction",
            "scope": "one fixed value per episode",
            "allowed": list(ALLOWED_DIRECTIONS),
            "default": DEFAULT_DIRECTION,
        },
        "selected_generator": {
            "path": str(generator_path),
            "sha256": _source_identity(generator_path),
            "declares_default_rule_hash": selected_hash_present,
        },
        "prototype": {
            "path": str(source_path),
            "sha256": _source_identity(source_path),
        },
        "rules": {
            direction: {
                "source": materialize_rule(direction),
                "normalized_hash": normalized_hash(materialize_rule(direction)),
                "racket_file": str(out_dir / "racket" / f"{direction}.rkt"),
            }
            for direction in ALLOWED_DIRECTIONS
        },
        "checks": {
            "racket_python_parity": all(item["passed"] for item in parity),
            "parity_case_count": len(parity),
            "all_fixtures_distinguish_settings": distinguishing,
            "public_records_hide_parameter_source_and_query_answer": public_safe,
            "default_hash_matches_selected_rule": normalized_hash(down_source)
            == "03fbcf596117",
        },
        "parity": parity,
        "replay": {
            "working_directory": "WORK/repo",
            "command": [
                "python3",
                f"generators/{TASK_ID}/workspace/parametric/direction.py",
                "--out-dir",
                "../checks/parametric/direction-run",
            ],
        },
    }
    _write_json(out_dir / "summary.json", summary)
    return summary


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="directory for private/public episodes and Racket parity evidence",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = run_prototype(args.out_dir)
    print(json.dumps({"passed": summary["passed"], "summary": str(args.out_dir / "summary.json")}, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

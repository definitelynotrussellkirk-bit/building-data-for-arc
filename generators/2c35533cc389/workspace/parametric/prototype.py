#!/usr/bin/env python3
"""Isolated episode-level direction prototype for task 2c35533cc389.

This proposal does not change the selected production generator or canonical
Racket authority.  It varies one hidden rule parameter exactly once per complete
episode: whether every red(2) source paints blue(1) one cell to its right or to
its left.  ``right`` is the original/default setting.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge

TASK_ID = "2c35533cc389"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_DIRECTIONS = ("right", "left")
DEFAULT_DIRECTION = "right"


def _validate_direction(direction: str) -> str:
    if direction not in ALLOWED_DIRECTIONS:
        raise ValueError(
            f"direction must be one of {ALLOWED_DIRECTIONS}, got {direction!r}"
        )
    return direction


def choose_direction(seed: int) -> str:
    """Choose one hidden rule setting once for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    digest = hashlib.sha256(f"{TASK_ID}|direction|{seed}".encode()).digest()
    return ALLOWED_DIRECTIONS[digest[0] % len(ALLOWED_DIRECTIONS)]


def _patterns() -> tuple[tuple[tuple[int, int], ...], ...]:
    """Small sparse scenes that distinguish left from right without ambiguity."""
    return (
        ((1, 2), (3, 5), (4, 0), (5, 6)),
        ((0, 1), (2, 4), (4, 7), (5, 3)),
        ((1, 3), (1, 4), (3, 1), (4, 6)),
        ((0, 0), (2, 2), (3, 6), (5, 7)),
    )


def make_input(seed: int, index: int) -> list[list[int]]:
    """Return a deterministic lawful sparse input for a prototype episode."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative literal Python integer")

    height, width = 6, 8
    grid = [[0 for _ in range(width)] for _ in range(height)]
    pattern = _patterns()[(seed + index) % len(_patterns())]

    # A deterministic vertical reflection adds seed variation while preserving
    # horizontal direction witnesses and the canonical sparse grammar.
    reflect_rows = hashlib.sha256(f"{TASK_ID}|layout|{seed}|{index}".encode()).digest()[0] & 1
    for row, col in pattern:
        out_row = height - 1 - row if reflect_rows else row
        grid[out_row][col] = 2
    return grid


def apply_python(grid: list[list[int]], direction: str) -> list[list[int]]:
    """Reference mirror for assertions; exact Racket execution labels evidence."""
    setting = _validate_direction(direction)
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a nonempty rectangle")
    out = copy.deepcopy(grid)
    delta = 1 if setting == "right" else -1
    sources = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    width = len(grid[0])
    for row, col in sources:
        destination = col + delta
        if 0 <= destination < width:
            out[row][destination] = 1
    return out


def program_for(direction: str) -> str:
    """Return the exact proposed Racket authority for one parameter value."""
    setting = _validate_direction(direction)
    if setting == "right":
        return """(rule!
 ;; Every red(2) gets a blue(1) painted immediately to its RIGHT (in bounds).
 (paint-cells g
              (filter (lambda (p) (< (second p) w))
                      (map (lambda (p) (list (first p) (+ (second p) 1)))
                           (find-color g 2)))
              1))"""
    return """(rule!
 ;; Every red(2) gets a blue(1) painted immediately to its LEFT (in bounds).
 (paint-cells g
              (filter (lambda (p) (>= (second p) 0))
                      (map (lambda (p) (list (first p) (- (second p) 1)))
                           (find-color g 2)))
              1))"""


def _rule_body(program: str) -> str:
    text = program.strip()
    prefix = "(rule!"
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len(prefix) : -1].strip()


def apply_racket(
    bridge: RacketBridge, program: str, grid: list[list[int]]
) -> list[list[int]]:
    """Execute the exact rule body through the protected Racket bridge."""
    bridge.define_grid("g", grid)
    bridge.define_value("h", len(grid))
    bridge.define_value("w", len(grid[0]))
    return bridge.eval_text(_rule_body(program))


def build_episode(seed: int, direction: str | None = None) -> dict[str, Any]:
    """Build a complete episode using one immutable hidden setting."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    setting = choose_direction(seed) if direction is None else _validate_direction(direction)
    train = []
    for index in range(3):
        grid = make_input(seed, index)
        train.append({"input": grid, "output": apply_python(grid, setting)})
    query = make_input(seed, 3)
    return {
        "schema": "2c35533cc389-parametric-episode-v1",
        "train": train,
        "test": {"input": query, "output": apply_python(query, setting)},
        "program": program_for(setting),
        "meta": {
            "seed": seed,
            "direction": setting,
            "default_direction": DEFAULT_DIRECTION,
            "prototype_version": PROTOTYPE_VERSION,
        },
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Report ambiguity against the sole other declared parameter setting."""
    setting = _validate_direction(episode["meta"]["direction"])
    rival = next(value for value in ALLOWED_DIRECTIONS if value != setting)
    findings: list[str] = []
    distinguishing = [
        index
        for index, pair in enumerate(episode["train"])
        if apply_python(pair["input"], rival) != pair["output"]
    ]
    if not distinguishing:
        findings.append(f"rival direction {rival!r} fits every demonstration")
    if apply_python(episode["test"]["input"], rival) == episode["test"]["output"]:
        findings.append(f"query does not distinguish rival direction {rival!r}")
    return findings


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


def _find_seed_for(setting: str, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_direction(seed) != setting:
        seed += 1
    return seed


def materialize(out_dir: Path, seed_start: int = 7300) -> dict[str, Any]:
    """Execute both settings in Racket and retain private/public evidence."""
    if type(seed_start) is not int:
        raise TypeError("seed_start must be a literal Python integer")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    public_dir = out_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(__file__).resolve()
    used: set[int] = set()
    episodes: list[dict[str, Any]] = []
    with RacketBridge(max_calls_before_restart=64) as bridge:
        for offset, setting in enumerate(ALLOWED_DIRECTIONS):
            seed = _find_seed_for(setting, seed_start + offset, used)
            used.add(seed)
            episode = build_episode(seed)
            if episode["meta"]["direction"] != setting:
                raise AssertionError("seed search returned wrong direction")

            for pair in episode["train"]:
                racket_output = apply_racket(bridge, episode["program"], pair["input"])
                if racket_output != pair["output"]:
                    raise AssertionError(
                        f"Racket/Python mismatch for {setting} demonstration"
                    )
                pair["output"] = racket_output
            racket_query = apply_racket(
                bridge, episode["program"], episode["test"]["input"]
            )
            if racket_query != episode["test"]["output"]:
                raise AssertionError(f"Racket/Python mismatch for {setting} query")
            episode["test"]["output"] = racket_query

            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError(findings)
            rival = next(value for value in ALLOWED_DIRECTIONS if value != setting)
            distinguishing = [
                index
                for index, pair in enumerate(episode["train"])
                if apply_python(pair["input"], rival) != pair["output"]
            ]

            public = {
                "schema": "2c35533cc389-parametric-public-v1",
                "train": copy.deepcopy(episode["train"]),
                "test": {"input": copy.deepcopy(episode["test"]["input"])},
            }
            public_path = public_dir / f"challenge_seed_{seed}.json"
            public_path.write_text(json.dumps(public, indent=2) + "\n")

            episodes.append(
                {
                    **episode,
                    "direction": setting,
                    "program_sha256": _sha256_text(episode["program"]),
                    "parameter_rival_findings": findings,
                    "distinguishing_demo_indices": distinguishing,
                    "public_path": str(public_path.relative_to(out_dir)),
                    "public_sha256": _sha256_json(public),
                }
            )

    report = {
        "schema": "2c35533cc389-parametric-evidence-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "parameter": {
            "name": "direction",
            "allowed_values": list(ALLOWED_DIRECTIONS),
            "canonical_default": DEFAULT_DIRECTION,
            "chosen_once_per_episode": True,
            "input_constraint": (
                "Each episode uses sparse asymmetric inputs with interior red sources; "
                "the three demonstrations and query all distinguish left from right."
            ),
        },
        "prototype_source": str(source_path),
        "prototype_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "episodes": episodes,
        "run_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            "generators/2c35533cc389/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric",
        ],
        "limitations": [
            "This is an isolated proposal, not a production generator/API change.",
            "Evidence covers two deterministic complete episodes and the single declared parameter rival.",
            "The prototype does not claim that left-paint is part of the original task family.",
        ],
    }
    (out_dir / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=7300)
    args = parser.parse_args()
    report = materialize(args.out, seed_start=args.seed_start)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": [
                    {
                        "seed": row["meta"]["seed"],
                        "direction": row["meta"]["direction"],
                        "distinguishing_demo_indices": row[
                            "distinguishing_demo_indices"
                        ],
                        "program_sha256": row["program_sha256"],
                    }
                    for row in report["episodes"]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

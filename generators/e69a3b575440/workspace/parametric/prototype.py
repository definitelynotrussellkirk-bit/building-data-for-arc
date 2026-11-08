#!/usr/bin/env python3
"""Isolated rule-parameter prototype for e69a3b575440.

This does not alter the selected generator or canonical authority.  It varies one
hidden episode-level parameter: whether command 2 means a clockwise or
counterclockwise quarter turn.  The canonical/default setting is clockwise.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge

ALLOWED_QUARTER_TURNS = ("clockwise", "counterclockwise")
DEFAULT_QUARTER_TURN = "clockwise"
TASK_ID = "e69a3b575440"
PROTOTYPE_VERSION = "1.0.0"


def _validate_setting(quarter_turn: str) -> str:
    if quarter_turn not in ALLOWED_QUARTER_TURNS:
        raise ValueError(
            f"quarter_turn must be one of {ALLOWED_QUARTER_TURNS}, got {quarter_turn!r}"
        )
    return quarter_turn


def choose_quarter_turn(seed: int) -> str:
    """Choose one hidden rule setting once for the entire episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    digest = hashlib.sha256(f"{TASK_ID}|quarter_turn|{seed}".encode()).digest()
    return ALLOWED_QUARTER_TURNS[digest[0] % len(ALLOWED_QUARTER_TURNS)]


def _patterns() -> tuple[tuple[tuple[int, ...], ...], ...]:
    return (
        ((1, 1, 0, 0), (0, 1, 2, 0), (0, 1, 2, 2)),
        ((1, 0, 0, 0), (1, 1, 2, 2), (0, 1, 2, 0)),
        ((1, 1, 1, 0), (0, 2, 1, 0), (0, 2, 2, 2)),
        ((1, 1, 0, 0), (1, 2, 2, 0), (0, 0, 2, 2)),
    )


def make_input(command: int, variant: int = 0) -> list[list[int]]:
    """Return a lawful asymmetric scene; command 2 separates both settings."""
    if type(command) is not int or not 1 <= command <= 8:
        raise ValueError("command must be an integer in 1..8")
    if type(variant) is not int:
        raise TypeError("variant must be an integer")
    grid = [[0 for _ in range(9)] for _ in range(8)]
    grid[0][0] = command
    pattern = _patterns()[variant % len(_patterns())]
    colors = (4 + variant % 3, 7 + variant % 2)
    row0 = 2 + (variant % 2)
    col0 = 2 + ((variant // 2) % 2)
    for row, values in enumerate(pattern):
        for col, value in enumerate(values):
            if value:
                grid[row0 + row][col0 + col] = colors[value - 1]
    return grid


def _crop(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return [[]]
    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    c1 = max(col for _, col in cells)
    return [values[c0 : c1 + 1] for values in grid[r0 : r1 + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    for _ in range(3):
        out = _rotate_cw(out)
    return out


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return grid[::-1]


def _anti_transpose(grid: list[list[int]]) -> list[list[int]]:
    return _rotate_180(_transpose(grid))


def apply_python(grid: list[list[int]], quarter_turn: str) -> list[list[int]]:
    """Python mirror used only for prototype assertions; Racket labels evidence."""
    setting = _validate_setting(quarter_turn)
    command = grid[0][0]
    clean = copy.deepcopy(grid)
    clean[0][0] = 0
    obj = _crop(clean)
    transforms = {
        1: lambda value: value,
        2: _rotate_cw if setting == "clockwise" else _rotate_ccw,
        3: _rotate_180,
        4: _transpose,
        5: _flip_lr,
        6: _flip_ud,
        7: _transpose,
        8: _anti_transpose,
    }
    if command not in transforms:
        raise ValueError(f"command outside 1..8: {command!r}")
    return transforms[command](obj)


def program_for(quarter_turn: str) -> str:
    setting = _validate_setting(quarter_turn)
    quarter = "(rotate-cw grid)" if setting == "clockwise" else "(rotate-cw (rotate-180 grid))"
    return f"""(rule!
  (let ((dummy 0))
    (define (anti-transpose grid) (rotate-180 (transpose grid)))
    (define (transform-code grid code)
      (cond [(= code 1) grid]
            [(= code 2) {quarter}]
            [(= code 3) (rotate-180 grid)]
            [(= code 4) (transpose grid)]
            [(= code 5) (flip-lr grid)]
            [(= code 6) (flip-ud grid)]
            [(= code 7) (transpose grid)]
            [else (anti-transpose grid)]))
    (let* ((cmd (at g 0 0))
           (clean (set-cell g 0 0 0)))
      (transform-code (crop-to-content clean) cmd))))"""


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def _rule_body(program: str) -> str:
    text = program.strip()
    prefix = "(rule!"
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len(prefix) : -1].strip()


def apply_racket(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    # This prototype body references only g, so evaluating it after define_grid is
    # equivalent to the rule wrapper without depending on the staged scripts package.
    bridge.define_grid("g", grid)
    return bridge.eval_text(_rule_body(program))


def build_episode(seed: int, quarter_turn: str | None = None) -> dict[str, Any]:
    """Build one complete hidden-setting episode with Python provisional labels."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    setting = choose_quarter_turn(seed) if quarter_turn is None else _validate_setting(quarter_turn)
    train = []
    for command in range(1, 9):
        grid = make_input(command, variant=seed + command)
        train.append({"input": grid, "output": apply_python(grid, setting)})
    query_grid = make_input(2, variant=seed + 101)
    return {
        "train": train,
        "test": {"input": query_grid, "output": apply_python(query_grid, setting)},
        "program": program_for(setting),
        "meta": {
            "seed": seed,
            "quarter_turn": setting,
            "default_setting": DEFAULT_QUARTER_TURN,
            "prototype_version": PROTOTYPE_VERSION,
        },
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Return ambiguity findings against the other allowed parameter value."""
    setting = episode["meta"]["quarter_turn"]
    rival = next(value for value in ALLOWED_QUARTER_TURNS if value != setting)
    findings: list[str] = []
    witnesses = [
        pair
        for pair in episode["train"]
        if apply_python(pair["input"], rival) != pair["output"]
    ]
    if not witnesses:
        findings.append(f"rival setting {rival!r} fits every demonstration")
    if apply_python(episode["test"]["input"], rival) == episode["test"]["output"]:
        findings.append(f"query does not distinguish rival setting {rival!r}")
    return findings


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


def _find_seed_for(setting: str, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_quarter_turn(seed) != setting:
        seed += 1
    return seed


def materialize(out_dir: Path, seed_start: int = 7300) -> dict[str, Any]:
    """Execute both settings with Racket and retain hidden/public evidence."""
    out_dir.mkdir(parents=True, exist_ok=True)
    public_dir = out_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(__file__).resolve()
    used: set[int] = set()
    episodes = []
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for setting_index, setting in enumerate(ALLOWED_QUARTER_TURNS):
            seed = _find_seed_for(setting, seed_start + setting_index, used)
            used.add(seed)
            episode = build_episode(seed)
            assert episode["meta"]["quarter_turn"] == setting
            for pair in episode["train"]:
                pair["output"] = apply_racket(bridge, episode["program"], pair["input"])
                assert pair["output"] == apply_python(pair["input"], setting)
            episode["test"]["output"] = apply_racket(
                bridge, episode["program"], episode["test"]["input"]
            )
            assert episode["test"]["output"] == apply_python(
                episode["test"]["input"], setting
            )
            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError(findings)

            public = {
                "schema": "e69a3b575440-parametric-public-v1",
                "train": copy.deepcopy(episode["train"]),
                "test": {"input": copy.deepcopy(episode["test"]["input"])},
            }
            public_path = public_dir / f"challenge_seed_{seed}.json"
            public_path.write_text(json.dumps(public, indent=2) + "\n")
            episodes.append(
                {
                    **episode,
                    "program_sha256": _sha256_text(episode["program"]),
                    "parameter_rival_findings": findings,
                    "distinguishing_demo_commands": [
                        pair["input"][0][0]
                        for pair in episode["train"]
                        if apply_python(
                            pair["input"],
                            next(v for v in ALLOWED_QUARTER_TURNS if v != setting),
                        )
                        != pair["output"]
                    ],
                    "public_challenge": str(public_path.relative_to(out_dir)),
                    "public_challenge_sha256": _sha256_json(public),
                }
            )
    finally:
        bridge.shutdown()

    report = {
        "schema": "e69a3b575440-parametric-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "quarter_turn",
            "allowed_values": list(ALLOWED_QUARTER_TURNS),
            "original_default": DEFAULT_QUARTER_TURN,
            "input_constraints": (
                "Every episode includes an asymmetric command-2 demonstration and "
                "an asymmetric command-2 query so clockwise and counterclockwise differ."
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
            "generators/e69a3b575440/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric",
        ],
        "limitations": [
            "Prototype only; it is not wired into the selected production generator or authority.",
            "Evidence covers two deterministic seeds and the single declared parameter rival, not all seeds or all possible alternative rules.",
            "Commands other than 2 retain the canonical mapping and therefore do not identify the parameter by themselves.",
        ],
    }
    (out_dir / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=7300)
    args = parser.parse_args()
    report = materialize(args.out, args.seed_start)
    print(json.dumps({
        "status": report["status"],
        "episodes": [
            {
                "seed": row["meta"]["seed"],
                "quarter_turn": row["meta"]["quarter_turn"],
                "program_sha256": row["program_sha256"],
                "distinguishing_demo_commands": row["distinguishing_demo_commands"],
            }
            for row in report["episodes"]
        ],
        "evidence": str(args.out / "evidence.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

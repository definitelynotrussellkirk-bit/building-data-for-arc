#!/usr/bin/env python3
"""Isolated episode-level cycle-direction prototype for task 19e04051ad0d.

The selected production generator and canonical authority remain unchanged by
this module.  One hidden setting is chosen once per complete episode:
``next`` fills each region's holes from the region to its right (the canonical
rule), while ``previous`` fills from the region to its left.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import find_root, load_selected_generator

TASK_ID = "19e04051ad0d"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_DIRECTIONS = ("next", "previous")
DEFAULT_DIRECTION = "next"
_CANONICAL_INDEX = "(remainder (+ i 1) n)"
_PREVIOUS_INDEX = "(remainder (+ i (- n 1)) n)"
CANONICAL_PROGRAM = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g)))\n           (let* ((bg (mode g -1))\n                  (sep-cols (for/list ((c (range 0 w)) #:when\n                                (for/and ((r (range 0 h))) (= (at g r c) bg)))\n                              c))\n                  (sep-set (make-hash))\n                  (dummy (for ((c sep-cols)) (hash-set! sep-set c #t)))\n                  (regions (list))\n                  (current (list))\n                  (dummy2 (for ((c (range 0 w)))\n                            (if (hash-has-key? sep-set c)\n                                (begin\n                                  (unless\n                                    (null? current)\n                                    (set! regions (append regions (list current))))\n                                  (set! current (list)))\n                                (set! current (append current (list c))))))\n                  (dummy3 (unless\n                            (null? current)\n                            (set! regions (append regions (list current)))))\n                  (region-colors (for/list ((reg regions))\n                                   (let ((colors (make-hash)))\n                                     (for ((c reg))\n                                       (for ((r (range 0 h)))\n                                         (let ((v (at g r c)))\n                                           (when (!= v bg) (hash-set! colors v #t)))))\n                                     (car (hash-keys colors)))))\n                  (n (length regions))\n                  (result (make-hash)))\n             (for* ((r (range 0 h)) (c (range 0 w)))\n                   (hash-set! result (list r c) (at g r c)))\n             (for ((i (range 0 n)))\n               (let ((reg (list-ref regions i))\n                     (repl (list-ref region-colors (remainder (+ i 1) n))))\n                 (for ((c reg))\n                   (for ((r (range 0 h)))\n                     (when (= (at g r c) bg) (hash-set! result (list r c) repl))))))\n             (cellmap g (r c v) (hash-ref result (list r c) 0))))))'

ROOT = find_root(__file__)
GENERATOR, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)


def _validate_direction(cycle_direction: str) -> str:
    if cycle_direction not in ALLOWED_DIRECTIONS:
        raise ValueError(
            "cycle_direction must be one of "
            f"{ALLOWED_DIRECTIONS}, got {cycle_direction!r}"
        )
    return cycle_direction


def choose_direction(seed: int) -> str:
    """Choose one hidden rule setting once for the complete episode."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    digest = hashlib.sha256(
        f"{TASK_ID}|cycle_direction|{seed}".encode()
    ).digest()
    return ALLOWED_DIRECTIONS[digest[0] % len(ALLOWED_DIRECTIONS)]


def make_input(seed: int, index: int) -> list[list[int]]:
    """Use a deterministic lawful selected-generator input."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative literal Python integer")
    return GENERATOR.generate(seed, index, difficulty="medium")


def _analyze(
    grid: Sequence[Sequence[int]],
) -> tuple[int, list[list[int]], list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangle")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be a nonempty rectangle")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be literal ARC colors 0..9")

    counts = Counter(value for row in grid for value in row)
    ranked = counts.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise ValueError("background is not uniquely modal")
    bg = ranked[0][0]
    separators = [
        col
        for col in range(width)
        if all(row[col] == bg for row in grid)
    ]
    separator_set = set(separators)
    regions: list[list[int]] = []
    current: list[int] = []
    for col in range(width):
        if col in separator_set:
            if current:
                regions.append(current)
                current = []
        else:
            current.append(col)
    if current:
        regions.append(current)
    if len(regions) != 3:
        raise ValueError(f"expected exactly three regions, got {len(regions)}")

    colors: list[int] = []
    for region in regions:
        foreground = {
            grid[row][col]
            for row in range(len(grid))
            for col in region
            if grid[row][col] != bg
        }
        if len(foreground) != 1:
            raise ValueError("each region must contain exactly one foreground color")
        colors.append(next(iter(foreground)))
    if len(set(colors)) != 3:
        raise ValueError("region colors must be distinct")
    return bg, regions, colors


def apply_python(
    grid: list[list[int]], cycle_direction: str
) -> list[list[int]]:
    """Independent mirror for assertions; retained evidence is Racket-labelled."""
    setting = _validate_direction(cycle_direction)
    bg, regions, colors = _analyze(grid)
    offset = 1 if setting == "next" else -1
    out = copy.deepcopy(grid)
    for index, region in enumerate(regions):
        replacement = colors[(index + offset) % len(regions)]
        for row in range(len(grid)):
            for col in region:
                if grid[row][col] == bg:
                    out[row][col] = replacement
    return out


def program_for(cycle_direction: str) -> str:
    """Return the exact proposed Racket authority for one parameter value."""
    setting = _validate_direction(cycle_direction)
    if CANONICAL_PROGRAM.count(_CANONICAL_INDEX) != 1:
        raise RuntimeError("canonical program no longer has one cycle-index site")
    if setting == "next":
        return CANONICAL_PROGRAM
    return CANONICAL_PROGRAM.replace(_CANONICAL_INDEX, _PREVIOUS_INDEX)


def apply_racket(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute one exact program through the protected Racket bridge."""
    bridge.define_grid("g", grid)
    callable_text = strip_rule_wrapper(program)
    return bridge.eval_text(f"({callable_text} g)")


def build_episode(
    seed: int,
    direction: str | None = None,
) -> dict[str, Any]:
    """Build three demonstrations and one query under one immutable setting."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    setting = (
        choose_direction(seed)
        if direction is None
        else _validate_direction(direction)
    )
    train = []
    for index in range(3):
        grid = make_input(seed, index)
        train.append({"input": grid, "output": apply_python(grid, setting)})
    query = make_input(seed, 3)
    return {
        "schema": "19e04051ad0d-parametric-episode-v1",
        "train": train,
        "test": {"input": query, "output": apply_python(query, setting)},
        "program": program_for(setting),
        "meta": {
            "seed": seed,
            "cycle_direction": setting,
            "default_cycle_direction": DEFAULT_DIRECTION,
            "prototype_version": PROTOTYPE_VERSION,
            "selected_generator_sha256": GENERATOR_SHA256,
        },
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Report ambiguity against the sole other declared parameter setting."""
    setting = _validate_direction(episode["meta"]["cycle_direction"])
    rival = next(value for value in ALLOWED_DIRECTIONS if value != setting)
    findings: list[str] = []
    distinguishing = [
        index
        for index, pair in enumerate(episode["train"])
        if apply_python(pair["input"], rival) != pair["output"]
    ]
    if not distinguishing:
        findings.append(
            f"rival cycle_direction {rival!r} fits every demonstration"
        )
    if apply_python(episode["test"]["input"], rival) == episode["test"]["output"]:
        findings.append(
            f"query does not distinguish rival cycle_direction {rival!r}"
        )
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
            if episode["meta"]["cycle_direction"] != setting:
                raise AssertionError("seed search returned wrong cycle direction")

            for pair in episode["train"]:
                racket_output = apply_racket(
                    bridge, episode["program"], pair["input"]
                )
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
                "schema": "19e04051ad0d-parametric-public-v1",
                "train": copy.deepcopy(episode["train"]),
                "test": {"input": copy.deepcopy(episode["test"]["input"])},
            }
            public_path = public_dir / f"challenge_seed_{seed}.json"
            public_path.write_text(json.dumps(public, indent=2) + "\n")

            episodes.append(
                {
                    **episode,
                    "cycle_direction": setting,
                    "program_sha256": _sha256_text(episode["program"]),
                    "parameter_rival_findings": findings,
                    "distinguishing_demo_indices": distinguishing,
                    "public_path": str(public_path.relative_to(out_dir)),
                    "public_sha256": _sha256_json(public),
                }
            )

    report = {
        "schema": "19e04051ad0d-parametric-evidence-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "parameter": {
            "name": "cycle_direction",
            "allowed_values": list(ALLOWED_DIRECTIONS),
            "canonical_default": DEFAULT_DIRECTION,
            "chosen_once_per_episode": True,
            "input_constraint": (
                "Every input has three distinct region colors and visible holes in "
                "all regions, so next and previous differ on every demonstration "
                "and query while preserving the canonical region-analysis problem."
            ),
        },
        "prototype_source": str(source_path),
        "prototype_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "selected_generator_source": str(GENERATOR_SOURCE),
        "selected_generator_sha256": GENERATOR_SHA256,
        "canonical_program_sha256": _sha256_text(CANONICAL_PROGRAM),
        "episodes": episodes,
        "run_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            "generators/19e04051ad0d/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric",
        ],
        "limitations": [
            "This is an isolated proposal, not a production generator or canonical-authority change.",
            "Evidence covers two deterministic complete episodes and the single declared parameter rival.",
            "The previous-direction setting is a proposed sibling rule, not evidence of original-family approval.",
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
                        "cycle_direction": row["cycle_direction"],
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

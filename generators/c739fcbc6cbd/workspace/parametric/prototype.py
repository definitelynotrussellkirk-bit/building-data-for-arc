#!/usr/bin/env python3
"""Bounded period-factor prototype for c739fcbc6cbd.

This module is deliberately separate from the selected production generator.
It preserves marker selection, axis choice, prefix handling, and phase colors,
while varying only the multiplier applied to the active-axis separation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sys

TASK_ID = "c739fcbc6cbd"
ALLOWED_PERIOD_FACTORS = (2, 3)
DEFAULT_PERIOD_FACTOR = 2
EPISODE_SIZE = 4  # three demonstrations plus one query


def _validate_period_factor(period_factor: int) -> int:
    if type(period_factor) is not int:
        raise TypeError("period_factor must be a literal integer")
    if period_factor not in ALLOWED_PERIOD_FACTORS:
        raise ValueError(
            f"period_factor must be one of {ALLOWED_PERIOD_FACTORS}, got {period_factor!r}"
        )
    return period_factor


def _validate_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be literal ARC colors 0..9")
    return len(grid), width


def _color_major_dots(grid):
    return [
        (row, col, color)
        for color in range(1, 10)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def python_mirror(grid, *, period_factor: int):
    """Independent Python audit mirror of the parameterized rule."""
    factor = _validate_period_factor(period_factor)
    height, width = _validate_grid(grid)
    dots = _color_major_dots(grid)
    if len(dots) < 2:
        raise ValueError("expected at least two nonzero dots")
    r1, c1, color1 = dots[0]
    r2, c2, color2 = dots[1]
    dr, dc = abs(r2 - r1), abs(c2 - c1)
    row_bands = dc == 0 or (dr > 0 and dr < dc)
    distance = dr if row_bands else dc
    if distance == 0:
        raise ValueError("selected dots must differ on the active axis")
    period = factor * distance
    output = [[0 for _ in range(width)] for _ in range(height)]
    if row_bands:
        for row in range(min(r1, r2), height):
            color = (
                color1
                if (row - r1) % period == 0
                else color2
                if (row - r2) % period == 0
                else 0
            )
            if color:
                output[row] = [color for _ in range(width)]
    else:
        for col in range(min(c1, c2), width):
            color = (
                color1
                if (col - c1) % period == 0
                else color2
                if (col - c2) % period == 0
                else 0
            )
            if color:
                for row in range(height):
                    output[row][col] = color
    return output


def rule_source(period_factor: int) -> str:
    factor = _validate_period_factor(period_factor)
    return f"""(rule!
  ;; Proposed variant: preserve the canonical selection/axis/prefix rule and
  ;; vary only the active-distance period multiplier for the whole episode.
  (let* ((dots (for*/list ((color (in-list (range 1 10)))
                           (p (in-list (find-color g color))))
                 (list (first p) (second p) color)))
         (a (first dots))
         (b (second dots))
         (r1 (first a)) (c1 (second a)) (color1 (third a))
         (r2 (first b)) (c2 (second b)) (color2 (third b))
         (dr (abs (- r2 r1)))
         (dc (abs (- c2 c1))))
    (define (phase x x1 x2 period)
      (cond ((zero? (mod (- x x1) period)) color1)
            ((zero? (mod (- x x2) period)) color2)
            (else 0)))
    (if (or (zero? dc) (and (> dr 0) (< dr dc)))
        (cellmap g (r c v)
          (if (< r (min r1 r2)) 0 (phase r r1 r2 (* {factor} dr))))
        (cellmap g (r c v)
          (if (< c (min c1 c2)) 0 (phase c c1 c2 (* {factor} dc)))))))"""


def _input_for(rng: random.Random, index: int):
    """Build a lawful scene where factors 2 and 3 necessarily disagree."""
    distance = (2, 3, 4, 2)[index % EPISODE_SIZE]
    prefix = (0, 1, 2, 1)[index % EPISODE_SIZE]
    color1, color2 = sorted(rng.sample(range(1, 10), 2))
    row_mode = index % 2 == 0

    if row_mode:
        height = prefix + 3 * distance + 3
        width = 11 + (index % 3)
        if index % 4 == 0:
            first = (prefix, rng.randrange(width))
            second = (prefix + distance, first[1])
        else:
            across = min(width - 1, distance + 3)
            first = (prefix, 0)
            second = (prefix + distance, across)
    else:
        width = prefix + 3 * distance + 3
        height = 11 + (index % 3)
        if index % 4 == 1:
            first = (rng.randrange(height), prefix)
            second = (first[0], prefix + distance)
        else:
            down = min(height - 1, distance + 3)
            first = (0, prefix)
            second = (down, prefix + distance)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[first[0]][first[1]] = color1
    grid[second[0]][second[1]] = color2
    output2 = python_mirror(grid, period_factor=2)
    output3 = python_mirror(grid, period_factor=3)
    if output2 == output3:
        raise AssertionError("prototype input failed to distinguish period factors")
    return grid


def build_episode(seed: int, *, period_factor: int | None = None):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if period_factor is None:
        period_factor = ALLOWED_PERIOD_FACTORS[seed % len(ALLOWED_PERIOD_FACTORS)]
    factor = _validate_period_factor(period_factor)
    rng = random.Random(seed)
    pairs = []
    for index in range(EPISODE_SIZE):
        grid = _input_for(rng, index)
        pairs.append(
            {
                "input": grid,
                "output": python_mirror(grid, period_factor=factor),
            }
        )
    return {
        "parameter": {"period_factor": factor},
        "seed": seed,
        "train": pairs[:-1],
        "test": pairs[-1:],
    }


def public_challenge(episode):
    """Visible challenge: demos labeled, hidden parameter and query answer omitted."""
    return {
        "train": episode["train"],
        "test": [{"input": episode["test"][0]["input"]}],
    }


def _grid_literal(grid) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def _install_scripts_namespace() -> None:
    import types

    repo_root = Path(__file__).resolve().parents[4]
    tools_dir = repo_root / "shared" / "tools"
    if "scripts" not in sys.modules and tools_dir.is_dir():
        package = types.ModuleType("scripts")
        package.__path__ = [str(tools_dir)]
        sys.modules["scripts"] = package


def _racket_apply(bridge, source: str, grid):
    _install_scripts_namespace()
    from puzzle_generators.rule_wrap import wrap_rule

    return bridge.eval_text(f"({wrap_rule(source)} {_grid_literal(grid)})")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_probe(out_dir: Path, *, base_seed: int = 20261020):
    """Execute both exact Racket settings and retain source-bound evidence."""
    from arc_repl.racket_bridge import RacketBridge

    out_dir.mkdir(parents=True, exist_ok=False)
    source_path = Path(__file__).resolve()
    report = {
        "schema": "c739fcbc6cbd-parametric-period-factor-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_scope": "proposed_not_selected_production_rule",
        "allowed_values": list(ALLOWED_PERIOD_FACTORS),
        "default_value": DEFAULT_PERIOD_FACTOR,
        "parameter_selection": "chosen once per episode and reused for all pairs",
        "labels": "retained outputs are overwritten with Racket bridge results",
        "prototype_source": str(source_path),
        "prototype_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "runtime": {
            "cwd": os.getcwd(),
            "argv": sys.argv,
            "python": sys.version,
            "racket_on_path": shutil.which("racket"),
            "racket_env": os.environ.get("RACKET"),
        },
        "episodes": [],
    }
    try:
        with RacketBridge(max_calls_before_restart=32) as bridge:
            for factor in ALLOWED_PERIOD_FACTORS:
                seed = base_seed + factor
                source = rule_source(factor)
                episode = build_episode(seed, period_factor=factor)
                rival_factor = 3 if factor == 2 else 2
                pair_rows = []
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        python_output = python_mirror(
                            pair["input"], period_factor=factor
                        )
                        racket_output = _racket_apply(bridge, source, pair["input"])
                        if racket_output != python_output:
                            raise AssertionError(
                                f"Racket/Python mismatch factor={factor} {split}[{index}]"
                            )
                        rival_output = python_mirror(
                            pair["input"], period_factor=rival_factor
                        )
                        if rival_output == racket_output:
                            raise AssertionError(
                                f"parameter rival survived factor={factor} {split}[{index}]"
                            )
                        # Retained labels are authority outputs, not Python-authored labels.
                        pair["output"] = racket_output
                        pair_rows.append(
                            {
                                "split": split,
                                "index": index,
                                "input": pair["input"],
                                "racket_output": racket_output,
                                "python_mirror_output": python_output,
                                "rival_period_factor": rival_factor,
                                "rival_output": rival_output,
                                "distinguished": True,
                            }
                        )

                rule_path = out_dir / f"period_factor_{factor}.rkt"
                rule_path.write_text(source + "\n", encoding="utf-8")
                challenge_path = out_dir / f"period_factor_{factor}_challenge.json"
                challenge_path.write_text(
                    json.dumps(public_challenge(episode), indent=2) + "\n",
                    encoding="utf-8",
                )
                report["episodes"].append(
                    {
                        "parameter": {"period_factor": factor},
                        "seed": seed,
                        "racket_source": source,
                        "racket_source_sha256": _sha256_text(source),
                        "rule_file": str(rule_path),
                        "rule_file_sha256": hashlib.sha256(rule_path.read_bytes()).hexdigest(),
                        "public_challenge": str(challenge_path),
                        "public_challenge_sha256": hashlib.sha256(
                            challenge_path.read_bytes()
                        ).hexdigest(),
                        "query_answer_omitted_from_public_challenge": True,
                        "hidden_parameter_omitted_from_public_challenge": True,
                        "pairs": pair_rows,
                    }
                )
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        report_path = out_dir / "evidence.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--base-seed", type=int, default=20261020)
    args = parser.parse_args(argv)
    report = run_probe(args.out, base_seed=args.base_seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "episodes": len(report["episodes"]),
            }
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

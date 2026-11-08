#!/usr/bin/env python3
"""Bounded shift-distance prototype for ce3c6d414140.

This is deliberately separate from the selected production generator.  It
chooses one rule parameter per episode, materializes the matching Racket rule,
and derives all labels through the protected Racket bridge when run as a CLI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys

ALLOWED_SHIFT_DISTANCES = (1, 2)
DEFAULT_SHIFT_DISTANCE = 1
EPISODE_SIZE = 4  # 3 demonstrations plus 1 query
_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _parallelogram(height: int, top_width: int) -> set[tuple[int, int]]:
    cells = {(0, c) for c in range(top_width)}
    cells.update((height - 1, c) for c in range(height - 2, height - 2 + top_width))
    cells.update((r, r - 1) for r in range(1, height - 1))
    cells.update((r, top_width + r - 1) for r in range(1, height - 1))
    return cells


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, set[tuple[int, int]]]] = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in _DIRS8:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _stays(grid):
    result: set[tuple[int, int]] = set()
    for _, cells in _components(grid):
        max_row = max(r for r, _ in cells)
        max_col = max(c for _, c in cells)
        result.update((r, c) for r, c in cells if r == max_row or c == max_col)
    return result


def python_mirror(grid, *, shift_distance: int):
    """Independent mirror of the parameterized Racket rule."""
    if shift_distance not in ALLOWED_SHIFT_DISTANCES:
        raise ValueError(f"unsupported shift_distance={shift_distance!r}")
    height, width = len(grid), len(grid[0])
    stays = _stays(grid)
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(height):
        for c in range(width):
            if (r, c) in stays:
                output[r][c] = grid[r][c]
            elif (
                c >= shift_distance
                and grid[r][c - shift_distance] != 0
                and (r, c - shift_distance) not in stays
            ):
                output[r][c] = grid[r][c - shift_distance]
    return output


def rule_source(shift_distance: int) -> str:
    if shift_distance not in ALLOWED_SHIFT_DISTANCES:
        raise ValueError(f"unsupported shift_distance={shift_distance!r}")
    return f"""(rule!
  (let* ((objs (objects-8 g 0))
         (stays
          (apply append
                 (map (lambda (o)
                        (let* ((cells (obj-cells o))
                               (rs (map first cells))
                               (cs (map second cells))
                               (maxr (max-list rs))
                               (maxc (max-list cs)))
                          (filter (lambda (p)
                                    (or (= (first p) maxr)
                                        (= (second p) maxc)))
                                  cells)))
                      objs))))
    (cellmap g
      (r c v)
      (cond
        ((member? (list r c) stays) v)
        ((and (>= c {shift_distance})
              (not (= (at g r (- c {shift_distance})) 0))
              (not (member? (list r (- c {shift_distance})) stays)))
         (at g r (- c {shift_distance})))
        (else 0)))))"""


def _input_for(rng: random.Random, index: int):
    height, width = 8, 12
    options = ((3, 3), (4, 3), (4, 4), (5, 3))
    object_height, top_width = options[index % len(options)]
    bbox_width = object_height + top_width - 2
    # Two columns of right margin make both parameter settings non-clipping.
    top = rng.randint(0, height - object_height)
    left = rng.randint(0, width - bbox_width - max(ALLOWED_SHIFT_DISTANCES))
    color = 1 + ((rng.randrange(9) + index) % 9)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in _parallelogram(object_height, top_width):
        grid[top + r][left + c] = color
    return grid


def build_episode(seed: int, *, shift_distance: int | None = None):
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if shift_distance is None:
        shift_distance = ALLOWED_SHIFT_DISTANCES[seed % len(ALLOWED_SHIFT_DISTANCES)]
    if shift_distance not in ALLOWED_SHIFT_DISTANCES:
        raise ValueError(f"unsupported shift_distance={shift_distance!r}")
    rng = random.Random(seed)
    pairs = []
    for index in range(EPISODE_SIZE):
        grid = _input_for(rng, index)
        pairs.append(
            {
                "input": grid,
                "output": python_mirror(grid, shift_distance=shift_distance),
            }
        )
    return {
        "parameter": {"shift_distance": shift_distance},
        "seed": seed,
        "train": pairs[:-1],
        "test": pairs[-1:],
    }


def _grid_literal(grid):
    rows = " ".join("(" + " ".join(str(v) for v in row) + ")" for row in grid)
    return f"'({rows})"


def _racket_apply(bridge, source, grid):
    # The packet keeps portable checker helpers under shared/tools, while
    # rule_wrap imports them through the staged runtime name ``scripts``.
    # Install that namespace locally so this task-workspace probe runs both
    # directly in the packet and inside the staged checker.
    import types

    repo_root = Path(__file__).resolve().parents[4]
    tools_dir = repo_root / "shared" / "tools"
    if "scripts" not in sys.modules and tools_dir.is_dir():
        package = types.ModuleType("scripts")
        package.__path__ = [str(tools_dir)]
        sys.modules["scripts"] = package

    from puzzle_generators.rule_wrap import wrap_rule

    return bridge.eval_text(f"({wrap_rule(source)} {_grid_literal(grid)})")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _public_challenge(episode):
    return {
        "train": episode["train"],
        "test": [{"input": episode["test"][0]["input"]}],
    }


def run_probe(out_dir: Path, *, base_seed: int = 8100):
    from arc_repl.racket_bridge import RacketBridge

    out_dir.mkdir(parents=True, exist_ok=False)
    source_path = Path(__file__).resolve()
    report = {
        "schema": "ce3c6d414140-parametric-shift-distance-v1",
        "status": "running",
        "task_id": "ce3c6d414140",
        "prototype_scope": "proposed_not_selected_production_rule",
        "allowed_values": list(ALLOWED_SHIFT_DISTANCES),
        "default_value": DEFAULT_SHIFT_DISTANCE,
        "parameter_selection": "chosen once per episode and reused for all pairs",
        "prototype_source": str(source_path),
        "prototype_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "episodes": [],
    }
    try:
        with RacketBridge(max_calls_before_restart=32) as bridge:
            for distance in ALLOWED_SHIFT_DISTANCES:
                seed = base_seed + distance
                source = rule_source(distance)
                episode = build_episode(seed, shift_distance=distance)
                rival = 2 if distance == 1 else 1
                pair_rows = []
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        racket_output = _racket_apply(bridge, source, pair["input"])
                        if racket_output != pair["output"]:
                            raise AssertionError(
                                f"Racket/Python mismatch distance={distance} {split}[{index}]"
                            )
                        rival_output = python_mirror(
                            pair["input"], shift_distance=rival
                        )
                        if rival_output == racket_output:
                            raise AssertionError(
                                f"parameter rival survived distance={distance} {split}[{index}]"
                            )
                        pair_rows.append(
                            {
                                "split": split,
                                "index": index,
                                "input": pair["input"],
                                "racket_output": racket_output,
                                "rival_shift_distance": rival,
                                "rival_output": rival_output,
                                "distinguished": True,
                            }
                        )

                rule_path = out_dir / f"shift_distance_{distance}.rkt"
                rule_path.write_text(source + "\n", encoding="utf-8")
                challenge_path = out_dir / f"shift_distance_{distance}_challenge.json"
                challenge_path.write_text(
                    json.dumps(_public_challenge(episode), indent=2) + "\n",
                    encoding="utf-8",
                )
                report["episodes"].append(
                    {
                        "parameter": {"shift_distance": distance},
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


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--base-seed", type=int, default=8100)
    args = parser.parse_args(argv)
    report = run_probe(args.out, base_seed=args.base_seed)
    print(json.dumps({
        "status": report["status"],
        "out": str(args.out),
        "episodes": len(report["episodes"]),
    }))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

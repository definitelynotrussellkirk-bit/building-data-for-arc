"""Bounded target-rank prototype for ARC task 351de765e33f.

The production rule fixes ``target_rank=2``.  This prototype tests the nearest
meaningful family member, ``target_rank=1``, without changing production code.
Each episode chooses the parameter once and uses it for all demonstrations and
the held-out query.  Public challenge files deliberately omit both the hidden
parameter and the query answer.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
from pathlib import Path
from typing import Iterable

ALLOWED_TARGET_RANKS = (1, 2)
DEFAULT_TARGET_RANK = 2
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

_CANONICAL_RACKET = """(rule!
  (let ((objs (sort (objects g 0)
                    (lambda (a b)
                      (cond [(not (= (obj-size a) (obj-size b))) (> (obj-size a) (obj-size b))]
                            [(not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b))]
                            [else (< (obj-c1 a) (obj-c1 b))])))))
    (if (empty? objs)
        g
        (paint-cells g (obj-cells (if (>= (length objs) 2) (second objs) (first objs))) 8))))"""

_RANK_ONE_RACKET = """(rule!
  (let ((objs (sort (objects g 0)
                    (lambda (a b)
                      (cond [(not (= (obj-size a) (obj-size b))) (> (obj-size a) (obj-size b))]
                            [(not (= (obj-r1 a) (obj-r1 b))) (< (obj-r1 a) (obj-r1 b))]
                            [else (< (obj-c1 a) (obj-c1 b))])))))
    (if (empty? objs)
        g
        (paint-cells g (obj-cells (first objs)) 8))))"""


def load_generator():
    return importlib.import_module(
        "puzzle_generators.per_puzzle.351de765e33f.generator"
    )


def racket_program(target_rank: int = DEFAULT_TARGET_RANK) -> str:
    _validate_rank(target_rank)
    return _RANK_ONE_RACKET if target_rank == 1 else _CANONICAL_RACKET


def _validate_rank(target_rank: int) -> None:
    if type(target_rank) is not int or target_rank not in ALLOWED_TARGET_RANKS:
        raise ValueError(
            f"target_rank must be one of {ALLOWED_TARGET_RANKS}, got {target_rank!r}"
        )


def _components(grid: list[list[int]]) -> list[dict]:
    """Independent same-color 4-connected oracle (no production helpers)."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in _DIR4:
                    neighbor = current[0] + dr, current[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "r1": min(cell[0] for cell in cells),
                    "c1": min(cell[1] for cell in cells),
                }
            )
    return sorted(result, key=lambda obj: (-obj["size"], obj["r1"], obj["c1"]))


def apply_rank(grid: list[list[int]], target_rank: int) -> list[list[int]]:
    _validate_rank(target_rank)
    objects = _components(grid)
    output = [row[:] for row in grid]
    if not objects:
        return output
    index = min(target_rank, len(objects)) - 1
    for row, col in objects[index]["cells"]:
        output[row][col] = 8
    return output


def build_episode(*, seed: int, target_rank: int) -> dict:
    _validate_rank(target_rank)
    generator = load_generator()
    pairs = []
    for sample_index in range(4):
        grid = generator.generate(seed, sample_index, difficulty="medium")
        pairs.append(
            {
                "sample_index": sample_index,
                "input": grid,
                "output": apply_rank(grid, target_rank),
            }
        )
    return {
        "task_id": "351de765e33f",
        "prototype_axis": "target_rank",
        "target_rank": target_rank,
        "racket_program": racket_program(target_rank),
        "pairs": pairs,
    }


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(output_dir: Path | str) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    episodes = {}
    for rank in ALLOWED_TARGET_RANKS:
        episode = build_episode(seed=91001, target_rank=rank)
        episodes[rank] = episode
        private_path = output / f"episode-rank-{rank}.json"
        _write_json(private_path, episode)
        files.append(private_path)

        challenge = {
            "task_id": "351de765e33f-parametric",
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["pairs"][:3]
            ],
            "test": [{"input": episode["pairs"][3]["input"]}],
        }
        challenge_path = output / f"challenge-rank-{rank}.json"
        _write_json(challenge_path, challenge)
        files.append(challenge_path)

        racket_path = output / f"rule-rank-{rank}.rkt"
        racket_path.write_text(episode["racket_program"] + "\n")
        files.append(racket_path)

    differing = [
        index
        for index, (left, right) in enumerate(
            zip(episodes[1]["pairs"], episodes[2]["pairs"])
        )
        if left["output"] != right["output"]
    ]
    if differing != [0, 1, 2, 3]:
        raise RuntimeError(f"prototype settings failed to differ: {differing}")

    generator = load_generator()
    for pair in episodes[2]["pairs"]:
        if pair["output"] != generator.rule_mirror(pair["input"]):
            raise RuntimeError("rank-two prototype diverged from production mirror")

    receipt = {
        "status": "complete",
        "task_id": "351de765e33f",
        "axis": "target_rank",
        "allowed_values": list(ALLOWED_TARGET_RANKS),
        "default_value": DEFAULT_TARGET_RANK,
        "canonical_rank_two_rule_hash": hashlib.sha256(
            " ".join(racket_program(2).split()).encode()
        ).hexdigest()[:12],
        "differing_pair_indexes": differing,
        "racket_executable": shutil.which("racket"),
        "verification": {
            "rank_two_matches_production_python_mirror": True,
            "independent_component_oracle": True,
            "racket_execution_performed": False,
            "racket_execution_note": (
                "No Racket executable was present in this reconstructed runtime; "
                "the exact programs and complete episodes are materialized for replay."
            ),
        },
        "files": {},
    }
    receipt_path = output / "receipt.json"
    _write_json(receipt_path, receipt)
    files.append(receipt_path)
    receipt["files"] = {
        path.name: _sha256(path)
        for path in files
        if path != receipt_path
    }
    _write_json(receipt_path, receipt)
    return receipt


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("evidence"),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    receipt = materialize(args.output)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

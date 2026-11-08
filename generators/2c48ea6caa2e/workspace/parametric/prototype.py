#!/usr/bin/env python3
"""Isolated fixed-count threshold prototype for task 2c48ea6caa2e.

The selected production generator and canonical authority stay fixed.  This
prototype varies exactly one hidden rule parameter once per complete episode:
``threshold`` is 3, 4 (the canonical/default setting), or 5.  In every setting,
the rule keeps blue cells and fills zero cells inside the blue bounding box with
red when their row or column contains at least ``threshold`` blue cells.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge


TASK_ID = "2c48ea6caa2e"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_THRESHOLDS = (3, 4, 5)
DEFAULT_THRESHOLD = 4
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"


_BASE_MASK = (
    (1, 0, 1, 0, 1, 0, 1, 0, 1),  # five blues
    (1, 0, 1, 0, 1, 0, 0, 0, 1),  # four blues
    (1, 0, 1, 0, 0, 0, 0, 0, 1),  # three blues
    (1, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 1),
    (1, 0, 0, 0, 0, 0, 0, 0, 1),
)


def _validate_threshold(threshold: int) -> int:
    if type(threshold) is not int or threshold not in ALLOWED_THRESHOLDS:
        raise ValueError(
            f"threshold must be one of {ALLOWED_THRESHOLDS}, got {threshold!r}"
        )
    return threshold


def choose_threshold(seed: int) -> int:
    """Choose one immutable hidden setting for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    digest = hashlib.sha256(f"{TASK_ID}|threshold|{seed}".encode("utf-8")).digest()
    return ALLOWED_THRESHOLDS[digest[0] % len(ALLOWED_THRESHOLDS)]


def program_for(threshold: int) -> str:
    """Return the exact proposed Racket authority for one setting."""
    value = _validate_threshold(threshold)
    return f"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (bb (bbox-of-cells (find-color g 1)))
                (r1 (first bb))
                (c1 (second bb))
                (r2 (third bb))
                (c2 (fourth bb))
                (row-blues (map (lambda (r) (row-count g r 1)) (range 0 h)))
                (col-blues (map (lambda (c) (col-count g c 1)) (range 0 w))))
           (cellmap g
                    (r c v)
                    (if (= 1 v)
                        1
                        (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2) (zero? v))
                            (if (or (>= (nth row-blues r) {value}) (>= (nth col-blues c) {value}))
                                2
                                0)
                            0))))))"""


def rule_path(threshold: int) -> Path:
    return RULE_DIR / f"threshold_{_validate_threshold(threshold)}.rkt"


def _rule_body(program: str) -> str:
    text = program.strip()
    if not text.startswith("(rule!") or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len("(rule!") : -1].strip()


def apply_racket(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute an exact proposed rule through the included Racket bridge."""
    bridge.define_grid("prototype_input", grid)
    return bridge.eval_text(f"({_rule_body(program)} prototype_input)")


def _validate_grid(grid: list[list[int]]) -> None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be a nonempty rectangular list")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")


def apply_python(grid: list[list[int]], threshold: int) -> list[list[int]]:
    """Independent mirror used to check exact Racket executions."""
    value = _validate_threshold(threshold)
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    blues = [
        (row, col)
        for row, values in enumerate(grid)
        for col, cell in enumerate(values)
        if cell == 1
    ]
    if not blues:
        raise ValueError("prototype inputs require at least one blue cell")
    top = min(row for row, _col in blues)
    bottom = max(row for row, _col in blues)
    left = min(col for _row, col in blues)
    right = max(col for _row, col in blues)
    row_counts = [sum(cell == 1 for cell in row) for row in grid]
    col_counts = [
        sum(grid[row][col] == 1 for row in range(height))
        for col in range(width)
    ]
    return [
        [
            1
            if grid[row][col] == 1
            else 2
            if (
                top <= row <= bottom
                and left <= col <= right
                and grid[row][col] == 0
                and (row_counts[row] >= value or col_counts[col] >= value)
            )
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def _transform(mask: tuple[tuple[int, ...], ...], orientation: int) -> list[list[int]]:
    grid = [list(row) for row in mask]
    if orientation >= 4:
        grid = [list(reversed(row)) for row in grid]
    for _turn in range(orientation % 4):
        grid = [list(row) for row in zip(*reversed(grid))]
    return grid


def make_input(seed: int, index: int) -> list[list[int]]:
    """Build a lawful input where all three thresholds disagree."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative integer (not bool)")
    digest = hashlib.sha256(f"{TASK_ID}|input|{seed}|{index}".encode("utf-8")).digest()
    orientation = (digest[0] + 3 * index) % 8
    mask = _transform(_BASE_MASK, orientation)
    top = 1 + digest[1] % 4
    bottom = 1 + digest[2] % 4
    left = 1 + digest[3] % 4
    right = 1 + digest[4] % 4
    height = top + len(mask) + bottom
    width = left + len(mask[0]) + right
    grid = [[0 for _col in range(width)] for _row in range(height)]
    for row, values in enumerate(mask, start=top):
        for col, cell in enumerate(values, start=left):
            grid[row][col] = cell
    outputs = {threshold: apply_python(grid, threshold) for threshold in ALLOWED_THRESHOLDS}
    if len({json.dumps(output, separators=(",", ":")) for output in outputs.values()}) != 3:
        raise AssertionError("prototype input does not distinguish all threshold settings")
    return grid


def build_episode(seed: int, threshold: int | None = None) -> dict[str, Any]:
    """Build three demonstrations and one query under one fixed setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    setting = choose_threshold(seed) if threshold is None else _validate_threshold(threshold)
    pairs = []
    for index in range(4):
        grid = make_input(seed, index)
        pairs.append({"input": grid, "output": apply_python(grid, setting)})
    return {
        "schema": "2c48ea6caa2e-parametric-threshold-private-episode-v1",
        "train": pairs[:3],
        "test": pairs[3:],
        "program": program_for(setting),
        "meta": {
            "seed": seed,
            "threshold": setting,
            "canonical_default": DEFAULT_THRESHOLD,
            "prototype_version": PROTOTYPE_VERSION,
        },
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Report any declared threshold rival not distinguished by the episode."""
    setting = _validate_threshold(episode["meta"]["threshold"])
    findings: list[str] = []
    for rival in ALLOWED_THRESHOLDS:
        if rival == setting:
            continue
        demo_disagreements = [
            apply_python(pair["input"], rival) != pair["output"]
            for pair in episode["train"]
        ]
        if not all(demo_disagreements):
            findings.append(
                f"not every demonstration refutes rival threshold={rival}"
            )
        if any(
            apply_python(pair["input"], rival) == pair["output"]
            for pair in episode["test"]
        ):
            findings.append(f"query does not distinguish rival threshold={rival}")
    return findings


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Expose demonstrations and unlabelled queries, omitting hidden semantics."""
    return {
        "schema": "2c48ea6caa2e-parametric-public-v1",
        "train": copy.deepcopy(episode["train"]),
        "test": [
            {"input": copy.deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


def _find_seed_for(setting: int, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_threshold(seed) != setting:
        seed += 1
    return seed


def materialize(
    evidence_path: Path,
    *,
    public_dir: Path,
    seed_start: int = 26000,
) -> dict[str, Any]:
    """Execute all settings in Racket and retain bounded prototype evidence."""
    if type(seed_start) is not int:
        raise TypeError("seed_start must be an integer (not bool)")
    evidence_path = Path(evidence_path)
    public_dir = Path(public_dir)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(__file__).resolve()
    used: set[int] = set()
    episodes: list[dict[str, Any]] = []
    with RacketBridge(max_calls_before_restart=96) as bridge:
        for offset, setting in enumerate(ALLOWED_THRESHOLDS):
            seed = _find_seed_for(setting, seed_start + offset, used)
            used.add(seed)
            episode = build_episode(seed)
            if episode["meta"]["threshold"] != setting:
                raise AssertionError("seed search selected the wrong threshold")

            retained_program = rule_path(setting).read_text(encoding="utf-8")
            if retained_program != episode["program"]:
                raise AssertionError(f"retained Racket source differs for threshold={setting}")

            executions: list[dict[str, Any]] = []
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    actual = apply_racket(bridge, retained_program, pair["input"])
                    python_output = apply_python(pair["input"], setting)
                    if actual != python_output or actual != pair["output"]:
                        raise AssertionError(
                            f"Racket/Python/episode mismatch for threshold={setting} "
                            f"{split}[{pair_index}]"
                        )
                    pair["output"] = actual
                    rival_outputs = {
                        str(rival): apply_racket(
                            bridge,
                            program_for(rival),
                            pair["input"],
                        )
                        for rival in ALLOWED_THRESHOLDS
                        if rival != setting
                    }
                    executions.append(
                        {
                            "split": split,
                            "pair_index": pair_index,
                            "input_sha256": _sha256_json(pair["input"]),
                            "output_sha256": _sha256_json(actual),
                            "racket_matches_python": actual == python_output,
                            "rival_output_sha256": {
                                rival: _sha256_json(output)
                                for rival, output in rival_outputs.items()
                            },
                            "chosen_differs_from_all_rivals": all(
                                actual != output for output in rival_outputs.values()
                            ),
                        }
                    )

            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError(findings)
            if not all(
                row["chosen_differs_from_all_rivals"]
                for row in executions
                if row["split"] == "train"
            ):
                raise AssertionError("a demonstration failed to refute every threshold rival")

            public = public_challenge(episode)
            filename = f"episode_seed_{seed}.json"
            public_path = public_dir / filename
            public_path.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
            episodes.append(
                {
                    "seed": seed,
                    "threshold": setting,
                    "is_canonical_default": setting == DEFAULT_THRESHOLD,
                    "program_path": str(rule_path(setting).relative_to(ROOT)),
                    "program_text": retained_program,
                    "program_sha256": _sha256_text(retained_program),
                    "public_path": str(public_path),
                    "public_sha256": _sha256_json(public),
                    "episode": episode,
                    "executions": executions,
                    "parameter_rival_findings": findings,
                    "every_demo_refutes_all_alternatives": True,
                }
            )

    report = {
        "schema": "2c48ea6caa2e-parametric-threshold-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "threshold",
            "allowed_values": list(ALLOWED_THRESHOLDS),
            "canonical_default": DEFAULT_THRESHOLD,
            "chosen_once_per_episode": True,
            "selection": "SHA-256(task_id|threshold|seed) modulo 3, once per episode",
            "invariant_reasoning": (
                "Find the blue bounding box, count blue cells by row and column, "
                "and fill interior zeros when either count reaches the episode threshold."
            ),
            "input_constraints": (
                "Each retained 9x9 blue mask has row/column counts crossing 3, 4, "
                "and 5, so every demonstration distinguishes all allowed settings."
            ),
        },
        "prototype_source": str(source_path),
        "prototype_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "episodes": episodes,
        "limitations": [
            "This is an isolated proposal, not a production generator or authority change.",
            "Evidence covers three complete deterministic episodes and only the two declared threshold rivals per episode.",
            "The deliberately diagnostic mask family does not establish identifiability against undeclared alternative rules.",
        ],
    }
    evidence_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=26000)
    args = parser.parse_args()
    report = materialize(
        args.out,
        public_dir=args.write_public,
        seed_start=args.seed_start,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "prototype_source_sha256": report["prototype_source_sha256"],
                "episodes": [
                    {
                        "seed": row["seed"],
                        "threshold": row["threshold"],
                        "program_sha256": row["program_sha256"],
                        "every_demo_refutes_all_alternatives": row[
                            "every_demo_refutes_all_alternatives"
                        ],
                        "public_path": row["public_path"],
                    }
                    for row in report["episodes"]
                ],
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

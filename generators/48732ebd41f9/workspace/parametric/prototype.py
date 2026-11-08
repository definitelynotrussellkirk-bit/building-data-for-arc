#!/usr/bin/env python3
"""Isolated minimum-height rule prototype for task 48732ebd41f9.

The selected production generator and canonical Racket authority remain fixed.
This prototype varies one hidden rule parameter once per complete episode:
``minimum_height`` is either 2 (the canonical/default setting) or 3.  In both
settings the rule finds the greatest-area all-zero rectangle whose height meets
the threshold and recolors that rectangle with 6.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge


TASK_ID = "48732ebd41f9"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_MIN_HEIGHTS = (2, 3)
DEFAULT_MIN_HEIGHT = 2
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"


def _validate_minimum_height(minimum_height: int) -> int:
    if type(minimum_height) is not int or minimum_height not in ALLOWED_MIN_HEIGHTS:
        raise ValueError(
            "minimum_height must be one of "
            f"{ALLOWED_MIN_HEIGHTS}, got {minimum_height!r}"
        )
    return minimum_height


def choose_minimum_height(seed: int) -> int:
    """Choose one hidden setting deterministically for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    digest = hashlib.sha256(f"{TASK_ID}|minimum-height|{seed}".encode()).digest()
    return ALLOWED_MIN_HEIGHTS[digest[0] % len(ALLOWED_MIN_HEIGHTS)]


def program_for(minimum_height: int) -> str:
    """Return the exact proposed Racket authority for one threshold setting."""
    threshold = _validate_minimum_height(minimum_height)
    return f"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((rect (tallest-rect g 0 {threshold}))
                  (r1 (nth rect 0))
                  (c1 (nth rect 1))
                  (r2 (nth rect 2))
                  (c2 (nth rect 3)))
             (cellmap g
                      (r c v)
                      (if (and (>= r r1) (<= r r2) (>= c c1) (<= c c2) (zero? v)) 6 v))))))"""


def rule_path(minimum_height: int) -> Path:
    return RULE_DIR / f"minimum_height_{_validate_minimum_height(minimum_height)}.rkt"


def _rule_body(program: str) -> str:
    text = program.strip()
    prefix = "(rule!"
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("prototype program must be a (rule! BODY) form")
    return text[len(prefix) : -1].strip()


def apply_racket(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute one exact rule through the protected Racket bridge."""
    bridge.define_grid("prototype_input", grid)
    body = _rule_body(program)
    return bridge.eval_text(f"({body} prototype_input)")


def _validate_grid(grid: list[list[int]]) -> None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be a nonempty rectangular list")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")


def _zero_rectangles(
    grid: list[list[int]], minimum_height: int
) -> list[tuple[int, int, int, int, int]]:
    threshold = _validate_minimum_height(minimum_height)
    height, width = len(grid), len(grid[0])
    rectangles: list[tuple[int, int, int, int, int]] = []
    for top in range(height):
        valid = [True] * width
        for bottom in range(top, height):
            for col in range(width):
                if grid[bottom][col] != 0:
                    valid[col] = False
            rect_height = bottom - top + 1
            if rect_height < threshold:
                continue
            start: int | None = None
            for col in range(width + 1):
                if col < width and valid[col]:
                    if start is None:
                        start = col
                elif start is not None:
                    rectangles.append(
                        (
                            top,
                            start,
                            bottom,
                            col - 1,
                            rect_height * (col - start),
                        )
                    )
                    start = None
    return rectangles


def _largest_rectangle(
    grid: list[list[int]], minimum_height: int
) -> tuple[int, int, int, int, int]:
    rectangles = _zero_rectangles(grid, minimum_height)
    if not rectangles:
        raise ValueError("no all-zero rectangle meets the minimum height")
    greatest_area = max(rect[4] for rect in rectangles)
    return next(rect for rect in rectangles if rect[4] == greatest_area)


def apply_python(grid: list[list[int]], minimum_height: int) -> list[list[int]]:
    """Independent Python mirror used only to assert exact Racket executions."""
    _validate_grid(grid)
    top, left, bottom, right, _ = _largest_rectangle(grid, minimum_height)
    output = copy.deepcopy(grid)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if output[row][col] == 0:
                output[row][col] = 6
    return output


# Each scene contains a unique low/wide 2-row rectangle and a unique taller,
# smaller-area rectangle.  Threshold 2 selects the former; threshold 3 excludes
# it and selects the latter.  Foreground separates the candidates completely.
_SCENES = (
    ((0, 1, 2, 7), (3, 13, 4, 3)),
    ((5, 11, 2, 7), (0, 2, 3, 4)),
    ((1, 12, 2, 6), (4, 2, 3, 3)),
    ((6, 1, 2, 8), (1, 15, 4, 3)),
)
_FOREGROUND_COLORS = (1, 2, 3, 4, 5, 7, 8, 9)


def _carve(
    grid: list[list[int]], rectangle: tuple[int, int, int, int]
) -> None:
    top, left, height, width = rectangle
    for row in range(top, top + height):
        for col in range(left, left + width):
            grid[row][col] = 0


def make_input(seed: int, index: int) -> list[list[int]]:
    """Build a deterministic threshold-discriminating input scene."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative integer (not bool)")
    height, width = 8, 20
    foreground = _FOREGROUND_COLORS[(seed + index) % len(_FOREGROUND_COLORS)]
    grid = [[foreground for _ in range(width)] for _ in range(height)]
    low_wide, tall = _SCENES[(seed + index) % len(_SCENES)]
    _carve(grid, low_wide)
    _carve(grid, tall)

    winners = {
        threshold: _largest_rectangle(grid, threshold)
        for threshold in ALLOWED_MIN_HEIGHTS
    }
    if winners[2] == winners[3]:
        raise AssertionError("prototype scene does not distinguish its thresholds")
    return grid


def build_episode(
    seed: int,
    minimum_height: int | None = None,
) -> dict[str, Any]:
    """Build three demonstrations and one query under one immutable setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    setting = (
        choose_minimum_height(seed)
        if minimum_height is None
        else _validate_minimum_height(minimum_height)
    )
    inputs = [make_input(seed, index) for index in range(4)]
    pairs = [
        {"input": grid, "output": apply_python(grid, setting)} for grid in inputs
    ]
    return {
        "schema": "48732ebd41f9-parametric-minimum-height-episode-v1",
        "train": pairs[:3],
        "test": pairs[3:],
        "program": program_for(setting),
        "meta": {
            "seed": seed,
            "minimum_height": setting,
            "canonical_default": DEFAULT_MIN_HEIGHT,
            "prototype_version": PROTOTYPE_VERSION,
        },
    }


def parameter_rival_findings(episode: dict[str, Any]) -> list[str]:
    """Report ambiguity against the sole other declared threshold setting."""
    setting = _validate_minimum_height(episode["meta"]["minimum_height"])
    rival = next(value for value in ALLOWED_MIN_HEIGHTS if value != setting)
    findings: list[str] = []
    distinguishing = [
        index
        for index, pair in enumerate(episode["train"])
        if apply_python(pair["input"], rival) != pair["output"]
    ]
    if not distinguishing:
        findings.append(f"rival minimum_height={rival} fits every demonstration")
    if any(
        apply_python(pair["input"], rival) == pair["output"]
        for pair in episode["test"]
    ):
        findings.append(f"query does not distinguish minimum_height={rival}")
    return findings


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return demonstrations and unlabelled queries without hidden semantics."""
    return {
        "schema": "48732ebd41f9-parametric-minimum-height-public-v1",
        "train": copy.deepcopy(episode["train"]),
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


def _find_seed_for(setting: int, start: int, used: set[int]) -> int:
    seed = start
    while seed in used or choose_minimum_height(seed) != setting:
        seed += 1
    return seed


def materialize(
    evidence_path: Path,
    *,
    public_dir: Path,
    seed_start: int = 6200,
) -> dict[str, Any]:
    """Execute both exact settings in Racket and retain bounded evidence."""
    if type(seed_start) is not int:
        raise TypeError("seed_start must be an integer (not bool)")
    evidence_path = Path(evidence_path)
    public_dir = Path(public_dir)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(__file__).resolve()
    used: set[int] = set()
    episodes: list[dict[str, Any]] = []
    with RacketBridge(max_calls_before_restart=64) as bridge:
        for offset, setting in enumerate(ALLOWED_MIN_HEIGHTS):
            seed = _find_seed_for(setting, seed_start + offset, used)
            used.add(seed)
            episode = build_episode(seed)
            if episode["meta"]["minimum_height"] != setting:
                raise AssertionError("seed search returned the wrong setting")

            retained_program = rule_path(setting).read_text(encoding="utf-8")
            if retained_program != episode["program"]:
                raise AssertionError(
                    f"retained Racket source differs for minimum_height={setting}"
                )
            rival = next(value for value in ALLOWED_MIN_HEIGHTS if value != setting)
            executions = []
            for split in ("train", "test"):
                for pair_index, pair in enumerate(episode[split]):
                    actual = apply_racket(bridge, episode["program"], pair["input"])
                    python_output = apply_python(pair["input"], setting)
                    rival_output = apply_racket(
                        bridge, program_for(rival), pair["input"]
                    )
                    if actual != python_output or actual != pair["output"]:
                        raise AssertionError(
                            "Racket/Python/episode mismatch for "
                            f"minimum_height={setting} {split}[{pair_index}]"
                        )
                    pair["output"] = actual
                    executions.append(
                        {
                            "split": split,
                            "pair_index": pair_index,
                            "input_sha256": _sha256_json(pair["input"]),
                            "output_sha256": _sha256_json(actual),
                            "rival_minimum_height": rival,
                            "rival_output_sha256": _sha256_json(rival_output),
                            "settings_disagree": actual != rival_output,
                        }
                    )

            findings = parameter_rival_findings(episode)
            if findings:
                raise AssertionError(findings)
            if not all(
                row["settings_disagree"]
                for row in executions
                if row["split"] == "train"
            ):
                raise AssertionError("not every demonstration refutes the threshold rival")

            public = public_challenge(episode)
            filename = f"minimum_height_{setting}_seed_{seed}.json"
            public_path = public_dir / filename
            public_path.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
            episodes.append(
                {
                    "seed": seed,
                    "minimum_height": setting,
                    "is_canonical_default": setting == DEFAULT_MIN_HEIGHT,
                    "program_path": str(rule_path(setting).relative_to(ROOT)),
                    "program_text": episode["program"],
                    "program_sha256": _sha256_text(episode["program"]),
                    "public_filename": filename,
                    "public_sha256": _sha256_json(public),
                    "episode": episode,
                    "executions": executions,
                    "parameter_rival_findings": findings,
                    "every_demo_refutes_alternative_setting": True,
                }
            )

    report = {
        "schema": "48732ebd41f9-parametric-minimum-height-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "minimum_height",
            "allowed_values": list(ALLOWED_MIN_HEIGHTS),
            "canonical_default": DEFAULT_MIN_HEIGHT,
            "chosen_once_per_episode": True,
            "selection": (
                "SHA-256(task_id|minimum-height|seed) modulo 2, once per episode"
            ),
            "input_constraints": (
                "Each input has a unique low/wide two-row zero rectangle and a "
                "unique taller smaller-area zero rectangle; foreground separates "
                "them, so thresholds 2 and 3 select different targets."
            ),
        },
        "prototype_source": str(source_path),
        "prototype_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "episodes": episodes,
        "limitations": [
            "This is an isolated proposal, not a production generator or authority change.",
            "Evidence covers two complete deterministic episodes and the sole declared parameter rival.",
            "The clean two-rectangle grammar is intentionally bounded and does not establish identifiability against undeclared rules.",
        ],
    }
    evidence_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=6200)
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
                        "minimum_height": row["minimum_height"],
                        "program_sha256": row["program_sha256"],
                        "every_demo_refutes_alternative_setting": row[
                            "every_demo_refutes_alternative_setting"
                        ],
                        "public_filename": row["public_filename"],
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

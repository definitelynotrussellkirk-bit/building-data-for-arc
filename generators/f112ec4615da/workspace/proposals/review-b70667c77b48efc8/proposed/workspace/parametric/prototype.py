#!/usr/bin/env python3
"""Prototype an episode-level quadrant overlay priority for f112ec4615da.

The selected production rule remains ``tr_bl_br_tl`` (highest to lowest).
The proposed alternative reverses that order while retaining the same four
quadrant roles, local-coordinate alignment, nonzero transparency, and output
shape.  One setting is chosen from the episode seed and shared by two labelled
demonstrations and one hidden-answer query.  Retained evidence executes exact
standalone Racket programs for both settings.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


TASK_ID = "f112ec4615da"
PARAMETER_NAME = "overlay_priority"
DEFAULT_OVERLAY_PRIORITY = "tr_bl_br_tl"
ALTERNATIVE_OVERLAY_PRIORITY = "tl_br_bl_tr"
ALLOWED_OVERLAY_PRIORITIES = (
    DEFAULT_OVERLAY_PRIORITY,
    ALTERNATIVE_OVERLAY_PRIORITY,
)
PROTOTYPE_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"
_ROLE_ORDERS = {
    DEFAULT_OVERLAY_PRIORITY: ("tr", "bl", "br", "tl"),
    ALTERNATIVE_OVERLAY_PRIORITY: ("tl", "br", "bl", "tr"),
}

# Portable task runtimes expose reviewer_support directly. Repository commands
# do not install it, so add the nearest source-bound shared/runtime directory
# without consulting cwd, environment-selected repositories, or siblings.
try:
    from reviewer_support import find_root, load_selected_generator
except ImportError:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "shared" / "runtime"
        if (candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    from reviewer_support import find_root, load_selected_generator


def _selected_generator():
    return load_selected_generator(
        TASK_ID,
        root=find_root(__file__),
    )


def _validate_seed(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("episode seed must be a nonnegative integer (not bool)")
    return value


def _validate_priority(value: str) -> str:
    if type(value) is not str or value not in ALLOWED_OVERLAY_PRIORITIES:
        raise ValueError(
            "overlay_priority must be one of "
            f"{ALLOWED_OVERLAY_PRIORITIES}, got {value!r}"
        )
    return value


def choose_parameters(episode_seed: int) -> dict[str, str]:
    seed = _validate_seed(episode_seed)
    return {
        PARAMETER_NAME: ALLOWED_OVERLAY_PRIORITIES[
            seed % len(ALLOWED_OVERLAY_PRIORITIES)
        ]
    }


def _validate_grid(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty row list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if len(grid) % 2 or width % 2:
        raise ValueError("grid dimensions must both be even")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return [row[:] for row in grid]


def python_reference(
    grid: list[list[int]],
    *,
    overlay_priority: str,
) -> list[list[int]]:
    """Independent local-coordinate overlay for one priority setting."""
    priority = _validate_priority(overlay_priority)
    source = _validate_grid(grid)
    height = len(source)
    width = len(source[0])
    half_h = height // 2
    half_w = width // 2

    def values(row: int, col: int) -> dict[str, int]:
        return {
            "tl": source[row][col],
            "tr": source[row][col + half_w],
            "bl": source[row + half_h][col],
            "br": source[row + half_h][col + half_w],
        }

    output = [[0] * half_w for _ in range(half_h)]
    for row in range(half_h):
        for col in range(half_w):
            local = values(row, col)
            output[row][col] = next(
                (
                    local[role]
                    for role in _ROLE_ORDERS[priority]
                    if local[role] != 0
                ),
                0,
            )
    return output


def _derived_seed(episode_seed: int, pair_index: int) -> int:
    digest = hashlib.sha256(
        f"f112ec4615da:parametric-priority:v1:{episode_seed}:{pair_index}".encode()
    ).hexdigest()
    return int(digest[:15], 16)


def build_input(episode_seed: int, pair_index: int) -> list[list[int]]:
    seed = _validate_seed(episode_seed)
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer (not bool)")
    generator, _path, _digest = _selected_generator()
    grid = generator.generate(
        _derived_seed(seed, pair_index),
        pair_index,
        difficulty="medium",
        grid_h=6,
        grid_w=6,
    )
    canonical = python_reference(
        grid,
        overlay_priority=DEFAULT_OVERLAY_PRIORITY,
    )
    alternative = python_reference(
        grid,
        overlay_priority=ALTERNATIVE_OVERLAY_PRIORITY,
    )
    if canonical != generator.rule_mirror(grid):
        raise AssertionError(
            "prototype default diverges from selected canonical rule"
        )
    if canonical == alternative:
        raise AssertionError(
            "prototype input does not distinguish overlay priorities"
        )
    return grid


def build_episode(
    episode_seed: int,
    *,
    overlay_priority: str | None = None,
) -> dict[str, Any]:
    seed = _validate_seed(episode_seed)
    priority = (
        choose_parameters(seed)[PARAMETER_NAME]
        if overlay_priority is None
        else _validate_priority(overlay_priority)
    )
    pairs = []
    for pair_index in range(3):
        grid = build_input(seed, pair_index)
        pairs.append({
            "input": deepcopy(grid),
            "output": python_reference(
                grid,
                overlay_priority=priority,
            ),
        })
    return {
        "schema": "arcpuzzles-parametric-overlay-priority-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {PARAMETER_NAME: priority},
        "train": pairs[:2],
        "test": pairs[2:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "arcpuzzles-parametric-overlay-priority-public-v1",
        "train": deepcopy(episode["train"]),
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def racket_program(overlay_priority: str) -> str:
    priority = _validate_priority(overlay_priority)
    role_text = " ".join(_ROLE_ORDERS[priority])
    return f'''#lang racket
(require json)

(define PRIORITY '({role_text}))
(define grid (read-json))
(define H (length grid))
(define W (length (first grid)))
(define HH (quotient H 2))
(define HW (quotient W 2))

(define (cell r c)
  (list-ref (list-ref grid r) c))

(define (role-value role r c)
  (case role
    [(tl) (cell r c)]
    [(tr) (cell r (+ c HW))]
    [(bl) (cell (+ r HH) c)]
    [(br) (cell (+ r HH) (+ c HW))]
    [else (error 'overlay-priority "unknown role ~a" role)]))

(define output
  (for/list ([r (in-range HH)])
    (for/list ([c (in-range HW)])
      (or (for/first ([role PRIORITY]
                      #:when (not (= (role-value role r c) 0)))
            (role-value role r c))
          0))))

(write-json output)
(newline)
'''


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rule_sha256(overlay_priority: str) -> str:
    return sha256_text(racket_program(overlay_priority))


def rule_path(overlay_priority: str) -> Path:
    priority = _validate_priority(overlay_priority)
    return RULE_DIR / f"priority_{priority}.rkt"


def materialize_rules() -> None:
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    for priority in ALLOWED_OVERLAY_PRIORITIES:
        rule_path(priority).write_text(
            racket_program(priority),
            encoding="utf-8",
        )


def run_racket(
    overlay_priority: str,
    grid: list[list[int]],
) -> list[list[int]]:
    priority = _validate_priority(overlay_priority)
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError("racket executable not found; run through review.py run")
    path = rule_path(priority)
    expected = racket_program(priority)
    if not path.is_file() or path.read_text(encoding="utf-8") != expected:
        raise RuntimeError(f"retained Racket source is stale: {path}")
    proc = subprocess.run(
        [executable, str(path)],
        input=json.dumps(grid, separators=(",", ":")) + "\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Racket failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    result = json.loads(proc.stdout)
    if not isinstance(result, list):
        raise RuntimeError(f"Racket returned non-grid JSON: {result!r}")
    return result


def build_evidence(episode_seed: int) -> dict[str, Any]:
    seed = _validate_seed(episode_seed)
    materialize_rules()
    _generator, generator_path, generator_sha = _selected_generator()
    source_root = find_root(__file__)
    settings: dict[str, Any] = {}
    for priority in ALLOWED_OVERLAY_PRIORITIES:
        other = next(
            value
            for value in ALLOWED_OVERLAY_PRIORITIES
            if value != priority
        )
        episode = build_episode(seed, overlay_priority=priority)
        executions = []
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = run_racket(priority, pair["input"])
                alternative = run_racket(other, pair["input"])
                mirror = python_reference(
                    pair["input"],
                    overlay_priority=priority,
                )
                if actual != pair["output"] or actual != mirror:
                    raise AssertionError(
                        "Racket/Python/episode mismatch for "
                        f"{priority} {split}[{pair_index}]"
                    )
                executions.append({
                    "split": split,
                    "pair_index": pair_index,
                    "input": pair["input"],
                    "racket_output": actual,
                    "alternative_priority": other,
                    "alternative_racket_output": alternative,
                    "settings_disagree": actual != alternative,
                })
        settings[priority] = {
            "overlay_priority": priority,
            "roles_high_to_low": list(_ROLE_ORDERS[priority]),
            "is_canonical_default": priority == DEFAULT_OVERLAY_PRIORITY,
            "racket_path": str(rule_path(priority).relative_to(source_root)),
            "racket_text": racket_program(priority),
            "racket_sha256": rule_sha256(priority),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executions": executions,
            "all_pairs_match_racket": True,
            "every_demo_refutes_alternative_setting": all(
                row["settings_disagree"]
                for row in executions
                if row["split"] == "train"
            ),
            "query_also_distinguishes_settings": all(
                row["settings_disagree"]
                for row in executions
                if row["split"] == "test"
            ),
        }
    return {
        "schema": "arcpuzzles-parametric-overlay-priority-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "chosen_parameter": choose_parameters(seed),
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_OVERLAY_PRIORITIES),
            "canonical_default": DEFAULT_OVERLAY_PRIORITY,
            "selection": (
                "ALLOWED_OVERLAY_PRIORITIES[episode_seed % 2], once per episode"
            ),
            "input_constraints": (
                "6x6 production-generator scenes with equal quadrants; each "
                "scene contains forced overlap patterns that distinguish both priorities"
            ),
            "invariant_reasoning": [
                "split the input into four aligned equal quadrants",
                "compare the four cells at each local coordinate",
                "treat zero as transparent",
                "emit one selected nonzero role into the half-sized output",
            ],
        },
        "prototype_source_path": str(Path(__file__).resolve().relative_to(source_root)),
        "prototype_source_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "selected_generator_path": str(generator_path.relative_to(source_root)),
        "selected_generator_sha256": generator_sha,
        "settings": settings,
        "limits": [
            "Bounded evidence for two settings at one seed, not production or training approval.",
            "The selected production generator and canonical Racket authority remain fixed at overlay_priority='tr_bl_br_tl'.",
            "The demonstrations refute the retained opposite setting; undeclared rival priority laws are not exhausted.",
            "Prototype inputs are intentionally fixed at 6x6 to retain compact complete episodes.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    args = parser.parse_args()

    evidence = build_evidence(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for priority, setting in evidence["settings"].items():
            path = args.write_public / f"priority_{priority}_public.json"
            path.write_text(
                json.dumps(
                    setting["public_challenge"],
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

    print(json.dumps({
        "status": evidence["status"],
        "seed": evidence["seed"],
        "chosen_parameter": evidence["chosen_parameter"],
        "settings": {
            priority: {
                "racket_sha256": row["racket_sha256"],
                "all_pairs_match_racket": row["all_pairs_match_racket"],
                "every_demo_refutes_alternative_setting": row[
                    "every_demo_refutes_alternative_setting"
                ],
                "query_also_distinguishes_settings": row[
                    "query_also_distinguishes_settings"
                ],
            }
            for priority, row in evidence["settings"].items()
        },
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

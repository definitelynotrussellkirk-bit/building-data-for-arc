#!/usr/bin/env python3
"""Standalone prototype for a parameterized nearest-neighbor upscale family.

This is deliberately separate from the selected generator and canonical rule.
The bounded rule parameter is ``scale_factor`` in {2, 3}; 2 is the canonical
setting.  A setting is chosen once per episode and shared by all pairs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any


ALLOWED_SCALE_FACTORS = (2, 3)
DEFAULT_SCALE_FACTOR = 2
PROTOTYPE_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"


def _validate_scale_factor(scale_factor: int) -> int:
    if type(scale_factor) is not int or scale_factor not in ALLOWED_SCALE_FACTORS:
        raise ValueError(
            f"scale_factor must be one of {ALLOWED_SCALE_FACTORS}, got {scale_factor!r}"
        )
    return scale_factor


def choose_scale_factor(seed: int) -> int:
    """Choose one hidden setting for an entire episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    return ALLOWED_SCALE_FACTORS[seed % len(ALLOWED_SCALE_FACTORS)]


def python_upscale(grid: list[list[int]], scale_factor: int) -> list[list[int]]:
    """Independent Python mirror used only as an assertion around Racket runs."""
    k = _validate_scale_factor(scale_factor)
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    out: list[list[int]] = []
    for row in grid:
        expanded = [value for value in row for _ in range(k)]
        for _ in range(k):
            out.append(expanded[:])
    return out


def racket_program(scale_factor: int) -> str:
    """Return the exact standalone Racket program for one setting."""
    k = _validate_scale_factor(scale_factor)
    return f'''#lang racket
(require json)

(define SCALE {k})

(define (expand-row row)
  (apply append
         (for/list ([value (in-list row)])
           (make-list SCALE value))))

(define (solve grid)
  (apply append
         (for/list ([row (in-list grid)])
           (define expanded (expand-row row))
           (make-list SCALE expanded))))

(define input-grid (read-json))
(write-json (solve input-grid))
(newline)
'''


def racket_sha256(scale_factor: int) -> str:
    return hashlib.sha256(racket_program(scale_factor).encode("utf-8")).hexdigest()


def rule_path(scale_factor: int) -> Path:
    return RULE_DIR / f"scale_{_validate_scale_factor(scale_factor)}.rkt"


def _episode_inputs(seed: int) -> list[list[list[int]]]:
    rng = random.Random(seed)
    palettes = [tuple(rng.sample(range(1, 10), 2)) for _ in range(3)]
    (a, b), (c, d), (e, f) = palettes
    return [
        [
            [0, a, 0],
            [0, a, b],
            [0, 0, b],
        ],
        [
            [c, 0, 0, 0],
            [c, d, d, 0],
            [0, 0, d, 0],
        ],
        [
            [0, e, 0],
            [e, e, f],
            [0, 0, f],
            [0, 0, 0],
        ],
    ]


def build_episode(seed: int, scale_factor: int | None = None) -> dict[str, Any]:
    """Build two demonstrations and one labelled query for one fixed setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    scale = choose_scale_factor(seed) if scale_factor is None else _validate_scale_factor(scale_factor)
    inputs = _episode_inputs(seed)
    pairs = [
        {"input": copy.deepcopy(grid), "output": python_upscale(grid, scale)}
        for grid in inputs
    ]
    return {
        "schema": "arcpuzzles-parametric-upscale-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {"scale_factor": scale},
        "train": pairs[:2],
        "test": pairs[2:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Public presentation: labelled demos, unlabelled query, no hidden parameter."""
    return {
        "schema": "arcpuzzles-parametric-upscale-public-v1",
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def run_racket(scale_factor: int, grid: list[list[int]]) -> list[list[int]]:
    """Execute the exact retained Racket program on one input grid."""
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError("racket executable not found; run through review.py run or run_with_racket.py")
    path = rule_path(scale_factor)
    expected_text = racket_program(scale_factor)
    if not path.is_file() or path.read_text() != expected_text:
        raise RuntimeError(f"retained Racket source does not match materialized setting: {path}")
    proc = subprocess.run(
        [executable, str(path)],
        input=json.dumps(grid, separators=(",", ":")) + "\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Racket failed ({proc.returncode}): {proc.stderr.strip()}")
    result = json.loads(proc.stdout)
    if not isinstance(result, list):
        raise RuntimeError(f"Racket returned non-grid JSON: {result!r}")
    return result


def build_evidence(seed: int) -> dict[str, Any]:
    """Execute both settings and verify per-episode parameter discrimination."""
    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    settings: dict[str, Any] = {}
    for scale in ALLOWED_SCALE_FACTORS:
        episode = build_episode(seed=seed, scale_factor=scale)
        alternative = next(value for value in ALLOWED_SCALE_FACTORS if value != scale)
        executed_pairs = []
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = run_racket(scale, pair["input"])
                alternative_output = run_racket(alternative, pair["input"])
                python_output = python_upscale(pair["input"], scale)
                if actual != pair["output"] or actual != python_output:
                    raise AssertionError(f"Racket/Python/episode mismatch for scale={scale} {split}[{pair_index}]")
                executed_pairs.append({
                    "split": split,
                    "pair_index": pair_index,
                    "input": pair["input"],
                    "racket_output": actual,
                    "alternative_scale_factor": alternative,
                    "alternative_racket_output": alternative_output,
                    "settings_disagree": actual != alternative_output,
                })
        demo_discriminates = all(item["settings_disagree"] for item in executed_pairs if item["split"] == "train")
        settings[str(scale)] = {
            "scale_factor": scale,
            "is_canonical_default": scale == DEFAULT_SCALE_FACTOR,
            "racket_path": str(rule_path(scale).relative_to(ROOT)),
            "racket_text": racket_program(scale),
            "racket_sha256": racket_sha256(scale),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executed_pairs": executed_pairs,
            "all_pairs_match_racket": True,
            "every_demo_refutes_alternative_setting": demo_discriminates,
        }
    return {
        "schema": "arcpuzzles-parametric-upscale-evidence-v1",
        "status": "prototype",
        "task_id": "0d6d64e90301",
        "seed": seed,
        "parameter": {
            "name": "scale_factor",
            "allowed_values": list(ALLOWED_SCALE_FACTORS),
            "canonical_default": DEFAULT_SCALE_FACTOR,
            "selection": "ALLOWED_SCALE_FACTORS[seed % 2], once per episode",
            "input_constraints": "non-empty rectangular ARC color grids; examples retain sparse connected two-color motifs",
        },
        "prototype_source_sha256": source_sha,
        "settings": settings,
        "limits": [
            "Bounded evidence for scale factors 2 and 3 at one seed, not production approval.",
            "The selected canonical generator and Racket authority remain fixed at scale factor 2.",
            "The two labelled demonstrations distinguish the retained alternative only; undeclared rivals are not exhausted.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    args = parser.parse_args()
    evidence = build_evidence(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for scale, setting in evidence["settings"].items():
            path = args.write_public / f"scale_{scale}_public.json"
            path.write_text(json.dumps(setting["public_challenge"], indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": evidence["status"],
        "seed": evidence["seed"],
        "settings": {
            key: {
                "racket_sha256": value["racket_sha256"],
                "all_pairs_match_racket": value["all_pairs_match_racket"],
                "every_demo_refutes_alternative_setting": value["every_demo_refutes_alternative_setting"],
            }
            for key, value in evidence["settings"].items()
        },
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

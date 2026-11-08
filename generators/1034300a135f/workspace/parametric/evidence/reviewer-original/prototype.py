#!/usr/bin/env python3
"""Prototype an episode-level marker-order parameter for ARC task 1034300a135f.

Production remains fixed to ``marker_order='near_to_far'``.  The proposed
alternative reverses only the ordering of input marker distance groups; all
other semantics stay fixed: nonzero modal background, zero as a lawful marker,
row-major stability inside equal-distance groups, and ranked output rings.
One setting is selected from the episode seed and shared by two demonstrations
and one hidden-answer query.  Retained evidence executes exact standalone
Racket programs for both settings.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


TASK_ID = "1034300a135f"
PARAMETER_NAME = "marker_order"
ALLOWED_MARKER_ORDERS = ("near_to_far", "far_to_near")
DEFAULT_MARKER_ORDER = "near_to_far"
PROTOTYPE_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"

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
    module, path, digest = load_selected_generator(
        TASK_ID,
        root=find_root(__file__),
    )
    return module, path, digest


def _validate_episode_seed(value: int) -> int:
    if type(value) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if value < 0:
        raise ValueError("episode seed must be nonnegative")
    return value


def _validate_marker_order(value: str) -> str:
    if type(value) is not str or value not in ALLOWED_MARKER_ORDERS:
        raise ValueError(
            "marker_order must be one of "
            f"{ALLOWED_MARKER_ORDERS}, got {value!r}"
        )
    return value


def choose_parameters(episode_seed: int) -> dict[str, str]:
    seed = _validate_episode_seed(episode_seed)
    return {
        PARAMETER_NAME: ALLOWED_MARKER_ORDERS[
            seed % len(ALLOWED_MARKER_ORDERS)
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
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be literal ARC integers 0..9")
    return [row[:] for row in grid]


def _edge_distance(row: int, col: int, height: int, width: int) -> int:
    return min(row, col, height - 1 - row, width - 1 - col)


def python_reference(
    grid: list[list[int]],
    *,
    marker_order: str,
) -> list[list[int]]:
    """Independent reference for one episode-level marker ordering."""
    order = _validate_marker_order(marker_order)
    source = _validate_grid(grid)
    height, width = len(source), len(source[0])
    counts = Counter(value for row in source for value in row if value != 0)
    if not counts:
        raise ValueError("at least one nonzero color is required")
    maximum = max(counts.values())
    modes = [color for color, count in counts.items() if count == maximum]
    if len(modes) != 1:
        raise ValueError("nonzero background mode must be unique")
    background = modes[0]
    markers = [
        (
            _edge_distance(row, col, height, width),
            row,
            col,
            source[row][col],
        )
        for row in range(height)
        for col in range(width)
        if source[row][col] != background
    ]
    distance_sign = 1 if order == "near_to_far" else -1
    ordered = sorted(markers, key=lambda marker: distance_sign * marker[0])
    colors = [marker[3] for marker in ordered]
    return [
        [
            colors[distance] if distance < len(colors) else background
            for col in range(width)
            for distance in [_edge_distance(row, col, height, width)]
        ]
        for row in range(height)
    ]


def _derived_seed(episode_seed: int, pair_index: int) -> int:
    digest = hashlib.sha256(
        f"1034300a135f-parametric-marker-order:v1:{episode_seed}:{pair_index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def build_input(episode_seed: int, pair_index: int) -> list[list[int]]:
    seed = _validate_episode_seed(episode_seed)
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer (not bool)")
    generator, _path, _digest = _selected_generator()
    grid = generator.generate(
        _derived_seed(seed, pair_index),
        seed * 101 + pair_index,
        difficulty="medium",
        scene_profile="teaching_combined",
    )
    canonical = python_reference(grid, marker_order=DEFAULT_MARKER_ORDER)
    alternative = python_reference(grid, marker_order="far_to_near")
    if canonical != generator.rule_mirror(grid):
        raise AssertionError("prototype default diverges from selected canonical rule")
    if canonical == alternative:
        raise AssertionError("prototype input does not distinguish marker orders")
    return grid


def build_episode(
    episode_seed: int,
    *,
    marker_order: str | None = None,
) -> dict[str, Any]:
    seed = _validate_episode_seed(episode_seed)
    order = (
        choose_parameters(seed)[PARAMETER_NAME]
        if marker_order is None
        else _validate_marker_order(marker_order)
    )
    pairs = []
    for pair_index in range(3):
        grid = build_input(seed, pair_index)
        pairs.append({
            "input": deepcopy(grid),
            "output": python_reference(grid, marker_order=order),
        })
    return {
        "schema": "arcpuzzles-parametric-marker-order-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {PARAMETER_NAME: order},
        "train": pairs[:2],
        "test": pairs[2:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "arcpuzzles-parametric-marker-order-public-v1",
        "train": deepcopy(episode["train"]),
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def racket_program(marker_order: str) -> str:
    order = _validate_marker_order(marker_order)
    return f'''#lang racket
(require json racket/list)

(define MARKER-ORDER '{order})
(define input-grid (read-json))
(define H (length input-grid))
(define W (length (first input-grid)))
(define (cell r c) (list-ref (list-ref input-grid r) c))
(define (edge-distance r c)
  (min r c (- H 1 r) (- W 1 c)))

(define counts (make-hash))
(for* ([r (in-range H)] [c (in-range W)])
  (define value (cell r c))
  (unless (= value 0)
    (hash-update! counts value add1 0)))
(define entries (hash->list counts))
(when (null? entries)
  (error 'marker-order "at least one nonzero color is required"))
(define best-entry
  (for/fold ([best (first entries)]) ([entry (rest entries)])
    (if (> (cdr entry) (cdr best)) entry best)))
(define background (car best-entry))

(define markers
  (for*/list ([r (in-range H)] [c (in-range W)]
              #:when (not (= (cell r c) background)))
    (list (edge-distance r c) r c (cell r c))))
(define (distance-before? left right)
  (if (eq? MARKER-ORDER 'near_to_far)
      (< (first left) (first right))
      (> (first left) (first right))))
(define ordered (sort markers distance-before?))
(define colors (map fourth ordered))
(define N (length colors))
(define output
  (for/list ([r (in-range H)])
    (for/list ([c (in-range W)])
      (define distance (edge-distance r c))
      (if (< distance N) (list-ref colors distance) background))))
(write-json output)
(newline)
'''


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rule_sha256(marker_order: str) -> str:
    return sha256_text(racket_program(marker_order))


def rule_path(marker_order: str) -> Path:
    return RULE_DIR / f"marker_{_validate_marker_order(marker_order)}.rkt"


def materialize_rules() -> None:
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    for marker_order in ALLOWED_MARKER_ORDERS:
        rule_path(marker_order).write_text(
            racket_program(marker_order),
            encoding="utf-8",
        )


def run_racket(marker_order: str, grid: list[list[int]]) -> list[list[int]]:
    order = _validate_marker_order(marker_order)
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError("racket executable not found; run through review.py run")
    path = rule_path(order)
    expected = racket_program(order)
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
    seed = _validate_episode_seed(episode_seed)
    materialize_rules()
    generator, generator_path, generator_sha = _selected_generator()
    settings: dict[str, Any] = {}
    for marker_order in ALLOWED_MARKER_ORDERS:
        other = next(
            value for value in ALLOWED_MARKER_ORDERS if value != marker_order
        )
        episode = build_episode(seed, marker_order=marker_order)
        executions = []
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = run_racket(marker_order, pair["input"])
                alternative = run_racket(other, pair["input"])
                mirror = python_reference(
                    pair["input"],
                    marker_order=marker_order,
                )
                if actual != pair["output"] or actual != mirror:
                    raise AssertionError(
                        "Racket/Python/episode mismatch for "
                        f"{marker_order} {split}[{pair_index}]"
                    )
                if (
                    marker_order == DEFAULT_MARKER_ORDER
                    and actual != generator.rule_mirror(pair["input"])
                ):
                    raise AssertionError(
                        "canonical prototype setting diverges from production rule"
                    )
                executions.append({
                    "split": split,
                    "pair_index": pair_index,
                    "input": pair["input"],
                    "racket_output": actual,
                    "alternative_marker_order": other,
                    "alternative_racket_output": alternative,
                    "settings_disagree": actual != alternative,
                })
        settings[marker_order] = {
            "marker_order": marker_order,
            "is_canonical_default": marker_order == DEFAULT_MARKER_ORDER,
            "racket_path": str(rule_path(marker_order).relative_to(find_root(__file__))),
            "racket_text": racket_program(marker_order),
            "racket_sha256": rule_sha256(marker_order),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executions": executions,
            "all_pairs_match_racket": True,
            "canonical_default_matches_production": (
                marker_order != DEFAULT_MARKER_ORDER
                or all(
                    row["racket_output"] == generator.rule_mirror(row["input"])
                    for row in executions
                )
            ),
            "every_demo_refutes_alternative_setting": all(
                row["settings_disagree"]
                for row in executions
                if row["split"] == "train"
            ),
        }
    return {
        "schema": "arcpuzzles-parametric-marker-order-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_MARKER_ORDERS),
            "canonical_default": DEFAULT_MARKER_ORDER,
            "selection": "ALLOWED_MARKER_ORDERS[episode_seed % 2], once per episode",
        },
        "prototype_source_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "selected_generator_path": str(generator_path),
        "selected_generator_sha256": generator_sha,
        "settings": settings,
        "limits": [
            "Bounded evidence for two marker-order settings, not production approval.",
            "Production and the canonical Racket authority remain fixed to near_to_far.",
            "The demonstrations refute the retained opposite setting; they do not exhaust undeclared rival rules.",
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
        for marker_order, setting in evidence["settings"].items():
            path = args.write_public / f"marker_{marker_order}_public.json"
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
        "settings": {
            marker_order: {
                "racket_sha256": row["racket_sha256"],
                "all_pairs_match_racket": row["all_pairs_match_racket"],
                "canonical_default_matches_production": row[
                    "canonical_default_matches_production"
                ],
                "every_demo_refutes_alternative_setting": row[
                    "every_demo_refutes_alternative_setting"
                ],
            }
            for marker_order, row in evidence["settings"].items()
        },
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded prototype: whether color-5 stops beams or beams pass through it.

This module is deliberately separate from the selected canonical generator.
``blocker_mode='stop'`` is the canonical/default setting. ``'pass'`` is a
proposed alternative. A mode is chosen once from the episode seed and shared by
all demonstrations and the query. Labels used for retained evidence are
executed by the exact materialized Racket program for that mode.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ALLOWED_BLOCKER_MODES = ("stop", "pass")
DEFAULT_BLOCKER_MODE = "stop"
PROTOTYPE_VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"
WORKSPACE = ROOT.parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
from reference_probe import load_generator  # noqa: E402


def _validate_mode(mode: str) -> str:
    if type(mode) is not str or mode not in ALLOWED_BLOCKER_MODES:
        raise ValueError(f"blocker_mode must be one of {ALLOWED_BLOCKER_MODES}, got {mode!r}")
    return mode


def choose_blocker_mode(seed: int) -> str:
    """Choose one hidden rule setting for an entire episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return ALLOWED_BLOCKER_MODES[seed % len(ALLOWED_BLOCKER_MODES)]


def _marker(grid: list[list[int]]) -> tuple[int, int, int]:
    h, w = len(grid), len(grid[0])
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    hits = [(r, c, grid[r][c]) for r, c in corners if grid[r][c] in {1, 2, 3, 4}]
    if len(hits) != 1:
        raise ValueError(f"expected one direction marker, found {hits}")
    return hits[0]


def python_beam(grid: list[list[int]], blocker_mode: str) -> list[list[int]]:
    """Independent Python mirror used only to cross-check Racket execution."""
    mode = _validate_mode(blocker_mode)
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    h, w = len(grid), width
    mr, mc, marker_color = _marker(grid)
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[marker_color]
    blockers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    out = deepcopy(grid)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 5) or (r, c) == (mr, mc):
                continue
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                if mode == "stop" and (rr, cc) in blockers:
                    break
                out[rr][cc] = value
                rr += dr
                cc += dc
    return out


def racket_program(blocker_mode: str) -> str:
    """Materialize one exact standalone Racket program for the setting."""
    mode = _validate_mode(blocker_mode)
    flag = "#t" if mode == "stop" else "#f"
    return f'''#lang racket
(require json)

(define STOP-AT-BLOCKER? {flag})

(define input-grid (read-json))
(define H (length input-grid))
(define W (length (first input-grid)))
(define source (list->vector (map list->vector input-grid)))
(define out (list->vector (for/list ([row (in-list input-grid)]) (list->vector row))))

(define (cell grid r c) (vector-ref (vector-ref grid r) c))
(define (set-cell! grid r c value) (vector-set! (vector-ref grid r) c value))
(define (inside? r c) (and (<= 0 r) (< r H) (<= 0 c) (< c W)))

(define corners
  (list (list 0 0)
        (list 0 (- W 1))
        (list (- H 1) 0)
        (list (- H 1) (- W 1))))
(define marker
  (first
   (filter (lambda (point)
             (member (cell source (first point) (second point)) '(1 2 3 4)))
           corners)))
(define mr (first marker))
(define mc (second marker))
(define marker-color (cell source mr mc))
(define direction
  (cond [(= marker-color 1) '(-1 0)]
        [(= marker-color 2) '(0 1)]
        [(= marker-color 3) '(1 0)]
        [else '(0 -1)]))
(define dr (first direction))
(define dc (second direction))

(for* ([r (in-range H)] [c (in-range W)])
  (define value (cell source r c))
  (unless (or (= value 0) (= value 5) (and (= r mr) (= c mc)))
    (let loop ([rr (+ r dr)] [cc (+ c dc)])
      (when (inside? rr cc)
        (unless (and STOP-AT-BLOCKER? (= (cell source rr cc) 5))
          (set-cell! out rr cc value)
          (loop (+ rr dr) (+ cc dc)))))))

(write-json (for/list ([row (in-vector out)]) (vector->list row)))
(newline)
'''


def rule_path(blocker_mode: str) -> Path:
    return RULE_DIR / f"blocker_{_validate_mode(blocker_mode)}.rkt"


def materialize_rules() -> None:
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    for mode in ALLOWED_BLOCKER_MODES:
        rule_path(mode).write_text(racket_program(mode), encoding="utf-8")


def rule_sha256(blocker_mode: str) -> str:
    return hashlib.sha256(racket_program(blocker_mode).encode("utf-8")).hexdigest()


def _episode_inputs(seed: int) -> list[list[list[int]]]:
    generator = load_generator()
    # Production inputs are guaranteed to contain both active and irrelevant
    # blockers, so each demonstration distinguishes these two rule settings.
    return [
        generator.generate(seed, 100 + index, difficulty="medium")
        for index in range(3)
    ]


def build_episode(seed: int, blocker_mode: str | None = None) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    mode = choose_blocker_mode(seed) if blocker_mode is None else _validate_mode(blocker_mode)
    pairs = [
        {"input": deepcopy(grid), "output": python_beam(grid, mode)}
        for grid in _episode_inputs(seed)
    ]
    return {
        "schema": "arcpuzzles-parametric-blocker-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {"blocker_mode": mode},
        "train": pairs[:2],
        "test": pairs[2:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Omit hidden parameter and query answer from the public presentation."""
    return {
        "schema": "arcpuzzles-parametric-blocker-public-v1",
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def run_racket(blocker_mode: str, grid: list[list[int]]) -> list[list[int]]:
    mode = _validate_mode(blocker_mode)
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError("racket executable not found; run through review.py run")
    path = rule_path(mode)
    expected = racket_program(mode)
    if not path.is_file() or path.read_text(encoding="utf-8") != expected:
        raise RuntimeError(f"retained Racket source does not match materialized mode: {path}")
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
    materialize_rules()
    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    generator_path = WORKSPACE.parent / "generator.py"
    settings: dict[str, Any] = {}
    for mode in ALLOWED_BLOCKER_MODES:
        other = next(candidate for candidate in ALLOWED_BLOCKER_MODES if candidate != mode)
        episode = build_episode(seed, blocker_mode=mode)
        executions = []
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = run_racket(mode, pair["input"])
                alternative = run_racket(other, pair["input"])
                mirror = python_beam(pair["input"], mode)
                if actual != pair["output"] or actual != mirror:
                    raise AssertionError(f"Racket/Python/episode mismatch for {mode} {split}[{pair_index}]")
                executions.append({
                    "split": split,
                    "pair_index": pair_index,
                    "input": pair["input"],
                    "racket_output": actual,
                    "alternative_mode": other,
                    "alternative_racket_output": alternative,
                    "settings_disagree": actual != alternative,
                })
        demo_rows = [row for row in executions if row["split"] == "train"]
        settings[mode] = {
            "blocker_mode": mode,
            "is_canonical_default": mode == DEFAULT_BLOCKER_MODE,
            "racket_path": str(rule_path(mode).relative_to(ROOT)),
            "racket_text": racket_program(mode),
            "racket_sha256": rule_sha256(mode),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executions": executions,
            "all_pairs_match_racket": True,
            "every_demo_refutes_alternative_setting": all(row["settings_disagree"] for row in demo_rows),
        }
    return {
        "schema": "arcpuzzles-parametric-blocker-evidence-v1",
        "status": "prototype",
        "task_id": "b91a3b0baac4",
        "seed": seed,
        "parameter": {
            "name": "blocker_mode",
            "allowed_values": list(ALLOWED_BLOCKER_MODES),
            "canonical_default": DEFAULT_BLOCKER_MODE,
            "selection": "ALLOWED_BLOCKER_MODES[seed % 2], once per episode",
            "input_constraints": "unique corner marker; at least one active color-5 blocker; production prototype inputs also retain an irrelevant blocker",
        },
        "prototype_source_sha256": source_sha,
        "selected_generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "settings": settings,
        "limits": [
            "Bounded evidence for two modes at one seed, not production approval.",
            "The selected generator and canonical Racket authority remain fixed at blocker_mode='stop'.",
            "The two demonstrations refute only the retained alternative; undeclared rival rules are not exhausted.",
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
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for mode, setting in evidence["settings"].items():
            (args.write_public / f"blocker_{mode}_public.json").write_text(
                json.dumps(setting["public_challenge"], indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    print(json.dumps({
        "status": evidence["status"],
        "seed": evidence["seed"],
        "settings": {
            mode: {
                "racket_sha256": row["racket_sha256"],
                "all_pairs_match_racket": row["all_pairs_match_racket"],
                "every_demo_refutes_alternative_setting": row["every_demo_refutes_alternative_setting"],
            }
            for mode, row in evidence["settings"].items()
        },
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

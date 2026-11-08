"""Proposed episode-level bridge-scope parameter for ARC family 79a30e61d332.

This is a task-local authoring prototype, not the selected production generator.
The canonical setting (``all_pairs``) preserves the approved rule exactly.  The
alternative (``seed_only``) keeps exact-mask key detection and key recoloring,
but recolors only bridge tiles lying between the distinguished color-8 seed and
another aligned key.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Iterable

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(ROOT / "src"))

from reference_probe import (  # noqa: E402
    canonical_record,
    key_positions,
    load_generator,
    seed_position,
    tile_positions,
)

TASK_ID = "79a30e61d332"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "bridge_scope"
SCOPES = ("all_pairs", "seed_only")
DEFAULT_SCOPE = "all_pairs"


def _validate_scope(scope: str) -> str:
    if type(scope) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if scope not in SCOPES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {SCOPES}")
    return scope


def choose_scope(seed: int) -> str:
    """Choose one hidden rule for an entire episode from its deterministic seed."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    return SCOPES[seed % len(SCOPES)]


def other_scope(scope: str) -> str:
    scope = _validate_scope(scope)
    return "seed_only" if scope == "all_pairs" else "all_pairs"


def _between(value: int, left: int, right: int) -> bool:
    return min(left, right) < value < max(left, right)


def _bridge_positions_all_pairs(keys: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    keys = set(keys)
    result: set[tuple[int, int]] = set()
    ordered = sorted(keys)
    for index, first in enumerate(ordered):
        for second in ordered[index + 1 :]:
            if first[0] == second[0]:
                result.update(
                    (first[0], col)
                    for col in range(min(first[1], second[1]) + 1, max(first[1], second[1]))
                )
            if first[1] == second[1]:
                result.update(
                    (row, first[1])
                    for row in range(min(first[0], second[0]) + 1, max(first[0], second[0]))
                )
    return result - keys


def _bridge_positions_seed_only(
    keys: Iterable[tuple[int, int]], seed: tuple[int, int]
) -> set[tuple[int, int]]:
    keys = set(keys)
    result: set[tuple[int, int]] = set()
    for other in keys - {seed}:
        if other[0] == seed[0]:
            result.update(
                (seed[0], col)
                for col in range(min(seed[1], other[1]) + 1, max(seed[1], other[1]))
            )
        if other[1] == seed[1]:
            result.update(
                (row, seed[1])
                for row in range(min(seed[0], other[0]) + 1, max(seed[0], other[0]))
            )
    return result - keys


def python_output(grid, scope: str):
    """Independent Python mirror used only to check retained Racket labels."""
    scope = _validate_scope(scope)
    out = deepcopy(grid)
    keys = set(key_positions(grid))
    seed = seed_position(grid)
    bridges = (
        _bridge_positions_all_pairs(keys)
        if scope == "all_pairs"
        else _bridge_positions_seed_only(keys, seed)
    )
    for tile_row, tile_col in tile_positions():
        if (tile_row, tile_col) in keys:
            color = 8
        elif (tile_row, tile_col) in bridges:
            color = 7
        else:
            continue
        for delta_row in range(3):
            for delta_col in range(3):
                row = 1 + 4 * tile_row + delta_row
                col = 1 + 4 * tile_col + delta_col
                if out[row][col] != 0:
                    out[row][col] = color
    return out


_SEED_ONLY_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define tile-rows (quotient (+ h 1) 4))
             (define tile-cols (quotient (+ w 1) 4))
             (define tile-pos
               (for*/list ((tr (range 0 tile-rows)) (tc (range 0 tile-cols)))
                 (list tr tc)))
             (define (tile-mask tr tc)
               (for*/list ((dr (range 0 3)) (dc (range 0 3)))
                 (if (zero? (at g (+ 1 (* 4 tr) dr) (+ 1 (* 4 tc) dc))) 0 1)))
             (define (tile-has-color? tr tc color)
               (for*/or ((dr (range 0 3)) (dc (range 0 3)))
                        (= (at g (+ 1 (* 4 tr) dr) (+ 1 (* 4 tc) dc)) color)))
             (define seed
               (find-first (lambda (p) (tile-has-color? (first p) (second p) 8))
                           tile-pos))
             (define key-mask (tile-mask (first seed) (second seed)))
             (define key-tiles
               (filter (lambda (p) (equal? (tile-mask (first p) (second p)) key-mask))
                       tile-pos))
             (define (key-tile? tr tc)
               (for/or ((p key-tiles)) (and (= (first p) tr) (= (second p) tc))))
             (define (between? x a b) (or (and (< a x) (< x b)) (and (< b x) (< x a))))
             (define (bridge-tile? tr tc)
               (for/or ((other key-tiles))
                       (or
                         (and
                           (= (first seed) tr)
                           (= (first other) tr)
                           (between? tc (second seed) (second other)))
                         (and
                           (= (second seed) tc)
                           (= (second other) tc)
                           (between? tr (first seed) (first other))))))
             (cellmap g
                      (r c v)
                      (let ((v v))
                        (if (or (zero? v) (zero? (modulo r 4)) (zero? (modulo c 4)))
                            v
                            (let ((tr (quotient r 4))
                                  (tc (quotient c 4)))
                              (cond
                                ((key-tile? tr tc) 8)
                                ((bridge-tile? tr tc) 7)
                                (else v))))))))))"""


def racket_program(scope: str) -> str:
    """Materialize the exact Racket authority proposed for one parameter setting."""
    scope = _validate_scope(scope)
    if scope == "all_pairs":
        return canonical_record()["program_solution"]
    return _SEED_ONLY_PROGRAM


def racket_outputs(program: str, grids):
    """Execute an exact Racket program through the packet's pinned runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parametric-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                "Racket worker failed: " + result["stderr"] + " " + result["stdout"]
            )
        return json.loads(result["stdout"])


def build_episode(
    seed: int,
    *,
    scope: str | None = None,
    difficulty: str = "medium",
    n_train: int = 3,
    n_test: int = 1,
):
    """Build one complete episode and label every pair with its chosen Racket rule."""
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if type(n_train) is not int or type(n_test) is not int or n_train < 1 or n_test < 1:
        raise ValueError("n_train and n_test must be positive integers")
    chosen = choose_scope(seed) if scope is None else _validate_scope(scope)
    generator = load_generator()
    grids = [
        generator.generate(seed, sample_index, difficulty=difficulty, n_keys=5)
        for sample_index in range(n_train + n_test)
    ]
    program = racket_program(chosen)
    labels = racket_outputs(program, grids)
    mirrors = [python_output(grid, chosen) for grid in grids]
    if labels != mirrors:
        raise AssertionError(f"Racket/Python parity failed for {chosen}")
    rival = other_scope(chosen)
    if not all(label != python_output(grid, rival) for grid, label in zip(grids[:n_train], labels[:n_train])):
        raise AssertionError("demonstrations do not identify bridge_scope")
    pairs = [{"input": grid, "output": output} for grid, output in zip(grids, labels)]
    return {
        "schema": "79a30e61d332-parametric-episode-v1",
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "meta": {
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "episode_seed": seed,
            "difficulty": difficulty,
            "bridge_scope": chosen,
            "allowed_bridge_scopes": list(SCOPES),
            "canonical_default": DEFAULT_SCOPE,
            "racket_verified": True,
        },
    }


def public_challenge(episode):
    """Remove hidden rule metadata, reference code, and query answers."""
    return {
        "schema": "79a30e61d332-parametric-public-v1",
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _grid_hash(grid) -> str:
    return _sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def write_evidence_bundle(out_dir: Path | str, *, seeds: dict[str, int] | None = None):
    """Materialize source-bound episodes, exact programs, public files, and hashes."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seeds = dict(seeds or {"all_pairs": 20, "seed_only": 21})
    if set(seeds) != set(SCOPES):
        raise ValueError(f"seeds must provide exactly {SCOPES}")

    manifest = {
        "schema": "79a30e61d332-parametric-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(SCOPES),
            "canonical_default": DEFAULT_SCOPE,
            "chosen_once_per_episode": True,
        },
        "prototype_source_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        "generator_source_sha256": _sha256_bytes(
            (ROOT / f"generators/{TASK_ID}/generator.py").read_bytes()
        ),
        "settings": {},
        "limitations": [
            "This is a proposed task-local prototype, not a production or approval change.",
            "Evidence covers two retained seeds and the declared alternative scope only.",
            "The input sampler is the canonical generator and intentionally guarantees a non-seed bridge witness.",
        ],
    }

    for scope in SCOPES:
        episode = build_episode(seeds[scope], scope=scope)
        public = public_challenge(episode)
        setting_dir = out / scope
        setting_dir.mkdir(parents=True, exist_ok=True)
        program_path = setting_dir / "program.rkt"
        episode_path = setting_dir / "episode.json"
        public_path = setting_dir / "public_challenge.json"
        program_path.write_text(episode["program"], encoding="utf-8")
        episode_path.write_text(json.dumps(episode, indent=2) + "\n", encoding="utf-8")
        public_path.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")

        rival = other_scope(scope)
        demo_diffs = [
            sum(
                left != right
                for left_row, right_row in zip(pair["output"], python_output(pair["input"], rival))
                for left, right in zip(left_row, right_row)
            )
            for pair in episode["train"]
        ]
        manifest["settings"][scope] = {
            "bridge_scope": scope,
            "episode_seed": seeds[scope],
            "racket_verified": True,
            "program_sha256": _sha256_bytes(episode["program"].encode()),
            "program_path": str(program_path.relative_to(out)),
            "episode_path": str(episode_path.relative_to(out)),
            "public_challenge_path": str(public_path.relative_to(out)),
            "demonstrations": len(episode["train"]),
            "queries": len(episode["test"]),
            "demonstrations_refute_other_scope": all(count > 0 for count in demo_diffs),
            "demo_output_diff_cell_counts": demo_diffs,
            "input_hashes": [
                _grid_hash(pair["input"]) for pair in episode["train"] + episode["test"]
            ],
            "output_hashes": [
                _grid_hash(pair["output"]) for pair in episode["train"] + episode["test"]
            ],
        }

    manifest_path = out / "evidence.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--all-pairs-seed", type=int, default=20)
    parser.add_argument("--seed-only-seed", type=int, default=21)
    args = parser.parse_args(argv)
    manifest = write_evidence_bundle(
        args.out,
        seeds={"all_pairs": args.all_pairs_seed, "seed_only": args.seed_only_seed},
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

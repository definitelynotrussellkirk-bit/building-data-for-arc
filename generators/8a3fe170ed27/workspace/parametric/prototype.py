#!/usr/bin/env python3
"""Prototype-only parameterized row-wave family for task 8a3fe170ed27.

The selected production generator and canonical rule remain unchanged.  This
prototype varies one episode-level rule parameter, ``wave_orientation``:

* ``left_first`` (canonical/default): cycle ``(0, -1, 0, +1)``
* ``right_first`` (proposed): cycle ``(0, +1, 0, -1)``

Both settings keep the original reasoning structure: find the last nonempty row,
measure every occupied row's distance above it, translate the entire row by the
four-step cycle, preserve holes, and clip cells that leave the canvas.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "8a3fe170ed27"
ALLOWED_ORIENTATIONS = ("left_first", "right_first")
DEFAULT_ORIENTATION = "left_first"
PROTOTYPE_VERSION = "1.0.0"
EXAMPLES_NEEDED = 4
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(payload)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_orientation(wave_orientation: str) -> str:
    if type(wave_orientation) is not str or wave_orientation not in ALLOWED_ORIENTATIONS:
        raise ValueError(
            "wave_orientation must be one of "
            f"{ALLOWED_ORIENTATIONS}, got {wave_orientation!r}"
        )
    return wave_orientation


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if type(grid) is not list or not grid:
        raise ValueError("grid must be a nonempty rectangular list")
    if any(type(row) is not list or not row for row in grid):
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be native integer ARC colors 0..9")
    return len(grid), width


def choose_orientation(seed: int) -> str:
    """Choose one hidden orientation for an entire episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    return ALLOWED_ORIENTATIONS[seed % len(ALLOWED_ORIENTATIONS)]


def _first_shift(wave_orientation: str) -> int:
    orientation = _validate_orientation(wave_orientation)
    return -1 if orientation == "left_first" else 1


def python_row_wave(
    grid: list[list[int]], wave_orientation: str
) -> list[list[int]]:
    """Independent Python mirror used only to check retained Racket outputs."""
    _validate_grid(grid)
    first_shift = _first_shift(wave_orientation)
    cycle = (0, first_shift, 0, -first_shift)
    active_rows = [row_index for row_index, row in enumerate(grid) if any(row)]
    if not active_rows:
        return [row[:] for row in grid]

    anchor = active_rows[-1]
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in grid]
    for row_index, row in enumerate(grid):
        if row_index not in active_rows:
            continue
        shift = cycle[(anchor - row_index) % len(cycle)]
        for column, value in enumerate(row):
            if value == 0:
                continue
            destination = column + shift
            if 0 <= destination < width:
                output[row_index][destination] = value
    return output


def racket_program(wave_orientation: str) -> str:
    """Return the exact standalone Racket program for one parameter setting."""
    first_shift = _first_shift(wave_orientation)
    return f'''#lang racket
(require json racket/list)

(define FIRST-SHIFT {first_shift})
(define CYCLE (list 0 FIRST-SHIFT 0 (- FIRST-SHIFT)))

(define (active-row? row)
  (for/or ([value (in-list row)])
    (not (= value 0))))

(define (shift-row row dc)
  (define width (length row))
  (for/list ([destination (in-range width)])
    (define source (- destination dc))
    (if (and (<= 0 source) (< source width))
        (list-ref row source)
        0)))

(define (solve grid)
  (define active-rows
    (for/list ([row (in-list grid)]
               [row-index (in-naturals)]
               #:when (active-row? row))
      row-index))
  (if (null? active-rows)
      grid
      (let ([anchor (last active-rows)])
        (for/list ([row (in-list grid)]
                   [row-index (in-naturals)])
          (if (active-row? row)
              (shift-row row
                         (list-ref CYCLE
                                   (modulo (- anchor row-index) 4)))
              row)))))

(define input-grid (read-json))
(write-json (solve input-grid))
(newline)
'''


def racket_sha256(wave_orientation: str) -> str:
    return _sha256_bytes(racket_program(wave_orientation).encode("utf-8"))


def rule_path(wave_orientation: str) -> Path:
    orientation = _validate_orientation(wave_orientation)
    return RULE_DIR / f"{orientation}.rkt"


def _load_generator():
    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    return root, generator, source, digest


def build_episode(
    seed: int, wave_orientation: str | None = None
) -> dict[str, Any]:
    """Build four demonstrations and one labelled query for one fixed setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    orientation = (
        choose_orientation(seed)
        if wave_orientation is None
        else _validate_orientation(wave_orientation)
    )
    _, generator, source, generator_sha256 = _load_generator()
    pairs = []
    for sample_index in range(EXAMPLES_NEEDED + 1):
        grid = generator.generate(seed, sample_index)
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(
                f"selected generator rejected its own seed={seed} index={sample_index}: {errors}"
            )
        pairs.append(
            {
                "sample_index": sample_index,
                "input": copy.deepcopy(grid),
                "output": python_row_wave(grid, orientation),
            }
        )
    return {
        "schema": "arcpuzzles-parametric-row-wave-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"wave_orientation": orientation},
        "input_source": {
            "generator_path": str(source),
            "generator_sha256": generator_sha256,
            "sample_indices": list(range(EXAMPLES_NEEDED + 1)),
        },
        "train": pairs[:EXAMPLES_NEEDED],
        "test": pairs[EXAMPLES_NEEDED:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return labelled demonstrations and an unlabelled query with no parameter."""
    return {
        "schema": "arcpuzzles-parametric-row-wave-public-v1",
        "task_family": TASK_ID,
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def run_racket(
    wave_orientation: str, grid: list[list[int]], *, timeout: float = 30.0
) -> list[list[int]]:
    """Execute the exact retained standalone Racket program on one grid."""
    orientation = _validate_orientation(wave_orientation)
    _validate_grid(grid)
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError(
            "racket executable not found; run through review.py run or run_with_racket.py"
        )
    path = rule_path(orientation)
    expected_text = racket_program(orientation)
    if not path.is_file() or path.read_text(encoding="utf-8") != expected_text:
        raise RuntimeError(
            f"retained Racket source does not match materialized setting: {path}"
        )
    process = subprocess.run(
        [executable, str(path)],
        input=json.dumps(grid, separators=(",", ":")) + "\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Racket failed ({process.returncode}): {process.stderr.strip()}"
        )
    result = json.loads(process.stdout)
    _validate_grid(result)
    return result


def _alternative(wave_orientation: str) -> str:
    orientation = _validate_orientation(wave_orientation)
    return next(value for value in ALLOWED_ORIENTATIONS if value != orientation)


def build_evidence(seed: int) -> dict[str, Any]:
    """Execute both settings and verify canonical/default and lesson evidence."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    root, _, generator_source, generator_sha256 = _load_generator()
    source_sha256 = _sha256_path(Path(__file__))

    canonical_checks = []
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    for pair_index, pair in enumerate(canonical):
        actual = run_racket(DEFAULT_ORIENTATION, pair["input"])
        python_output = python_row_wave(pair["input"], DEFAULT_ORIENTATION)
        matches = actual == pair["output"] == python_output
        canonical_checks.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": _grid_sha256(pair["input"]),
                "expected_output_sha256": _grid_sha256(pair["output"]),
                "racket_output_sha256": _grid_sha256(actual),
                "matches": matches,
            }
        )
        if not matches:
            raise AssertionError(f"canonical default mismatch at canonical pair {pair_index}")

    settings: dict[str, Any] = {}
    first_witness: dict[str, Any] | None = None
    for orientation in ALLOWED_ORIENTATIONS:
        alternative = _alternative(orientation)
        episode = build_episode(seed=seed, wave_orientation=orientation)
        executed_pairs = []
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = run_racket(orientation, pair["input"])
                alternative_output = run_racket(alternative, pair["input"])
                python_output = python_row_wave(pair["input"], orientation)
                if actual != pair["output"] or actual != python_output:
                    raise AssertionError(
                        f"Racket/Python/episode mismatch for {orientation} "
                        f"{split}[{pair_index}]"
                    )
                differs = actual != alternative_output
                record = {
                    "split": split,
                    "pair_index": pair_index,
                    "sample_index": pair["sample_index"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "racket_output_sha256": _grid_sha256(actual),
                    "alternative_orientation": alternative,
                    "alternative_output_sha256": _grid_sha256(alternative_output),
                    "settings_disagree": differs,
                }
                executed_pairs.append(record)
                if differs and first_witness is None:
                    first_witness = {
                        "input": copy.deepcopy(pair["input"]),
                        orientation: actual,
                        alternative: alternative_output,
                        "input_sha256": record["input_sha256"],
                    }
        demos = [record for record in executed_pairs if record["split"] == "train"]
        if not demos or not all(record["settings_disagree"] for record in demos):
            raise AssertionError(
                f"every demonstration must refute the alternative setting: {orientation}"
            )
        settings[orientation] = {
            "wave_orientation": orientation,
            "is_canonical_default": orientation == DEFAULT_ORIENTATION,
            "first_shift": _first_shift(orientation),
            "racket_path": str(rule_path(orientation).relative_to(ROOT)),
            "racket_text": racket_program(orientation),
            "racket_sha256": racket_sha256(orientation),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executed_pairs": executed_pairs,
            "all_pairs_match_racket": True,
            "every_demo_refutes_alternative_setting": True,
        }

    if first_witness is None:
        raise AssertionError("no input distinguished the two orientation settings")

    return {
        "schema": "arcpuzzles-parametric-row-wave-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {
            "name": "wave_orientation",
            "allowed_values": list(ALLOWED_ORIENTATIONS),
            "canonical_default": DEFAULT_ORIENTATION,
            "selection": "ALLOWED_ORIENTATIONS[seed % 2], once per episode",
            "input_constraints": (
                "same lawful connected one-color row-wave inputs emitted by the "
                "selected canonical generator"
            ),
            "invariant_reasoning": (
                "last nonempty row anchor, distance modulo four, whole-row "
                "translation, hole preservation, and clipping"
            ),
        },
        "prototype_version": PROTOTYPE_VERSION,
        "prototype_source_sha256": source_sha256,
        "selected_generator_path": str(generator_source),
        "selected_generator_sha256": generator_sha256,
        "canonical_default_checks": canonical_checks,
        "canonical_default_all_match": all(row["matches"] for row in canonical_checks),
        "settings": settings,
        "differing_witness": first_witness,
        "limits": [
            "Prototype-only evidence for two orientations at one episode seed; not production approval.",
            "The selected generator, canonical rule text, RULE_HASH, and catalogue authority are unchanged.",
            "Demonstrations distinguish only the retained opposite-orientation rival; undeclared rules are not exhausted.",
            "The proposed right-first setting has bounded generated evidence, not a corpus-wide distribution study.",
        ],
    }


def write_evidence(evidence: dict[str, Any], out: Path) -> dict[str, Any]:
    """Write a source-bound private/public evidence bundle and file manifest."""
    out.mkdir(parents=True, exist_ok=False)
    for orientation in ALLOWED_ORIENTATIONS:
        setting = evidence["settings"][orientation]
        _write_json(out / "private" / f"episode-{orientation}.json", setting["episode"])
        _write_json(out / "public" / f"episode-{orientation}.json", setting["public_challenge"])
        rule_target = out / "rules" / f"{orientation}.rkt"
        rule_target.parent.mkdir(parents=True, exist_ok=True)
        rule_target.write_text(setting["racket_text"], encoding="utf-8")
    _write_json(out / "private" / "canonical-default.json", evidence["canonical_default_checks"])
    _write_json(out / "private" / "differing-witness.json", evidence["differing_witness"])
    _write_json(out / "report.json", evidence)

    files = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append(
                {
                    "path": str(path.relative_to(out)),
                    "size": path.stat().st_size,
                    "sha256": _sha256_path(path),
                }
            )
    manifest = {
        "schema": "arcpuzzles-parametric-row-wave-manifest-v1",
        "task_id": TASK_ID,
        "prototype_source_sha256": evidence["prototype_source_sha256"],
        "selected_generator_sha256": evidence["selected_generator_sha256"],
        "files": files,
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--out", type=Path, required=True, help="fresh evidence directory")
    parser.add_argument(
        "--write-public",
        type=Path,
        help="optional directory for stable public challenge examples",
    )
    args = parser.parse_args()

    evidence = build_evidence(args.seed)
    manifest = write_evidence(evidence, args.out)
    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for orientation in ALLOWED_ORIENTATIONS:
            _write_json(
                args.write_public / f"{orientation}_public.json",
                evidence["settings"][orientation]["public_challenge"],
            )

    print(
        json.dumps(
            {
                "status": evidence["status"],
                "task_id": TASK_ID,
                "seed": args.seed,
                "canonical_default_all_match": evidence["canonical_default_all_match"],
                "settings": {
                    orientation: {
                        "racket_sha256": evidence["settings"][orientation]["racket_sha256"],
                        "all_pairs_match_racket": evidence["settings"][orientation][
                            "all_pairs_match_racket"
                        ],
                        "every_demo_refutes_alternative_setting": evidence["settings"][
                            orientation
                        ]["every_demo_refutes_alternative_setting"],
                    }
                    for orientation in ALLOWED_ORIENTATIONS
                },
                "evidence_files": len(manifest["files"]),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

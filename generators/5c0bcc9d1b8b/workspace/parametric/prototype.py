#!/usr/bin/env python3
"""Prototype for nearby parameterized variants of ARC task 5c0bcc9d1b8b.

The selected production generator and canonical Racket authority remain fixed.
This task-local prototype varies two executed parts of the same transformation:

* ``output_wall_offset`` in {1, 2}: how far the rebuilt parallel walls sit from
  the center line.  The canonical/default value is 1.
* ``length_measure`` in {``cell_count``, ``track_span``}: whether the centered
  output line preserves gray-cell count (canonical/default) or the motif's
  longitudinal bounding-box span.

A complete setting is selected once per episode from the deterministic seed and
is shared by every demonstration and query in that episode.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

TASK_ID = "5c0bcc9d1b8b"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_WALL_OFFSETS = (1, 2)
ALLOWED_LENGTH_MEASURES = ("cell_count", "track_span")

ROOT = Path(__file__).resolve().parent
TASK_ROOT = ROOT.parents[1]
REPO_ROOT = ROOT.parents[3]
GENERATOR_PATH = TASK_ROOT / "generator.py"
RULE_DIR = ROOT / "rules"
TEST_PATH = TASK_ROOT / "tests" / "test_parametric_prototype.py"

# Three labelled demonstrations and one query.  Every profile has count greater
# than longitudinal span, so both length settings are visibly distinguishable;
# both track directions and several canonical sizes are represented.
EPISODE_PROFILES = (
    "n11_vertical_c7",
    "n13_horizontal_c9",
    "n19_vertical_c13",
    "n9_horizontal_c7",
)


@dataclass(frozen=True, order=True)
class RuleSetting:
    output_wall_offset: int
    length_measure: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "output_wall_offset": self.output_wall_offset,
            "length_measure": self.length_measure,
        }

    @property
    def slug(self) -> str:
        return f"walls{self.output_wall_offset}__{self.length_measure}"


DEFAULT_SETTING = RuleSetting(1, "cell_count")
ALL_SETTINGS = tuple(
    RuleSetting(offset, measure)
    for offset in ALLOWED_WALL_OFFSETS
    for measure in ALLOWED_LENGTH_MEASURES
)


def _validate_setting(setting: RuleSetting) -> RuleSetting:
    if not isinstance(setting, RuleSetting):
        raise TypeError("setting must be a RuleSetting")
    if type(setting.output_wall_offset) is not int or setting.output_wall_offset not in ALLOWED_WALL_OFFSETS:
        raise ValueError(
            f"output_wall_offset must be one of {ALLOWED_WALL_OFFSETS}, "
            f"got {setting.output_wall_offset!r}"
        )
    if setting.length_measure not in ALLOWED_LENGTH_MEASURES:
        raise ValueError(
            f"length_measure must be one of {ALLOWED_LENGTH_MEASURES}, "
            f"got {setting.length_measure!r}"
        )
    return setting


def choose_setting(seed: int) -> RuleSetting:
    """Choose one hidden rule setting for an entire episode."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    return ALL_SETTINGS[seed % len(ALL_SETTINGS)]


def _load_parent_generator():
    spec = importlib.util.spec_from_file_location(
        "parametric_parent_5c0bcc9d1b8b", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load parent generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_grid(grid: Any) -> tuple[int, int]:
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        raise ValueError("grid must be a nonempty rectangular sequence")
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def _is_divider(values: list[int]) -> bool:
    return all(value in (0, 5) for value in values) or (
        sum(value == 0 for value in values) > len(values) // 2
    )


def _divider_rows(grid: list[list[int]]) -> list[int]:
    return [row for row, values in enumerate(grid) if _is_divider(list(values))]


def _divider_cols(grid: list[list[int]]) -> list[int]:
    height, width = len(grid), len(grid[0])
    return [
        col
        for col in range(width)
        if _is_divider([grid[row][col] for row in range(height)])
    ]


def _line_length(grid: list[list[int]], *, vertical: bool, measure: str) -> int:
    gray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not gray:
        raise ValueError("input must contain at least one gray cell")
    if measure == "cell_count":
        return len(gray)
    coordinates = [row if vertical else col for row, col in gray]
    return max(coordinates) - min(coordinates) + 1


def python_transform(grid: list[list[int]], setting: RuleSetting) -> list[list[int]]:
    """Independent Python mirror for tests around actual Racket execution."""
    setting = _validate_setting(setting)
    height, width = _validate_grid(grid)
    divider_rows = _divider_rows(grid)
    divider_cols = _divider_cols(grid)
    center_row = (height - 1) // 2
    center_col = (width - 1) // 2
    vertical = len(divider_cols) >= 2
    line_length = _line_length(
        grid,
        vertical=vertical,
        measure=setting.length_measure,
    )

    output = [[7 for _ in range(width)] for _ in range(height)]
    if vertical:
        for col in (
            center_col - setting.output_wall_offset,
            center_col + setting.output_wall_offset,
        ):
            if not 0 <= col < width:
                raise ValueError("output_wall_offset places a wall outside the grid")
            for row in range(height):
                output[row][col] = 0
        for row in divider_rows:
            output[row] = [0 for _ in range(width)]
        half = (line_length - 1) // 2
        for index in range(line_length):
            row = center_row - half + index
            if 0 <= row < height:
                output[row][center_col] = 5
    else:
        for row in (
            center_row - setting.output_wall_offset,
            center_row + setting.output_wall_offset,
        ):
            if not 0 <= row < height:
                raise ValueError("output_wall_offset places a wall outside the grid")
            output[row] = [0 for _ in range(width)]
        for col in divider_cols:
            for row in range(height):
                output[row][col] = 0
        half = (line_length - 1) // 2
        for index in range(line_length):
            col = center_col - half + index
            if 0 <= col < width:
                output[center_row][col] = 5
    return output


def racket_program(setting: RuleSetting) -> str:
    """Return one exact standalone Racket implementation of a setting."""
    setting = _validate_setting(setting)
    racket_measure = setting.length_measure.replace("_", "-")
    return f'''#lang racket
(require json)

(define OUTPUT-WALL-OFFSET {setting.output_wall_offset})
(define LENGTH-MEASURE '{racket_measure})

(define (grid-rows grid) (length grid))
(define (grid-cols grid) (length (first grid)))
(define (at grid row col) (list-ref (list-ref grid row) col))

(define (divider-line? values)
  (or (andmap (lambda (value) (or (= value 0) (= value 5))) values)
      (> (for/sum ([value (in-list values)]) (if (= value 0) 1 0))
         (quotient (length values) 2))))

(define (divider-rows grid)
  (for/list ([row (in-range (grid-rows grid))]
             #:when (divider-line? (list-ref grid row)))
    row))

(define (divider-cols grid)
  (for/list ([col (in-range (grid-cols grid))]
             #:when
             (divider-line?
              (for/list ([row (in-range (grid-rows grid))])
                (at grid row col))))
    col))

(define (gray-cells grid)
  (for*/list ([row (in-range (grid-rows grid))]
              [col (in-range (grid-cols grid))]
              #:when (= (at grid row col) 5))
    (list row col)))

(define (full-grid height width value)
  (build-list height (lambda (_) (make-list width value))))

(define (set-cell grid target-row target-col value)
  (for/list ([values (in-list grid)] [row (in-naturals)])
    (if (= row target-row)
        (for/list ([cell (in-list values)] [col (in-naturals)])
          (if (= col target-col) value cell))
        values)))

(define (paint-row grid target-row value)
  (for/list ([values (in-list grid)] [row (in-naturals)])
    (if (= row target-row)
        (make-list (grid-cols grid) value)
        values)))

(define (paint-col grid target-col value)
  (for/list ([values (in-list grid)])
    (for/list ([cell (in-list values)] [col (in-naturals)])
      (if (= col target-col) value cell))))

(define (selected-line-length cells vertical?)
  (cond
    [(eq? LENGTH-MEASURE 'cell-count) (length cells)]
    [(eq? LENGTH-MEASURE 'track-span)
     (let ([coordinates
            (map (lambda (cell) (if vertical? (first cell) (second cell)))
                 cells)])
       (+ 1 (- (apply max coordinates) (apply min coordinates))))]
    [else (error 'selected-line-length "unsupported LENGTH-MEASURE")]))

(define (solve grid)
  (define height (grid-rows grid))
  (define width (grid-cols grid))
  (define drows (divider-rows grid))
  (define dcols (divider-cols grid))
  (define center-row (quotient (- height 1) 2))
  (define center-col (quotient (- width 1) 2))
  (define vertical? (>= (length dcols) 2))
  (define cells (gray-cells grid))
  (define line-length (selected-line-length cells vertical?))
  (define base (full-grid height width 7))
  (define with-walls
    (if vertical?
        (for/fold ([out base])
                  ([col (in-list
                         (list (- center-col OUTPUT-WALL-OFFSET)
                               (+ center-col OUTPUT-WALL-OFFSET)))])
          (paint-col out col 0))
        (for/fold ([out base])
                  ([row (in-list
                         (list (- center-row OUTPUT-WALL-OFFSET)
                               (+ center-row OUTPUT-WALL-OFFSET)))])
          (paint-row out row 0))))
  (define with-crossbar
    (if vertical?
        (for/fold ([out with-walls]) ([row (in-list drows)])
          (paint-row out row 0))
        (for/fold ([out with-walls]) ([col (in-list dcols)])
          (paint-col out col 0))))
  (define half (quotient (- line-length 1) 2))
  (for/fold ([out with-crossbar]) ([index (in-range line-length)])
    (if vertical?
        (let ([row (+ (- center-row half) index)])
          (if (and (>= row 0) (< row height))
              (set-cell out row center-col 5)
              out))
        (let ([col (+ (- center-col half) index)])
          (if (and (>= col 0) (< col width))
              (set-cell out center-row col 5)
              out)))))

(define input-grid (read-json))
(write-json (solve input-grid))
(newline)
'''


def rule_path(setting: RuleSetting) -> Path:
    setting = _validate_setting(setting)
    return RULE_DIR / f"{setting.slug}.rkt"


def racket_sha256(setting: RuleSetting) -> str:
    return hashlib.sha256(racket_program(setting).encode("utf-8")).hexdigest()


def materialize_rules() -> list[Path]:
    """Write the exact standalone Racket source for every bounded setting."""
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for setting in ALL_SETTINGS:
        path = rule_path(setting)
        path.write_text(racket_program(setting))
        paths.append(path)
    return paths


def _require_materialized_rules() -> None:
    for setting in ALL_SETTINGS:
        path = rule_path(setting)
        expected = racket_program(setting)
        if not path.is_file() or path.read_text() != expected:
            raise RuntimeError(
                f"materialized Racket source does not match setting {setting}: {path}"
            )


def run_racket(setting: RuleSetting, grid: list[list[int]]) -> list[list[int]]:
    """Execute the exact retained Racket program for one input grid."""
    setting = _validate_setting(setting)
    _validate_grid(grid)
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError(
            "racket executable not found; run through review.py run or run_with_racket.py"
        )
    _require_materialized_rules()
    completed = subprocess.run(
        [executable, str(rule_path(setting))],
        input=json.dumps(grid, separators=(",", ":")) + "\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Racket failed for {setting.slug} ({completed.returncode}): "
            f"{completed.stderr.strip()}"
        )
    result = json.loads(completed.stdout)
    _validate_grid(result)
    return result


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_episode(
    seed: int,
    setting: RuleSetting | None = None,
) -> dict[str, Any]:
    """Build three demonstrations and one labelled query for one fixed setting."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    selected = choose_setting(seed) if setting is None else _validate_setting(setting)
    parent = _load_parent_generator()
    pairs: list[dict[str, Any]] = []
    for index, profile in enumerate(EPISODE_PROFILES):
        grid = parent.generate(
            seed + 1009 * index,
            index,
            scene_profile=profile,
        )
        pairs.append(
            {
                "profile": profile,
                "input_sha256": _grid_sha256(grid),
                "input": copy.deepcopy(grid),
                "output": python_transform(grid, selected),
            }
        )
    return {
        "schema": "arcpuzzles-parametric-track-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": selected.as_dict(),
        "train": pairs[:3],
        "test": pairs[3:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return demos plus unlabeled query, omitting the hidden rule parameters."""
    return {
        "schema": "arcpuzzles-parametric-track-public-v1",
        "task_id": TASK_ID,
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def _canonical_pairs() -> list[dict[str, Any]]:
    runtime = REPO_ROOT / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    from reviewer_support import canonical_pairs

    return canonical_pairs(TASK_ID, root=REPO_ROOT, labeled_only=True)


def _sha256_path(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _runtime_identity(executable: str) -> dict[str, Any]:
    completed = subprocess.run(
        [executable, "--version"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    return {
        "executable": executable,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def build_evidence(seed: int) -> dict[str, Any]:
    """Execute all four settings and retain bounded discrimination evidence."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError(
            "racket executable not found; run through review.py run or run_with_racket.py"
        )
    _require_materialized_rules()

    output_cache: dict[tuple[str, str], list[list[int]]] = {}

    def executed(setting: RuleSetting, grid: list[list[int]]) -> list[list[int]]:
        key = (setting.slug, _grid_sha256(grid))
        if key not in output_cache:
            output_cache[key] = run_racket(setting, grid)
        return copy.deepcopy(output_cache[key])

    canonical_records: list[dict[str, Any]] = []
    for index, pair in enumerate(_canonical_pairs()):
        actual = executed(DEFAULT_SETTING, pair["input"])
        canonical_records.append(
            {
                "pair_index": index,
                "input_sha256": _grid_sha256(pair["input"]),
                "matches_label": actual == pair["output"],
                "input": pair["input"],
                "expected_output": pair["output"],
                "racket_output": actual,
            }
        )

    settings_report: dict[str, Any] = {}
    for setting in ALL_SETTINGS:
        episode = build_episode(seed=seed, setting=setting)
        executed_pairs: list[dict[str, Any]] = []
        all_match = True
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = executed(setting, pair["input"])
                python_output = python_transform(pair["input"], setting)
                pair_matches = actual == pair["output"] == python_output
                all_match = all_match and pair_matches
                rivals: dict[str, Any] = {}
                for rival in ALL_SETTINGS:
                    if rival == setting:
                        continue
                    rival_output = executed(rival, pair["input"])
                    rivals[rival.slug] = {
                        "parameter": rival.as_dict(),
                        "racket_output": rival_output,
                        "disagrees": rival_output != actual,
                    }
                executed_pairs.append(
                    {
                        "split": split,
                        "pair_index": pair_index,
                        "profile": pair["profile"],
                        "input_sha256": pair["input_sha256"],
                        "input": pair["input"],
                        "episode_output": pair["output"],
                        "python_output": python_output,
                        "racket_output": actual,
                        "matches": pair_matches,
                        "rivals": rivals,
                    }
                )
        demo_records = [row for row in executed_pairs if row["split"] == "train"]
        demos_distinguish = all(
            all(rival["disagrees"] for rival in row["rivals"].values())
            for row in demo_records
        )
        settings_report[setting.slug] = {
            "parameter": setting.as_dict(),
            "is_canonical_default": setting == DEFAULT_SETTING,
            "racket_path": str(rule_path(setting).relative_to(ROOT)),
            "racket_text": racket_program(setting),
            "racket_sha256": racket_sha256(setting),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executed_pairs": executed_pairs,
            "all_pairs_match_racket": all_match,
            "every_demo_refutes_all_rivals": demos_distinguish,
        }

    witness_input = settings_report[DEFAULT_SETTING.slug]["episode"]["train"][0]["input"]
    witness_outputs = {
        setting.slug: executed(setting, witness_input)
        for setting in ALL_SETTINGS
    }
    witness_keys = {
        json.dumps(output, separators=(",", ":"))
        for output in witness_outputs.values()
    }

    source_hashes = {
        "prototype.py": _sha256_path(Path(__file__)),
        "parent_generator.py": _sha256_path(GENERATOR_PATH),
        "test_parametric_prototype.py": _sha256_path(TEST_PATH),
    }
    canonical_matched = sum(record["matches_label"] for record in canonical_records)
    return {
        "schema": "arcpuzzles-parametric-track-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "episode_selected_setting": choose_setting(seed).as_dict(),
        "parameters": {
            "output_wall_offset": {
                "allowed_values": list(ALLOWED_WALL_OFFSETS),
                "canonical_default": DEFAULT_SETTING.output_wall_offset,
                "meaning": "distance from center to each rebuilt parallel output wall",
                "input_constraints": "odd canonical-sized grids must fit both symmetric walls",
            },
            "length_measure": {
                "allowed_values": list(ALLOWED_LENGTH_MEASURES),
                "canonical_default": DEFAULT_SETTING.length_measure,
                "meaning": "preserve gray-cell count or longitudinal motif span in the 1-wide output line",
                "input_constraints": "gray motif is nonempty and has a centered odd track span",
            },
            "selection": "ALL_SETTINGS[seed % 4], once per episode",
        },
        "source_hashes": source_hashes,
        "racket_runtime": _runtime_identity(executable),
        "canonical_default_replay": {
            "setting": DEFAULT_SETTING.as_dict(),
            "total": len(canonical_records),
            "matched": canonical_matched,
            "all_match": canonical_matched == len(canonical_records),
            "records": canonical_records,
        },
        "settings": settings_report,
        "distinguishing_witness": {
            "input_sha256": _grid_sha256(witness_input),
            "input": witness_input,
            "outputs": witness_outputs,
            "all_four_outputs_distinct": len(witness_keys) == len(ALL_SETTINGS),
        },
        "limits": [
            "Prototype evidence only; the production generator and canonical rule hash remain unchanged.",
            "The bounded settings are tested on four generated profiles at one episode seed plus canonical replay for the default.",
            "Declared parameter rivals are exhausted, but unrelated or more complex rival rules are not.",
            "The track-span alternative is intentionally nearby rather than claimed as an original ARC label.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    args = parser.parse_args(argv)

    evidence = build_evidence(args.seed)
    evidence["command"] = [sys.executable, *sys.argv]
    evidence["cwd"] = str(Path.cwd())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for slug, setting_report in evidence["settings"].items():
            destination = args.write_public / f"{slug}.public.json"
            destination.write_text(
                json.dumps(
                    setting_report["public_challenge"],
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

    print(
        json.dumps(
            {
                "status": evidence["status"],
                "seed": evidence["seed"],
                "canonical_default_replay": evidence["canonical_default_replay"]["all_match"],
                "settings": {
                    slug: {
                        "all_pairs_match_racket": row["all_pairs_match_racket"],
                        "every_demo_refutes_all_rivals": row["every_demo_refutes_all_rivals"],
                        "racket_sha256": row["racket_sha256"],
                    }
                    for slug, row in evidence["settings"].items()
                },
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

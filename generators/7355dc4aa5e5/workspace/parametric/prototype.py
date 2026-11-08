"""Bounded evidence builder for a proposed diagonal-radius rule parameter.

This module is deliberately outside the production generator.  It retains the
canonical cross/center/diagonal reasoning and varies only the distance of the
four diagonal cells from each original blue marker.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from itertools import combinations
import json
import os
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "7355dc4aa5e5"
PROTOTYPE_VERSION = "diagonal-radius-prototype-v1"
ALLOWED_DIAGONAL_RADII = (1, 2)
DEFAULT_DIAGONAL_RADIUS = 1
TRAIN_COUNT = 3
PAIR_COUNT = 4
LEGAL_BACKGROUNDS = (0, 4, 5, 6, 7, 8, 9)
PROFILES = (
    (9, 9, 2),
    (10, 12, 2),
    (12, 11, 3),
    (13, 13, 3),
)

LIMITATIONS = [
    "Proposed task-local prototype only; it does not change the canonical generator, catalog rule, or approval state.",
    "The original/default diagonal_radius=1 program is byte-for-byte the canonical Racket program after stripping outer whitespace.",
    "Only diagonal_radius in {1,2} is supported; row/column extent, marker color, center color, and diagonal color remain fixed.",
    "Prototype inputs keep every marker at least two cells from an edge so both settings expose four complete diagonal cells.",
    "Marker rows and columns are distinct and separated by at least three cells, avoiding parameter-dependent marker overwrites.",
    "Evidence covers two retained episodes (one per setting), four query rotations per episode, and the single declared rival setting.",
    "Finite examples refute the declared radius rival but do not prove identification against arbitrary programs or training suitability.",
    "The labeled one-marker canary is runtime plumbing and is not part of either public episode.",
]


def _validate_radius(diagonal_radius: Any) -> int:
    if type(diagonal_radius) is not int or diagonal_radius not in ALLOWED_DIAGONAL_RADII:
        raise ValueError(
            f"diagonal_radius must be one of {ALLOWED_DIAGONAL_RADII}, "
            f"got {diagonal_radius!r}"
        )
    return diagonal_radius


def rule_source(diagonal_radius: Any) -> str:
    """Materialize the exact legacy Racket rule for one parameter setting."""
    radius = _validate_radius(diagonal_radius)
    negative = -radius
    return f"""(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g))
               (dots (find-color g 1)))
           (reduce (lambda (acc dot)
                     (let ((r (fst dot))
                           (c (snd dot)))
                       (let ((g2 (reduce (lambda (a c2) (set-cell a r c2 1))
                                         acc
                                         (range 0 w))))
                         (let ((g3 (reduce (lambda (a r2) (set-cell a r2 c 1))
                                           g2
                                           (range 0 h))))
                           (let ((g4 (set-cell g3 r c 2)))
                             (reduce (lambda (a d)
                                       (let ((nr (+ r (fst d)))
                                             (nc (+ c (snd d))))
                                         (if (and (>= nr 0) (< nr h) (>= nc 0) (< nc w))
                                             (set-cell a nr nc 3)
                                             a)))
                                     g4
                                     (list (list {negative} {negative})
                                           (list {negative} {radius})
                                           (list {radius} {negative})
                                           (list {radius} {radius}))))))))
                   g
                   dots))))"""


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be literal ARC colors 0..9")
    return len(grid), width


def python_mirror(grid: list[list[int]], diagonal_radius: Any) -> list[list[int]]:
    """Independent mirror used only to cross-check the executed Racket output."""
    radius = _validate_radius(diagonal_radius)
    height, width = _validate_grid(grid)
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    if not markers:
        raise ValueError("grid must contain at least one blue marker")
    result = deepcopy(grid)
    for row, col in markers:
        for column in range(width):
            result[row][column] = 1
        for row_index in range(height):
            result[row_index][col] = 1
        result[row][col] = 2
        for row_delta, col_delta in (
            (-radius, -radius),
            (-radius, radius),
            (radius, -radius),
            (radius, radius),
        ):
            target_row = row + row_delta
            target_col = col + col_delta
            if 0 <= target_row < height and 0 <= target_col < width:
                result[target_row][target_col] = 3
    return result


def _stream_rng(seed: int, stream: str) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    digest = hashlib.sha256(f"{PROTOTYPE_VERSION}:{stream}:{seed}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def diagonal_radius_for_seed(seed: int) -> int:
    """Choose the hidden rule once from an episode-only deterministic stream."""
    return _stream_rng(seed, "rule").choice(ALLOWED_DIAGONAL_RADII)


def _spaced_choices(size: int, count: int) -> list[tuple[int, ...]]:
    # Two-cell edge margin exposes both radii.  Gap >=3 avoids a radius-2
    # diagonal stamp landing on another original marker.
    candidates = range(2, size - 2)
    return [
        values
        for values in combinations(candidates, count)
        if all(right - left >= 3 for left, right in zip(values, values[1:]))
    ]


def sample_inputs(seed: int) -> list[list[list[int]]]:
    """Draw four lawful inputs from a stream independent of the chosen rule."""
    rng = _stream_rng(seed, "inputs")
    backgrounds = list(LEGAL_BACKGROUNDS)
    rng.shuffle(backgrounds)
    inputs: list[list[list[int]]] = []
    for pair_index, (height, width, count) in enumerate(PROFILES):
        rows = list(rng.choice(_spaced_choices(height, count)))
        cols = list(rng.choice(_spaced_choices(width, count)))
        rng.shuffle(cols)
        markers = list(zip(rows, cols, strict=True))
        background = backgrounds[pair_index]
        grid = [[background for _ in range(width)] for _ in range(height)]
        for row, col in markers:
            grid[row][col] = 1
        # Every retained pair must expose the actual parameter difference.
        if python_mirror(grid, 1) == python_mirror(grid, 2):
            raise RuntimeError("sampled input does not distinguish diagonal radii")
        inputs.append(grid)
    return inputs


def sample_episode(seed: int) -> dict[str, Any]:
    radius = diagonal_radius_for_seed(seed)
    inputs = sample_inputs(seed)
    episode_id = "episode-" + _json_sha256(inputs)[:16]
    return {
        "episode_id": episode_id,
        "seed": seed,
        "parameters": {"diagonal_radius": radius},
        "program": rule_source(radius),
        "inputs": inputs,
        "train_count": TRAIN_COUNT,
    }


def select_seeds(base_seed: int) -> dict[str, Any]:
    if type(base_seed) is not int:
        raise TypeError("base_seed must be a literal integer")
    found: dict[int, int] = {}
    examined = 0
    for seed in range(base_seed, base_seed + 1000):
        examined += 1
        found.setdefault(diagonal_radius_for_seed(seed), seed)
        if set(found) == set(ALLOWED_DIAGONAL_RADII):
            break
    if set(found) != set(ALLOWED_DIAGONAL_RADII):
        raise RuntimeError("could not find one deterministic seed per setting")
    return {
        "base_seed": base_seed,
        "examined_seeds": examined,
        "by_diagonal_radius": {str(radius): found[radius] for radius in ALLOWED_DIAGONAL_RADII},
        "seeds": [found[radius] for radius in ALLOWED_DIAGONAL_RADII],
    }


def public_challenge(pairs: list[dict[str, Any]], query_index: int = TRAIN_COUNT) -> dict[str, Any]:
    if type(query_index) is not int or len(pairs) != PAIR_COUNT or not 0 <= query_index < len(pairs):
        raise ValueError(f"query_index must select one of exactly {PAIR_COUNT} pairs")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for index, pair in enumerate(pairs)
            if index != query_index
        ],
        "test": [{"input": deepcopy(pairs[query_index]["input"])}],
    }


def score_rotation(
    predictions: dict[int, list[list[list[int]]]],
    chosen_radius: Any,
    query_index: int,
) -> dict[str, Any]:
    chosen = _validate_radius(chosen_radius)
    if set(predictions) != set(ALLOWED_DIAGONAL_RADII):
        raise ValueError("predictions must cover every declared diagonal_radius")
    length = len(predictions[chosen])
    if length != PAIR_COUNT or type(query_index) is not int or not 0 <= query_index < length:
        raise ValueError("inconsistent predictions or query index")
    if any(len(outputs) != length for outputs in predictions.values()):
        raise ValueError("inconsistent prediction lengths")
    demos = [index for index in range(length) if index != query_index]
    rivals = []
    for radius in ALLOWED_DIAGONAL_RADII:
        if radius == chosen:
            continue
        mismatches = [
            index
            for index in demos
            if predictions[radius][index] != predictions[chosen][index]
        ]
        query_disagrees = predictions[radius][query_index] != predictions[chosen][query_index]
        status = (
            "refuted_by_demonstrations"
            if mismatches
            else "ambiguous_query"
            if query_disagrees
            else "survived_all"
        )
        rivals.append(
            {
                "diagonal_radius": radius,
                "status": status,
                "demonstration_mismatches": mismatches,
                "query_disagrees": query_disagrees,
            }
        )
    return {
        "query_pair_index": query_index,
        "demonstration_pair_indices": demos,
        "is_production_query": query_index == TRAIN_COUNT,
        "rivals": rivals,
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha256(value: Any) -> str:
    return _sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _source_bindings() -> dict[str, str]:
    from arc_repl import isolated_verifier, racket_bridge

    here = Path(__file__).resolve()
    root = here.parents[4]
    task_home = here.parents[2]
    paths = [
        here,
        here.with_name("README.md"),
        task_home / "generator.py",
        task_home / "tests/test_parametric_diagonal_radius.py",
        Path(isolated_verifier.__file__).resolve(),
        Path(racket_bridge.__file__).resolve(),
        Path(racket_bridge.__file__).with_name("executor.py").resolve(),
        Path(racket_bridge.__file__).parent / "racket_prelude/arc-prelude.rkt",
    ]
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
    }


def run_evidence(
    out: Path,
    *,
    base_seed: int = 20261019,
    racket_path: str | None = None,
) -> dict[str, Any]:
    """Execute both programs with the isolated real-Racket verifier."""
    from arc_repl.isolated_verifier import verify_candidate

    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)
    (out / "private/racket").mkdir(parents=True)
    (out / "private/episodes").mkdir(parents=True)

    selection = select_seeds(base_seed)
    report: dict[str, Any] = {
        "schema": "parametric-diagonal-radius-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_contract": {
            "name": "diagonal_radius",
            "allowed_values": list(ALLOWED_DIAGONAL_RADII),
            "original_default": DEFAULT_DIAGONAL_RADIUS,
            "sampling_unit": "once per episode from a rule-only deterministic seed stream",
            "dependent_input_constraints": [
                "markers are at least two cells from every edge",
                "marker rows and columns are distinct and separated by at least three cells",
            ],
        },
        "seed_selection": selection,
        "rules": [],
        "episodes": [],
        "limitations": LIMITATIONS,
        "invocation": {
            "argv": list(sys.argv),
            "cwd": str(Path.cwd()),
            "python_executable": sys.executable,
            "python_version": sys.version,
        },
    }
    _write_json(out / "report.json", report)

    try:
        report["source_sha256"] = _source_bindings()
        chosen_racket = racket_path if racket_path is not None else os.environ.get("RACKET_PATH", "")
        binary = Path(chosen_racket).resolve(strict=True)
        report["runtime"] = {
            "backend": "racket",
            "public_api": "arc_repl.isolated_verifier.verify_candidate",
            "racket_path": str(binary),
            "racket_sha256": _sha256(binary.read_bytes()),
        }

        episodes = [sample_episode(seed) for seed in selection["seeds"]]
        execution_inputs = [
            {
                "episode_id": episode["episode_id"],
                "pair_index": pair_index,
                "input": grid,
                "input_sha256": _json_sha256(grid),
            }
            for episode in episodes
            for pair_index, grid in enumerate(episode["inputs"])
        ]
        _write_json(out / "private/execution_inputs.json", execution_inputs)

        predictions: dict[int, list[list[list[int]]]] = {}
        parity_matches = 0
        for radius in ALLOWED_DIAGONAL_RADII:
            program = rule_source(radius)
            program_sha = _sha256(program.encode())
            rule_rel = f"private/rules/diagonal_radius_{radius}.rkt"
            receipt_rel = f"private/racket/diagonal_radius_{radius}.json"
            (out / rule_rel).write_text(program + "\n", encoding="utf-8")
            report["rules"].append(
                {
                    "parameters": {"diagonal_radius": radius},
                    "source": program,
                    "sha256": program_sha,
                    "path": rule_rel,
                    "execution_path": receipt_rel,
                    "canonical_default": radius == DEFAULT_DIAGONAL_RADIUS,
                }
            )

            canary_input = [[0 for _ in range(7)] for _ in range(7)]
            canary_input[3][3] = 1
            canary = {
                "input": canary_input,
                "output": python_mirror(canary_input, radius),
            }
            task = {
                "train": [canary],
                "test": [{"input": row["input"]} for row in execution_inputs],
            }
            receipt = verify_candidate(task, program, racket_path=str(binary))
            _write_json(
                out / receipt_rel,
                {
                    "program": program,
                    "program_sha256": program_sha,
                    "canary": canary,
                    "input_order": "../execution_inputs.json",
                    "input_sha256": [row["input_sha256"] for row in execution_inputs],
                    "receipt": receipt,
                },
            )
            if receipt.get("status") != "pass" or receipt.get("backend") != "racket":
                raise RuntimeError(
                    f"Racket execution failed for diagonal_radius={radius}: "
                    f"{receipt.get('error')}"
                )
            predictions[radius] = receipt["test_outputs"]
            for row, observed in zip(execution_inputs, predictions[radius], strict=True):
                expected = python_mirror(row["input"], radius)
                if observed != expected:
                    _write_json(
                        out / "private/parity_failure.json",
                        {
                            "diagonal_radius": radius,
                            "input": row["input"],
                            "racket_output": observed,
                            "python_mirror": expected,
                        },
                    )
                    raise RuntimeError(f"Racket/Python mismatch at diagonal_radius={radius}")
                parity_matches += 1

        offset = 0
        rotation_rows = []
        for episode in episodes:
            chosen = episode["parameters"]["diagonal_radius"]
            episode_predictions = {
                radius: predictions[radius][offset : offset + PAIR_COUNT]
                for radius in ALLOWED_DIAGONAL_RADII
            }
            offset += PAIR_COUNT
            pairs = [
                {"input": grid, "output": output}
                for grid, output in zip(
                    episode["inputs"], episode_predictions[chosen], strict=True
                )
            ]
            rotations = [
                score_rotation(episode_predictions, chosen, query_index)
                for query_index in range(PAIR_COUNT)
            ]
            rotation_rows.extend(rotations)
            public = public_challenge(pairs)
            public_rel = f"public/{episode['episode_id']}.json"
            private_rel = f"private/episodes/{episode['episode_id']}.json"
            _write_json(out / public_rel, public)
            _write_json(
                out / private_rel,
                {
                    "episode_id": episode["episode_id"],
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "program": episode["program"],
                    "program_sha256": _sha256(episode["program"].encode()),
                    "pairs": pairs,
                    "cross_setting_outputs": {
                        str(radius): episode_predictions[radius]
                        for radius in ALLOWED_DIAGONAL_RADII
                    },
                    "rotations": rotations,
                    "public_path": public_rel,
                    "public_sha256": _sha256((out / public_rel).read_bytes()),
                },
            )
            report["episodes"].append(
                {
                    "episode_id": episode["episode_id"],
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "public_path": public_rel,
                    "public_sha256": _sha256((out / public_rel).read_bytes()),
                    "private_path": private_rel,
                    "private_sha256": _sha256((out / private_rel).read_bytes()),
                }
            )

        witness = execution_inputs[0]["input"]
        witness_outputs = {
            str(radius): predictions[radius][0]
            for radius in ALLOWED_DIAGONAL_RADII
        }
        _write_json(
            out / "private/cross_setting_witness.json",
            {
                "input": witness,
                "input_sha256": _json_sha256(witness),
                "outputs": witness_outputs,
                "output_sha256": {
                    radius: _json_sha256(output)
                    for radius, output in witness_outputs.items()
                },
                "pairwise_outputs_distinct": len(
                    {_json_sha256(output) for output in witness_outputs.values()}
                )
                == len(ALLOWED_DIAGONAL_RADII),
            },
        )

        rival_rows = [rival for rotation in rotation_rows for rival in rotation["rivals"]]
        report["summary"] = {
            "episodes": len(episodes),
            "episode_pairs": len(execution_inputs),
            "racket_rule_applications": len(execution_inputs) * len(ALLOWED_DIAGONAL_RADII),
            "racket_canaries": len(ALLOWED_DIAGONAL_RADII),
            "python_mirror_matches": parity_matches,
            "query_rotations": len(rotation_rows),
            "rotation_rival_checks": len(rival_rows),
            "refuted_rotation_rivals": sum(
                row["status"] == "refuted_by_demonstrations" for row in rival_rows
            ),
            "ambiguous_rotation_rivals": sum(
                row["status"] == "ambiguous_query" for row in rival_rows
            ),
            "survived_rotation_rivals": sum(
                row["status"] == "survived_all" for row in rival_rows
            ),
        }
        if _source_bindings() != report["source_sha256"]:
            raise RuntimeError("bound source files changed during evidence execution")
        if any(row["status"] != "refuted_by_demonstrations" for row in rival_rows):
            report["status"] = "ambiguity"
        else:
            report["status"] = "pass"
    except Exception as exc:  # Evidence must retain failures rather than disappear.
        report["status"] = "error"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}

    _write_json(out / "report.json", report)
    manifest = {
        "schema": "parametric-evidence-manifest-v1",
        "status": report["status"],
        "task_id": TASK_ID,
        "report": "report.json",
        "report_sha256": _sha256((out / "report.json").read_bytes()),
        "public_challenges": [row["public_path"] for row in report.get("episodes", [])],
        "private_evidence": [row["private_path"] for row in report.get("episodes", [])],
    }
    _write_json(out / "manifest.json", manifest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=20261019)
    args = parser.parse_args(argv)
    report = run_evidence(args.out, base_seed=args.base_seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "out": str(args.out),
                "summary": report.get("summary"),
                "error": report.get("error"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Task-local period-2/period-3 prototype for marker-defined residue filling.

This module is deliberately outside the production generator. It preserves the
canonical object roles and transformation: locate the unique non-0/non-5 marker,
use its row and column residue as an ordered pair, recolor matching background-0
cells with the marker color, and preserve gray blockers and all other cells.
Only the lattice period varies once per episode.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "c9034f0626e0"
PROTOTYPE_VERSION = "lattice-period-prototype-v1"
ALLOWED_PERIODS = (2, 3)
DEFAULT_PERIOD = 2
TRAIN_COUNT = 3
PAIR_COUNT = 4

LIMITATIONS = [
    "Proposed task-local prototype only; it does not change the selected canonical rule, production generator, catalog entry, or approval state.",
    "The original/default lattice_period=2 program is byte-for-byte the canonical Racket program after stripping outer whitespace.",
    "Only lattice_period in {2,3} is supported; marker semantics, ordered row/column residues, blockers, background, and output color remain fixed.",
    "Inputs are drawn from the selected production generator and filtered so every retained input distinguishes periods 2 and 3.",
    "Evidence retains two episodes (one per setting), four query rotations per episode, and the single declared rival setting.",
    "Finite evidence establishes execution and pairwise identifiability for retained cases, not uniqueness against arbitrary programs or training approval.",
]

CANONICAL_RULE = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g)))\n           (let* ((hh (rows g))\n                  (ww (cols g))\n                  (marker #f)\n                  (mr 0)\n                  (mc 0)\n                  (dummy (for* ((r (range 0 hh)) (c (range 0 ww)))\n                               (when\n                                 (and (not marker) (!= (at g r c) 0) (!= (at g r c) 5))\n                                 (set! marker (at g r c))\n                                 (set! mr r)\n                                 (set! mc c))))\n                  (rp (remainder mr 2))\n                  (cp (remainder mc 2)))\n             (build-grid hh\n                         ww\n                         (r c)\n                         (if (and\n                               (= (remainder r 2) rp)\n                               (= (remainder c 2) cp)\n                               (zero? (at g r c)))\n                             marker\n                             (at g r c)))))))'


def _validate_period(lattice_period: Any) -> int:
    if type(lattice_period) is not int or lattice_period not in ALLOWED_PERIODS:
        raise ValueError(
            f"lattice_period must be one of {ALLOWED_PERIODS}, got {lattice_period!r}"
        )
    return lattice_period


def rule_source(lattice_period: Any = DEFAULT_PERIOD) -> str:
    """Materialize the exact Racket program for one period setting."""
    period = _validate_period(lattice_period)
    if period == DEFAULT_PERIOD:
        return CANONICAL_RULE
    program = CANONICAL_RULE
    for variable in ("mr", "mc", "r", "c"):
        needle = f"(remainder {variable} 2)"
        replacement = f"(remainder {variable} {period})"
        if program.count(needle) != 1:
            raise RuntimeError(
                f"canonical remainder for {variable} is not uniquely replaceable"
            )
        program = program.replace(needle, replacement, 1)
    return program


def _validate_grid(grid: Any) -> tuple[int, int]:
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(cell) is not int or not 0 <= cell <= 9
        for row in grid
        for cell in row
    ):
        raise ValueError("grid cells must be literal ARC color integers 0..9")
    return len(grid), width


def _find_marker(grid: list[list[int]]) -> tuple[int, int, int]:
    _validate_grid(grid)
    markers = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]
    if len(markers) != 1:
        raise ValueError(
            f"expected exactly one non-0/non-5 marker, found {len(markers)}"
        )
    return markers[0]


def python_mirror(grid: list[list[int]], lattice_period: Any) -> list[list[int]]:
    """Independent mirror used only to cross-check real Racket execution."""
    period = _validate_period(lattice_period)
    marker_row, marker_col, marker_color = _find_marker(grid)
    output = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (
                value == 0
                and row % period == marker_row % period
                and col % period == marker_col % period
            ):
                output[row][col] = marker_color
    return output


def _stream_rng(seed: int, stream: str) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    digest = hashlib.sha256(f"{PROTOTYPE_VERSION}:{stream}:{seed}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def period_for_seed(seed: int) -> int:
    """Choose the hidden rule once from a rule-only deterministic stream."""
    return _stream_rng(seed, "rule").choice(ALLOWED_PERIODS)


def _load_parent_generator():
    from reviewer_support import find_root, load_selected_generator

    module, _path, _sha256 = load_selected_generator(
        TASK_ID, root=find_root(__file__)
    )
    return module


def sample_inputs(seed: int) -> list[list[list[int]]]:
    """Draw four lawful inputs independently of the hidden period setting."""
    rng = _stream_rng(seed, "inputs")
    parent = _load_parent_generator()
    difficulties = ("easy", "medium", "hard", "medium")
    inputs: list[list[list[int]]] = []
    for pair_index, difficulty in enumerate(difficulties):
        for _attempt in range(100):
            generated_seed = rng.randrange(0, 2**63)
            grid = parent.generate(
                generated_seed, pair_index, difficulty=difficulty
            )
            errors = parent.self_check(grid)
            if errors:
                raise RuntimeError(
                    f"parent generator emitted invalid input: {errors}"
                )
            strict_errors = parent.strict_canonical_like(grid)
            if strict_errors:
                raise RuntimeError(
                    f"parent generator emitted non-canonical input: {strict_errors}"
                )
            if python_mirror(grid, 2) != python_mirror(grid, 3):
                inputs.append(grid)
                break
        else:
            raise RuntimeError(
                f"could not draw a period-distinguishing input for pair {pair_index}"
            )
    return inputs


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return _sha256(payload.encode())


def sample_episode(seed: int) -> dict[str, Any]:
    period = period_for_seed(seed)
    inputs = sample_inputs(seed)
    episode_id = "episode-" + _json_sha256({"seed": seed, "inputs": inputs})[:16]
    return {
        "episode_id": episode_id,
        "seed": seed,
        "parameters": {"lattice_period": period},
        "program": rule_source(period),
        "inputs": inputs,
        "train_count": TRAIN_COUNT,
    }


def select_seeds(base_seed: int) -> dict[str, Any]:
    """Find one deterministic episode seed for each declared setting."""
    if type(base_seed) is not int:
        raise TypeError("base_seed must be a literal integer")
    found: dict[int, int] = {}
    examined = 0
    for seed in range(base_seed, base_seed + 1000):
        examined += 1
        found.setdefault(period_for_seed(seed), seed)
        if set(found) == set(ALLOWED_PERIODS):
            break
    if set(found) != set(ALLOWED_PERIODS):
        raise RuntimeError("could not find one deterministic seed per setting")
    return {
        "base_seed": base_seed,
        "examined_seeds": examined,
        "by_lattice_period": {
            str(period): found[period] for period in ALLOWED_PERIODS
        },
        "seeds": [found[period] for period in ALLOWED_PERIODS],
    }


def public_challenge(
    pairs: list[dict[str, Any]], query_index: int = TRAIN_COUNT
) -> dict[str, Any]:
    if (
        type(query_index) is not int
        or len(pairs) != PAIR_COUNT
        or not 0 <= query_index < PAIR_COUNT
    ):
        raise ValueError(f"query_index must select one of exactly {PAIR_COUNT} pairs")
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for index, pair in enumerate(pairs)
            if index != query_index
        ],
        "test": [{"input": deepcopy(pairs[query_index]["input"])}],
    }


def score_rotation(
    predictions: dict[int, list[list[list[int]]]],
    chosen_period: Any,
    query_index: int,
) -> dict[str, Any]:
    chosen = _validate_period(chosen_period)
    if set(predictions) != set(ALLOWED_PERIODS):
        raise ValueError("predictions must cover every declared lattice_period")
    length = len(predictions[chosen])
    if (
        length != PAIR_COUNT
        or type(query_index) is not int
        or not 0 <= query_index < length
    ):
        raise ValueError("inconsistent predictions or query index")
    if any(len(outputs) != length for outputs in predictions.values()):
        raise ValueError("inconsistent prediction lengths")

    demonstrations = [index for index in range(length) if index != query_index]
    rivals = []
    for period in ALLOWED_PERIODS:
        if period == chosen:
            continue
        mismatches = [
            index
            for index in demonstrations
            if predictions[period][index] != predictions[chosen][index]
        ]
        query_disagrees = (
            predictions[period][query_index] != predictions[chosen][query_index]
        )
        status = (
            "refuted_by_demonstrations"
            if mismatches
            else "ambiguous_query"
            if query_disagrees
            else "survived_all"
        )
        rivals.append(
            {
                "lattice_period": period,
                "status": status,
                "demonstration_mismatches": mismatches,
                "query_disagrees": query_disagrees,
            }
        )
    return {
        "query_pair_index": query_index,
        "demonstration_pair_indices": demonstrations,
        "is_production_query": query_index == TRAIN_COUNT,
        "rivals": rivals,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _canonical_program_from_ledger() -> str:
    from reviewer_support import canonical_path, find_root

    root = find_root(__file__)
    matches = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if (
                row.get("task_id") == TASK_ID
                and row.get("content_hash") == TASK_ID
            ):
                matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one base canonical row for {TASK_ID}, found {len(matches)}"
        )
    return matches[0]["program_solution"].strip()


def _source_bindings() -> dict[str, str]:
    from arc_repl import isolated_verifier, racket_bridge
    from reviewer_support import canonical_path, find_root

    here = Path(__file__).resolve()
    root = find_root(here)
    task_home = here.parents[2]
    paths = [
        here,
        task_home / "generator.py",
        task_home / "tests/test_generator.py",
        task_home / "tests/test_parametric_lattice_period.py",
        canonical_path(root),
        Path(isolated_verifier.__file__).resolve(),
        Path(racket_bridge.__file__).resolve(),
        Path(racket_bridge.__file__).with_name("executor.py").resolve(),
        Path(racket_bridge.__file__).parent / "racket_prelude/arc-prelude.rkt",
    ]
    return {
        path.resolve().relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
    }


def run_evidence(
    out: Path,
    *,
    base_seed: int = 20261023,
    racket_path: str | None = None,
) -> dict[str, Any]:
    """Execute both exact programs and retain complete source-bound evidence."""
    from arc_repl.isolated_verifier import verify_candidate
    from reviewer_support import public_challenge_bytes, public_challenge_id

    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)
    (out / "private/racket").mkdir(parents=True)
    (out / "private/episodes").mkdir(parents=True)

    report: dict[str, Any] = {
        "schema": "parametric-lattice-period-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_contract": {
            "name": "lattice_period",
            "allowed_values": list(ALLOWED_PERIODS),
            "original_default": DEFAULT_PERIOD,
            "sampling_unit": (
                "once per episode from a rule-only deterministic seed stream"
            ),
            "invariant_reasoning_steps": [
                "locate the unique non-background/non-blocker marker",
                "derive an ordered row-residue and column-residue pair",
                "preserve gray blockers and every nonzero cell",
                "paint matching zero cells with the marker color",
            ],
            "dependent_input_constraints": [
                "exactly one marker color outside {0,5}",
                "input passes the production generator's self_check and strict_canonical_like",
                "period-2 and period-3 outputs differ on every retained input",
            ],
        },
        "seed_selection": None,
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
        selection = select_seeds(base_seed)
        report["seed_selection"] = selection
        report["source_sha256"] = _source_bindings()

        chosen_racket = (
            racket_path
            if racket_path is not None
            else os.environ.get("RACKET_PATH", "")
        )
        binary = Path(chosen_racket).expanduser().resolve(strict=True)
        if not binary.is_file():
            raise FileNotFoundError(f"Racket path is not a file: {binary}")
        report["runtime"] = {
            "backend": "racket",
            "public_api": "arc_repl.isolated_verifier.verify_candidate",
            "racket_path": str(binary),
            "racket_sha256": _sha256(binary.read_bytes()),
        }

        canonical = _canonical_program_from_ledger()
        if rule_source(DEFAULT_PERIOD) != canonical:
            raise RuntimeError(
                "default program no longer equals the base canonical source"
            )

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
        for period in ALLOWED_PERIODS:
            program = rule_source(period)
            program_sha = _sha256(program.encode())
            rule_rel = f"private/rules/lattice_period_{period}.rkt"
            receipt_rel = f"private/racket/lattice_period_{period}.json"
            (out / rule_rel).write_text(program + "\n", encoding="utf-8")
            report["rules"].append(
                {
                    "parameters": {"lattice_period": period},
                    "source": program,
                    "sha256": program_sha,
                    "path": rule_rel,
                    "execution_path": receipt_rel,
                    "canonical_default": period == DEFAULT_PERIOD,
                }
            )

            canary_input = execution_inputs[0]["input"]
            canary = {
                "input": canary_input,
                "output": python_mirror(canary_input, period),
            }
            task = {
                "train": [canary],
                "test": [
                    {"input": row["input"]} for row in execution_inputs
                ],
            }
            receipt = verify_candidate(task, program, racket_path=str(binary))
            _write_json(
                out / receipt_rel,
                {
                    "program": program,
                    "program_sha256": program_sha,
                    "canary": canary,
                    "input_order": "../execution_inputs.json",
                    "input_sha256": [
                        row["input_sha256"] for row in execution_inputs
                    ],
                    "receipt": receipt,
                },
            )
            if (
                receipt.get("status") != "pass"
                or receipt.get("backend") != "racket"
            ):
                raise RuntimeError(
                    f"Racket execution failed for lattice_period={period}: "
                    f"{receipt.get('error')}"
                )
            predictions[period] = receipt["test_outputs"]
            for row, observed in zip(
                execution_inputs, predictions[period], strict=True
            ):
                expected = python_mirror(row["input"], period)
                if observed != expected:
                    _write_json(
                        out / "private/parity_failure.json",
                        {
                            "lattice_period": period,
                            "input": row["input"],
                            "racket_output": observed,
                            "python_mirror": expected,
                        },
                    )
                    raise RuntimeError(
                        f"Racket/Python mismatch at lattice_period={period}"
                    )
                parity_matches += 1

        offset = 0
        rotation_rows: list[dict[str, Any]] = []
        for episode in episodes:
            chosen = episode["parameters"]["lattice_period"]
            episode_predictions = {
                period: predictions[period][offset : offset + PAIR_COUNT]
                for period in ALLOWED_PERIODS
            }
            offset += PAIR_COUNT
            pairs = [
                {"input": grid, "output": output}
                for grid, output in zip(
                    episode["inputs"],
                    episode_predictions[chosen],
                    strict=True,
                )
            ]
            rotations = [
                score_rotation(episode_predictions, chosen, query_index)
                for query_index in range(PAIR_COUNT)
            ]
            rotation_rows.extend(rotations)
            public = public_challenge(pairs)
            public_rel = f"public/{public_challenge_id(public)}.json"
            private_rel = f"private/episodes/{episode['episode_id']}.json"
            (out / public_rel).write_bytes(public_challenge_bytes(public))
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
                        str(period): episode_predictions[period]
                        for period in ALLOWED_PERIODS
                    },
                    "rotations": rotations,
                    "public_path": public_rel,
                    "public_sha256": _sha256(
                        (out / public_rel).read_bytes()
                    ),
                },
            )
            report["episodes"].append(
                {
                    "episode_id": episode["episode_id"],
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "public_path": public_rel,
                    "public_sha256": _sha256(
                        (out / public_rel).read_bytes()
                    ),
                    "private_path": private_rel,
                    "private_sha256": _sha256(
                        (out / private_rel).read_bytes()
                    ),
                }
            )

        witness = execution_inputs[0]["input"]
        witness_outputs = {
            str(period): predictions[period][0]
            for period in ALLOWED_PERIODS
        }
        witness_distinct = (
            len({_json_sha256(output) for output in witness_outputs.values()})
            == len(ALLOWED_PERIODS)
        )
        _write_json(
            out / "private/cross_setting_witness.json",
            {
                "input": witness,
                "input_sha256": _json_sha256(witness),
                "outputs": witness_outputs,
                "output_sha256": {
                    period: _json_sha256(output)
                    for period, output in witness_outputs.items()
                },
                "pairwise_outputs_distinct": witness_distinct,
            },
        )

        rival_rows = [
            rival
            for rotation in rotation_rows
            for rival in rotation["rivals"]
        ]
        report["summary"] = {
            "episodes": len(episodes),
            "episode_pairs": len(execution_inputs),
            "racket_rule_applications": (
                len(execution_inputs) * len(ALLOWED_PERIODS)
            ),
            "racket_canaries": len(ALLOWED_PERIODS),
            "python_mirror_matches": parity_matches,
            "query_rotations": len(rotation_rows),
            "rotation_rival_checks": len(rival_rows),
            "refuted_rotation_rivals": sum(
                row["status"] == "refuted_by_demonstrations"
                for row in rival_rows
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
        report["status"] = (
            "pass"
            if witness_distinct
            and all(
                row["status"] == "refuted_by_demonstrations"
                for row in rival_rows
            )
            else "ambiguity"
        )
    except Exception as exc:  # retained evidence must describe every failure
        report["status"] = "error"
        report["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    _write_json(out / "report.json", report)
    files = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append(
                {
                    "path": path.relative_to(out).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": _sha256(path.read_bytes()),
                }
            )
    manifest = {
        "schema": "parametric-evidence-manifest-v1",
        "status": report["status"],
        "task_id": TASK_ID,
        "report": "report.json",
        "report_sha256": _sha256((out / "report.json").read_bytes()),
        "public_challenges": [
            row["public_path"] for row in report.get("episodes", [])
        ],
        "private_evidence": [
            row["private_path"] for row in report.get("episodes", [])
        ],
        "files": files,
    }
    _write_json(out / "manifest.json", manifest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=20261023)
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

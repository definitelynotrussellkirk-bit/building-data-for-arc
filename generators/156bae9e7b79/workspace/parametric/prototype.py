"""Bounded evidence builder for a proposed triangle growth-rate parameter.

This module is deliberately separate from the production generator.  It keeps
all canonical object roles and reasoning steps fixed—read the dense key row,
locate the vertical cyan line, and reveal a centered triangle over the observed
line interval—while varying only how quickly the visible radius grows per row.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "156bae9e7b79"
PROTOTYPE_VERSION = "triangle-growth-rate-prototype-v1"
ALLOWED_GROWTH_RATES = (1, 2)
DEFAULT_GROWTH_RATE = 1
TRAIN_COUNT = 3
PAIR_COUNT = 4

LIMITATIONS = [
    "Proposed task-local prototype only; it does not change the selected canonical rule, generator catalog entry, or approval state.",
    "The original/default growth_rate=1 program is byte-for-byte the canonical Racket program after stripping outer whitespace.",
    "Only growth_rate in {1,2} is supported; key extraction, line detection, active interval, colors, center, and saturation radius remain fixed.",
    "Inputs are drawn from the selected production generator, so the prototype is source-bound to that generator's lawful domain.",
    "Evidence retains two episodes (one per setting), four query rotations per episode, and the single declared rival setting.",
    "Every retained input distinguishes the two settings, but finite evidence does not prove identification against arbitrary programs or establish training approval.",
]

_CANONICAL_RULE = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (bg 5)
                  (key (for/list ((c (range 0 ww))) (at g 0 c)))
                  (line-col (let loop
                                 ((c 0))
                                 (if (for/or ((r (range 1 hh))) (= (at g r c) 8))
                                     c
                                     (loop (+ c 1)))))
                  (line-top (let loop
                                 ((r 0))
                                 (if (= (at g r line-col) 8) r (loop (+ r 1)))))
                  (line-bottom (let loop
                                    ((r (- hh 1)))
                                    (if (= (at g r line-col) 8) r (loop (- r 1)))))
                  (max-radius (quotient (- ww 1) 2)))
             (build-grid hh
                         ww
                         (r c)
                         (if (and (>= r line-top) (<= r line-bottom))
                             (let ((vis-r (min max-radius (- r line-top))))
                               (if (= c line-col)
                                   8
                                   (if (and
                                         (>= c (- line-col vis-r))
                                         (<= c (+ line-col vis-r)))
                                       (list-ref key c)
                                       bg)))
                             bg))))))"""


def _validate_growth_rate(growth_rate: Any) -> int:
    if type(growth_rate) is not int or growth_rate not in ALLOWED_GROWTH_RATES:
        raise ValueError(
            f"growth_rate must be one of {ALLOWED_GROWTH_RATES}, got {growth_rate!r}"
        )
    return growth_rate


def rule_source(growth_rate: Any) -> str:
    """Materialize the exact Racket program for one parameter setting."""
    rate = _validate_growth_rate(growth_rate)
    if rate == DEFAULT_GROWTH_RATE:
        return _CANONICAL_RULE
    needle = "(let ((vis-r (min max-radius (- r line-top))))"
    replacement = f"(let ((vis-r (min max-radius (* {rate} (- r line-top)))))"
    if _CANONICAL_RULE.count(needle) != 1:
        raise RuntimeError("canonical growth expression is not uniquely replaceable")
    return _CANONICAL_RULE.replace(needle, replacement, 1)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be literal ARC color integers 0..9")
    return len(grid), width


def _line_geometry(grid: list[list[int]]) -> tuple[int, int, int]:
    height, _ = _validate_grid(grid)
    line_cells = [
        (row, col)
        for row in range(1, height)
        for col, value in enumerate(grid[row])
        if value == 8
    ]
    if not line_cells:
        raise ValueError("grid must contain a cyan line below the key row")
    columns = {col for _, col in line_cells}
    if len(columns) != 1:
        raise ValueError("cyan line must occupy exactly one column")
    line_col = next(iter(columns))
    rows = sorted(row for row, _ in line_cells)
    if rows != list(range(rows[0], rows[-1] + 1)):
        raise ValueError("cyan line must be vertically contiguous")
    if grid[0][line_col] != 5:
        raise ValueError("key row must contain gray at the cyan-line column")
    return line_col, rows[0], rows[-1]


def python_mirror(grid: list[list[int]], growth_rate: Any) -> list[list[int]]:
    """Independent mirror used only to cross-check exact Racket execution."""
    rate = _validate_growth_rate(growth_rate)
    height, width = _validate_grid(grid)
    line_col, line_top, line_bottom = _line_geometry(grid)
    key = list(grid[0])
    max_radius = (width - 1) // 2
    result = [[5 for _ in range(width)] for _ in range(height)]
    for row in range(line_top, line_bottom + 1):
        visible_radius = min(max_radius, rate * (row - line_top))
        for col in range(width):
            if col == line_col:
                result[row][col] = 8
            elif line_col - visible_radius <= col <= line_col + visible_radius:
                result[row][col] = key[col]
    return result


def _stream_rng(seed: int, stream: str) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    digest = hashlib.sha256(f"{PROTOTYPE_VERSION}:{stream}:{seed}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def growth_rate_for_seed(seed: int) -> int:
    """Choose the hidden rule once from an episode-only deterministic stream."""
    return _stream_rng(seed, "rule").choice(ALLOWED_GROWTH_RATES)


def _load_parent_generator():
    path = Path(__file__).resolve().parents[2] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"parametric_parent_{TASK_ID}", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load parent generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_inputs(seed: int) -> list[list[list[int]]]:
    """Draw four lawful parent-generator inputs independently of the hidden rule."""
    rng = _stream_rng(seed, "inputs")
    parent = _load_parent_generator()
    difficulties = ("easy", "medium", "hard", "medium")
    inputs: list[list[list[int]]] = []
    for pair_index, difficulty in enumerate(difficulties):
        generated_seed = rng.randrange(0, 2**63)
        grid = parent.generate(generated_seed, pair_index, difficulty=difficulty)
        errors = parent.self_check(grid)
        if errors:
            raise RuntimeError(f"parent generator emitted invalid input: {errors}")
        if python_mirror(grid, 1) == python_mirror(grid, 2):
            raise RuntimeError("parent input does not distinguish growth rates")
        inputs.append(grid)
    return inputs


def sample_episode(seed: int) -> dict[str, Any]:
    rate = growth_rate_for_seed(seed)
    inputs = sample_inputs(seed)
    episode_id = "episode-" + _json_sha256({"seed": seed, "inputs": inputs})[:16]
    return {
        "episode_id": episode_id,
        "seed": seed,
        "parameters": {"growth_rate": rate},
        "program": rule_source(rate),
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
        found.setdefault(growth_rate_for_seed(seed), seed)
        if set(found) == set(ALLOWED_GROWTH_RATES):
            break
    if set(found) != set(ALLOWED_GROWTH_RATES):
        raise RuntimeError("could not find one deterministic seed per setting")
    return {
        "base_seed": base_seed,
        "examined_seeds": examined,
        "by_growth_rate": {str(rate): found[rate] for rate in ALLOWED_GROWTH_RATES},
        "seeds": [found[rate] for rate in ALLOWED_GROWTH_RATES],
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
    chosen_rate: Any,
    query_index: int,
) -> dict[str, Any]:
    chosen = _validate_growth_rate(chosen_rate)
    if set(predictions) != set(ALLOWED_GROWTH_RATES):
        raise ValueError("predictions must cover every declared growth_rate")
    length = len(predictions[chosen])
    if length != PAIR_COUNT or type(query_index) is not int or not 0 <= query_index < length:
        raise ValueError("inconsistent predictions or query index")
    if any(len(outputs) != length for outputs in predictions.values()):
        raise ValueError("inconsistent prediction lengths")
    demos = [index for index in range(length) if index != query_index]
    rivals = []
    for rate in ALLOWED_GROWTH_RATES:
        if rate == chosen:
            continue
        mismatches = [
            index for index in demos
            if predictions[rate][index] != predictions[chosen][index]
        ]
        query_disagrees = predictions[rate][query_index] != predictions[chosen][query_index]
        status = (
            "refuted_by_demonstrations"
            if mismatches
            else "ambiguous_query"
            if query_disagrees
            else "survived_all"
        )
        rivals.append(
            {
                "growth_rate": rate,
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
        task_home / "tests/test_generator.py",
        task_home / "tests/test_parametric_growth_rate.py",
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
    base_seed: int = 20261021,
    racket_path: str | None = None,
) -> dict[str, Any]:
    """Execute both exact programs and retain complete source-bound evidence."""
    from arc_repl.isolated_verifier import verify_candidate

    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)
    (out / "private/racket").mkdir(parents=True)
    (out / "private/episodes").mkdir(parents=True)

    selection = select_seeds(base_seed)
    report: dict[str, Any] = {
        "schema": "parametric-triangle-growth-rate-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_contract": {
            "name": "growth_rate",
            "allowed_values": list(ALLOWED_GROWTH_RATES),
            "original_default": DEFAULT_GROWTH_RATE,
            "sampling_unit": "once per episode from a rule-only deterministic seed stream",
            "invariant_reasoning_steps": [
                "read row 0 as the dense key",
                "locate the unique vertical cyan line",
                "restrict painting to the observed line interval",
                "reveal a centered, saturating triangular projection",
            ],
            "dependent_input_constraints": [
                "line length is at least two rows so growth is observable",
                "line position leaves a key cell two columns away on at least one side",
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

        if rule_source(DEFAULT_GROWTH_RATE).strip() != _CANONICAL_RULE.strip():
            raise RuntimeError("default program no longer equals the pinned canonical source")

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
        for rate in ALLOWED_GROWTH_RATES:
            program = rule_source(rate)
            program_sha = _sha256(program.encode())
            rule_rel = f"private/rules/growth_rate_{rate}.rkt"
            receipt_rel = f"private/racket/growth_rate_{rate}.json"
            (out / rule_rel).write_text(program + "\n", encoding="utf-8")
            report["rules"].append(
                {
                    "parameters": {"growth_rate": rate},
                    "source": program,
                    "sha256": program_sha,
                    "path": rule_rel,
                    "execution_path": receipt_rel,
                    "canonical_default": rate == DEFAULT_GROWTH_RATE,
                }
            )

            canary_input = execution_inputs[0]["input"]
            canary = {
                "input": canary_input,
                "output": python_mirror(canary_input, rate),
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
                    f"Racket execution failed for growth_rate={rate}: {receipt.get('error')}"
                )
            predictions[rate] = receipt["test_outputs"]
            for row, observed in zip(execution_inputs, predictions[rate], strict=True):
                expected = python_mirror(row["input"], rate)
                if observed != expected:
                    _write_json(
                        out / "private/parity_failure.json",
                        {
                            "growth_rate": rate,
                            "input": row["input"],
                            "racket_output": observed,
                            "python_mirror": expected,
                        },
                    )
                    raise RuntimeError(f"Racket/Python mismatch at growth_rate={rate}")
                parity_matches += 1

        offset = 0
        rotation_rows = []
        for episode in episodes:
            chosen = episode["parameters"]["growth_rate"]
            episode_predictions = {
                rate: predictions[rate][offset : offset + PAIR_COUNT]
                for rate in ALLOWED_GROWTH_RATES
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
                        str(rate): episode_predictions[rate]
                        for rate in ALLOWED_GROWTH_RATES
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
            str(rate): predictions[rate][0]
            for rate in ALLOWED_GROWTH_RATES
        }
        _write_json(
            out / "private/cross_setting_witness.json",
            {
                "input": witness,
                "input_sha256": _json_sha256(witness),
                "outputs": witness_outputs,
                "output_sha256": {
                    rate: _json_sha256(output)
                    for rate, output in witness_outputs.items()
                },
                "pairwise_outputs_distinct": len(
                    {_json_sha256(output) for output in witness_outputs.values()}
                ) == len(ALLOWED_GROWTH_RATES),
            },
        )

        rival_rows = [rival for rotation in rotation_rows for rival in rotation["rivals"]]
        report["summary"] = {
            "episodes": len(episodes),
            "episode_pairs": len(execution_inputs),
            "racket_rule_applications": len(execution_inputs) * len(ALLOWED_GROWTH_RATES),
            "racket_canaries": len(ALLOWED_GROWTH_RATES),
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
        report["status"] = (
            "pass"
            if all(row["status"] == "refuted_by_demonstrations" for row in rival_rows)
            else "ambiguity"
        )
    except Exception as exc:
        report["status"] = "error"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}

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
        "public_challenges": [row["public_path"] for row in report.get("episodes", [])],
        "private_evidence": [row["private_path"] for row in report.get("episodes", [])],
        "files": files,
    }
    _write_json(out / "manifest.json", manifest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=20261021)
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

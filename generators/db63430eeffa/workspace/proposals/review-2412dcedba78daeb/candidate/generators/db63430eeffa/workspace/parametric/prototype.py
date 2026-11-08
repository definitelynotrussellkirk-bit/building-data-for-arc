"""Racket-backed evidence builder for a proposed path-order rule parameter.

The production generator remains fixed to the canonical union of two paths.
This task-local prototype keeps the same endpoint detection, diagonal segment,
major-axis straight segment, endpoint preservation, and colors, while varying
which path order is painted: both orders (canonical), diagonal-first only, or
straight-first only.
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

from reviewer_support import (
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)

TASK_ID = "db63430eeffa"
PROTOTYPE_VERSION = "path-mode-prototype-v1"
ALLOWED_PATH_MODES = ("both", "diagonal_first", "straight_first")
DEFAULT_PATH_MODE = "both"
TRAIN_COUNT = 3
QUERY_COUNT = 4
PAIR_COUNT = TRAIN_COUNT + QUERY_COUNT

# First four profiles are the four official linked canonical forms.  The last
# three add the declared size/gap boundaries while preserving unequal gaps, so
# every input exposes all three parameter settings.
PROFILE_SPECS = (
    (12, 14, 7, 9),
    (13, 13, 9, 6),
    (11, 14, 2, 10),
    (13, 14, 11, 7),
    (7, 18, 2, 17),
    (16, 7, 15, 2),
    (10, 12, 8, 3),
)

LIMITATIONS = [
    "Proposed task-local prototype only; it does not change the canonical rule, catalog, approval, or training state.",
    "The original/default path_mode='both' program is exactly the canonical Racket program after stripping outer whitespace.",
    "Only path_mode in {'both','diagonal_first','straight_first'} is supported; endpoint colors, path color, segment geometry, and reading-order endpoint selection remain fixed.",
    "Prototype episodes use exactly three labeled demonstrations and four distinct unlabeled queries.",
    "All retained inputs have row/column gaps at least two and unequal, because equal gaps collapse both orders to the same diagonal and cannot identify this parameter.",
    "Evidence retains one episode per setting and executes every setting on every retained input in real Racket (63 logical rule applications).",
    "Finite demonstrations refute the two declared path-mode rivals but do not prove uniqueness against arbitrary programs or establish training suitability.",
    "The labeled canary used by the verifier is runtime plumbing and is not part of a public episode.",
]

_CANONICAL_BOTH_SOURCE = r"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((eights (find-color g 8))
                  (p1 (first eights))
                  (p2 (second eights))
                  (r1 (first p1))
                  (c1 (second p1))
                  (r2 (first p2))
                  (c2 (second p2))
                  (dr (- r2 r1))
                  (dc (- c2 c1))
                  (adr (abs dr))
                  (adc (abs dc))
                  (sr (cond ((> dr 0) 1) ((< dr 0) -1) (else 0)))
                  (sc (cond ((> dc 0) 1) ((< dc 0) -1) (else 0)))
                  (d-steps (min adr adc))
                  (s-steps (abs (- adr adc)))
                  (major-is-r (> adr adc))
                  (path (make-hash)))
             (let loop1
                  ((rr r1) (cc c1) (step 0))
                  (cond
                    ((< step d-steps) (hash-set! path (list rr cc) #t)
                      (loop1 (+ rr sr) (+ cc sc) (+ step 1)))
                    (else (let loop2
                               ((rr rr) (cc cc) (step 0))
                               (cond
                                 ((< step s-steps) (hash-set! path (list rr cc) #t)
                                   (cond
                                     (major-is-r (loop2 (+ rr sr) cc (+ step 1)))
                                     (else (loop2 rr (+ cc sc) (+ step 1)))))
                                 (else (hash-set! path (list rr cc) #t)))))))
             (let loop1
                  ((rr r1) (cc c1) (step 0))
                  (cond
                    ((< step s-steps) (hash-set! path (list rr cc) #t)
                      (cond
                        (major-is-r (loop1 (+ rr sr) cc (+ step 1)))
                        (else (loop1 rr (+ cc sc) (+ step 1)))))
                    (else (let loop2
                               ((rr rr) (cc cc) (step 0))
                               (cond
                                 ((< step d-steps) (hash-set! path (list rr cc) #t)
                                   (loop2 (+ rr sr) (+ cc sc) (+ step 1)))
                                 (else (hash-set! path (list rr cc) #t)))))))
             (cellmap g
                      (r c v)
                      (cond
                        ((and (= r r1) (= c c1)) 8)
                        ((and (= r r2) (= c c2)) 8)
                        ((hash-has-key? path (list r c)) 3)
                        (else 0)))))))"""

_DIAGONAL_FIRST_SOURCE = r"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((eights (find-color g 8))
                  (p1 (first eights))
                  (p2 (second eights))
                  (r1 (first p1))
                  (c1 (second p1))
                  (r2 (first p2))
                  (c2 (second p2))
                  (dr (- r2 r1))
                  (dc (- c2 c1))
                  (adr (abs dr))
                  (adc (abs dc))
                  (sr (cond ((> dr 0) 1) ((< dr 0) -1) (else 0)))
                  (sc (cond ((> dc 0) 1) ((< dc 0) -1) (else 0)))
                  (d-steps (min adr adc))
                  (s-steps (abs (- adr adc)))
                  (major-is-r (> adr adc))
                  (path (make-hash)))
             (let loop1
                  ((rr r1) (cc c1) (step 0))
                  (cond
                    ((< step d-steps) (hash-set! path (list rr cc) #t)
                      (loop1 (+ rr sr) (+ cc sc) (+ step 1)))
                    (else (let loop2
                               ((rr rr) (cc cc) (step 0))
                               (cond
                                 ((< step s-steps) (hash-set! path (list rr cc) #t)
                                   (cond
                                     (major-is-r (loop2 (+ rr sr) cc (+ step 1)))
                                     (else (loop2 rr (+ cc sc) (+ step 1)))))
                                 (else (hash-set! path (list rr cc) #t)))))))
             (cellmap g
                      (r c v)
                      (cond
                        ((and (= r r1) (= c c1)) 8)
                        ((and (= r r2) (= c c2)) 8)
                        ((hash-has-key? path (list r c)) 3)
                        (else 0)))))))"""

_STRAIGHT_FIRST_SOURCE = r"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((eights (find-color g 8))
                  (p1 (first eights))
                  (p2 (second eights))
                  (r1 (first p1))
                  (c1 (second p1))
                  (r2 (first p2))
                  (c2 (second p2))
                  (dr (- r2 r1))
                  (dc (- c2 c1))
                  (adr (abs dr))
                  (adc (abs dc))
                  (sr (cond ((> dr 0) 1) ((< dr 0) -1) (else 0)))
                  (sc (cond ((> dc 0) 1) ((< dc 0) -1) (else 0)))
                  (d-steps (min adr adc))
                  (s-steps (abs (- adr adc)))
                  (major-is-r (> adr adc))
                  (path (make-hash)))
             (let loop1
                  ((rr r1) (cc c1) (step 0))
                  (cond
                    ((< step s-steps) (hash-set! path (list rr cc) #t)
                      (cond
                        (major-is-r (loop1 (+ rr sr) cc (+ step 1)))
                        (else (loop1 rr (+ cc sc) (+ step 1)))))
                    (else (let loop2
                               ((rr rr) (cc cc) (step 0))
                               (cond
                                 ((< step d-steps) (hash-set! path (list rr cc) #t)
                                   (loop2 (+ rr sr) (+ cc sc) (+ step 1)))
                                 (else (hash-set! path (list rr cc) #t)))))))
             (cellmap g
                      (r c v)
                      (cond
                        ((and (= r r1) (= c c1)) 8)
                        ((and (= r r2) (= c c2)) 8)
                        ((hash-has-key? path (list r c)) 3)
                        (else 0)))))))"""

_RULE_SOURCES = {
    "both": _CANONICAL_BOTH_SOURCE,
    "diagonal_first": _DIAGONAL_FIRST_SOURCE,
    "straight_first": _STRAIGHT_FIRST_SOURCE,
}


def _validate_mode(path_mode: Any) -> str:
    if type(path_mode) is not str or path_mode not in ALLOWED_PATH_MODES:
        raise ValueError(
            f"path_mode must be one of {ALLOWED_PATH_MODES}, got {path_mode!r}"
        )
    return path_mode


def rule_source(path_mode: Any) -> str:
    """Return the exact Racket rule for one path-mode setting."""
    return _RULE_SOURCES[_validate_mode(path_mode)]


def _validate_grid(grid: Any) -> tuple[int, int, tuple[int, int], tuple[int, int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(cell) is not int or cell not in (0, 8)
        for row in grid
        for cell in row
    ):
        raise ValueError("grid cells must be literal 0 or 8 integers")
    endpoints = [
        (row, col)
        for row, values in enumerate(grid)
        for col, cell in enumerate(values)
        if cell == 8
    ]
    if len(endpoints) != 2:
        raise ValueError("grid must contain exactly two color-8 endpoints")
    first, second = endpoints
    row_gap = abs(second[0] - first[0])
    col_gap = abs(second[1] - first[1])
    if row_gap < 2 or col_gap < 2:
        raise ValueError("endpoint row and column gaps must both be at least two")
    if row_gap == col_gap:
        raise ValueError("prototype inputs require unequal row and column gaps")
    return len(grid), width, first, second


def _walk(
    first: tuple[int, int],
    second: tuple[int, int],
    *,
    diagonal_first: bool,
) -> set[tuple[int, int]]:
    r1, c1 = first
    r2, c2 = second
    dr, dc = r2 - r1, c2 - c1
    row_step = 1 if dr > 0 else -1 if dr < 0 else 0
    col_step = 1 if dc > 0 else -1 if dc < 0 else 0
    diagonal_steps = min(abs(dr), abs(dc))
    straight_steps = abs(abs(dr) - abs(dc))
    major_is_row = abs(dr) > abs(dc)
    row, col = r1, c1
    path: set[tuple[int, int]] = set()
    segments = (
        (("diagonal", diagonal_steps), ("straight", straight_steps))
        if diagonal_first
        else (("straight", straight_steps), ("diagonal", diagonal_steps))
    )
    for kind, steps in segments:
        for _ in range(steps):
            path.add((row, col))
            if kind == "diagonal":
                row += row_step
                col += col_step
            elif major_is_row:
                row += row_step
            else:
                col += col_step
    path.add((row, col))
    return path


def python_mirror(grid: list[list[int]], path_mode: Any) -> list[list[int]]:
    """Independent Python mirror used only to check executed Racket labels."""
    mode = _validate_mode(path_mode)
    height, width, first, second = _validate_grid(grid)
    path: set[tuple[int, int]] = set()
    if mode in ("both", "diagonal_first"):
        path.update(_walk(first, second, diagonal_first=True))
    if mode in ("both", "straight_first"):
        path.update(_walk(first, second, diagonal_first=False))
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in path:
        output[row][col] = 3
    output[first[0]][first[1]] = 8
    output[second[0]][second[1]] = 8
    return output


def _literal_seed(seed: Any, *, label: str) -> int:
    if type(seed) is not int:
        raise TypeError(f"{label} must be a literal integer")
    return seed


def _stream_rng(seed: Any, stream: str) -> random.Random:
    value = _literal_seed(seed, label="seed")
    digest = hashlib.sha256(
        f"{PROTOTYPE_VERSION}:{stream}:{value}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def path_mode_for_seed(seed: Any) -> str:
    """Choose the hidden rule once from a rule-only deterministic stream."""
    return _stream_rng(seed, "rule").choice(ALLOWED_PATH_MODES)


def sample_inputs(seed: Any) -> list[list[list[int]]]:
    """Draw seven inputs from a stream independent of the hidden rule."""
    rng = _stream_rng(seed, "inputs")
    inputs: list[list[list[int]]] = []
    for height, width, row_gap, col_gap in PROFILE_SPECS:
        r0 = rng.randint(0, height - 1 - row_gap)
        c0 = rng.randint(0, width - 1 - col_gap)
        r1, c1 = r0 + row_gap, c0 + col_gap
        if rng.choice((False, True)):
            first, second = (r0, c0), (r1, c1)
        else:
            first, second = (r0, c1), (r1, c0)
        grid = [[0 for _ in range(width)] for _ in range(height)]
        grid[first[0]][first[1]] = 8
        grid[second[0]][second[1]] = 8
        outputs = [python_mirror(grid, mode) for mode in ALLOWED_PATH_MODES]
        if len({_json_sha256(output) for output in outputs}) != len(ALLOWED_PATH_MODES):
            raise RuntimeError("sampled input does not distinguish every path_mode")
        inputs.append(grid)
    if len({_json_sha256(grid) for grid in inputs}) != PAIR_COUNT:
        raise RuntimeError("sampled episode contains duplicate inputs")
    return inputs


def sample_episode(seed: Any) -> dict[str, Any]:
    value = _literal_seed(seed, label="seed")
    mode = path_mode_for_seed(value)
    inputs = sample_inputs(value)
    return {
        "seed": value,
        "parameters": {"path_mode": mode},
        "program": rule_source(mode),
        "inputs": inputs,
        "input_batch_id": _json_sha256(inputs),
        "train_count": TRAIN_COUNT,
        "query_count": QUERY_COUNT,
    }


def select_seeds(base_seed: Any) -> dict[str, Any]:
    base = _literal_seed(base_seed, label="base_seed")
    found: dict[str, int] = {}
    examined = 0
    for seed in range(base, base + 1000):
        examined += 1
        found.setdefault(path_mode_for_seed(seed), seed)
        if set(found) == set(ALLOWED_PATH_MODES):
            break
    if set(found) != set(ALLOWED_PATH_MODES):
        raise RuntimeError("could not find one deterministic seed per path_mode")
    ordered = [found[mode] for mode in ALLOWED_PATH_MODES]
    return {
        "base_seed": base,
        "examined_seeds": examined,
        "by_path_mode": {mode: found[mode] for mode in ALLOWED_PATH_MODES},
        "seeds": ordered,
    }


def public_challenge(pairs: Any) -> dict[str, Any]:
    if type(pairs) is not list or len(pairs) != PAIR_COUNT:
        raise ValueError(f"pairs must contain exactly {PAIR_COUNT} labeled pairs")
    try:
        challenge = {
            "train": [
                {
                    "input": deepcopy(pair["input"]),
                    "output": deepcopy(pair["output"]),
                }
                for pair in pairs[:TRAIN_COUNT]
            ],
            "test": [
                {"input": deepcopy(pair["input"])}
                for pair in pairs[TRAIN_COUNT:]
            ],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("pairs require input and output grids") from exc
    # Shared helper is the fail-closed public schema validator.
    _public_challenge_bytes(challenge)
    return challenge


def public_bytes(challenge: Any) -> bytes:
    return _public_challenge_bytes(challenge)


def public_id(challenge: Any) -> str:
    return _public_challenge_id(challenge)


def score_episode(
    predictions: Any,
    chosen_mode: Any,
) -> dict[str, Any]:
    chosen = _validate_mode(chosen_mode)
    if type(predictions) is not dict or set(predictions) != set(ALLOWED_PATH_MODES):
        raise ValueError("predictions must cover every declared path_mode")
    if any(type(outputs) is not list or len(outputs) != PAIR_COUNT for outputs in predictions.values()):
        raise ValueError(f"each path_mode must have exactly {PAIR_COUNT} outputs")
    demos = list(range(TRAIN_COUNT))
    queries = list(range(TRAIN_COUNT, PAIR_COUNT))
    rivals = []
    for mode in ALLOWED_PATH_MODES:
        if mode == chosen:
            continue
        demonstration_mismatches = [
            index
            for index in demos
            if predictions[mode][index] != predictions[chosen][index]
        ]
        query_disagreements = [
            index
            for index in queries
            if predictions[mode][index] != predictions[chosen][index]
        ]
        status = (
            "refuted_by_demonstrations"
            if demonstration_mismatches
            else "ambiguous_queries"
            if query_disagreements
            else "survived_all"
        )
        rivals.append(
            {
                "path_mode": mode,
                "status": status,
                "demonstration_mismatches": demonstration_mismatches,
                "query_disagreements": query_disagreements,
                "all_queries_disagree": query_disagreements == queries,
            }
        )
    return {
        "chosen_path_mode": chosen,
        "demonstration_pair_indices": demos,
        "query_pair_indices": queries,
        "rivals": rivals,
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha256(value: Any) -> str:
    return _sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
            "utf-8"
        )
    )


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
        task_home / "tests/test_generator_db63430eeffa.py",
        task_home / "tests/test_parametric_path_mode.py",
        root / "shared/data/canonical/puzzles.jsonl",
        Path(isolated_verifier.__file__).resolve(),
        Path(racket_bridge.__file__).resolve(),
        Path(racket_bridge.__file__).with_name("executor.py").resolve(),
        Path(racket_bridge.__file__).parent / "racket_prelude/arc-prelude.rkt",
    ]
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
    }


def _canary_grid() -> list[list[int]]:
    grid = [[0 for _ in range(9)] for _ in range(7)]
    grid[0][1] = 8
    grid[4][7] = 8
    return grid


def run_evidence(
    out: Path,
    *,
    base_seed: Any = 20261023,
    racket_path: str | None = None,
) -> dict[str, Any]:
    """Execute all three rules on all retained inputs with real Racket."""
    from arc_repl.isolated_verifier import verify_candidate

    base = _literal_seed(base_seed, label="base_seed")
    out = Path(out).absolute()
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/rules").mkdir(parents=True)
    (out / "private/racket").mkdir(parents=True)
    (out / "private/episodes").mkdir(parents=True)

    selection = select_seeds(base)
    report: dict[str, Any] = {
        "schema": "parametric-path-mode-evidence-v1",
        "status": "running",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter_contract": {
            "name": "path_mode",
            "allowed_values": list(ALLOWED_PATH_MODES),
            "original_default": DEFAULT_PATH_MODE,
            "sampling_unit": "once per episode from a rule-only deterministic seed stream",
            "demonstrations_per_episode": TRAIN_COUNT,
            "queries_per_episode": QUERY_COUNT,
            "input_constraint": "row/column gaps are both >=2 and unequal",
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
        chosen_racket = (
            racket_path if racket_path is not None else os.environ.get("RACKET_PATH", "")
        )
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
                "episode_index": episode_index,
                "pair_index": pair_index,
                "input": grid,
                "input_sha256": _json_sha256(grid),
            }
            for episode_index, episode in enumerate(episodes)
            for pair_index, grid in enumerate(episode["inputs"])
        ]
        _write_json(out / "private/execution_inputs.json", execution_inputs)

        predictions: dict[str, list[list[list[int]]]] = {}
        parity_matches = 0
        canary_grid = _canary_grid()
        for mode in ALLOWED_PATH_MODES:
            program = rule_source(mode)
            program_sha = _sha256(program.encode("utf-8"))
            safe_mode = mode.replace("_", "-")
            rule_rel = f"private/rules/path-mode-{safe_mode}.rkt"
            receipt_rel = f"private/racket/path-mode-{safe_mode}.json"
            (out / rule_rel).write_text(program + "\n", encoding="utf-8")
            report["rules"].append(
                {
                    "parameters": {"path_mode": mode},
                    "source": program,
                    "sha256": program_sha,
                    "path": rule_rel,
                    "execution_path": receipt_rel,
                    "canonical_default": mode == DEFAULT_PATH_MODE,
                }
            )
            canary = {
                "input": canary_grid,
                "output": python_mirror(canary_grid, mode),
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
                    f"Racket execution failed for path_mode={mode!r}: "
                    f"{receipt.get('error')}"
                )
            outputs = receipt.get("test_outputs")
            if type(outputs) is not list or len(outputs) != len(execution_inputs):
                raise RuntimeError(f"Racket returned an incomplete output batch for {mode}")
            predictions[mode] = outputs
            for row, observed in zip(execution_inputs, outputs, strict=True):
                expected = python_mirror(row["input"], mode)
                if observed != expected:
                    _write_json(
                        out / "private/parity_failure.json",
                        {
                            "path_mode": mode,
                            "input": row["input"],
                            "racket_output": observed,
                            "python_mirror": expected,
                        },
                    )
                    raise RuntimeError(f"Racket/Python mismatch for path_mode={mode}")
                parity_matches += 1

        offset = 0
        rival_rows = []
        for episode_index, episode in enumerate(episodes):
            chosen = episode["parameters"]["path_mode"]
            episode_predictions = {
                mode: predictions[mode][offset : offset + PAIR_COUNT]
                for mode in ALLOWED_PATH_MODES
            }
            offset += PAIR_COUNT
            scored = score_episode(episode_predictions, chosen)
            rival_rows.extend(scored["rivals"])
            pairs = [
                {"input": grid, "output": output}
                for grid, output in zip(
                    episode["inputs"], episode_predictions[chosen], strict=True
                )
            ]
            public = public_challenge(pairs)
            challenge_id = public_id(public)
            public_rel = f"public/{challenge_id}.json"
            private_rel = f"private/episodes/{challenge_id}.json"
            (out / public_rel).write_bytes(public_bytes(public))
            _write_json(
                out / private_rel,
                {
                    "public_challenge_id": challenge_id,
                    "episode_index": episode_index,
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "program": episode["program"],
                    "program_sha256": _sha256(episode["program"].encode("utf-8")),
                    "pairs": pairs,
                    "cross_setting_outputs": episode_predictions,
                    "score": scored,
                    "public_path": public_rel,
                    "public_sha256": _sha256((out / public_rel).read_bytes()),
                },
            )
            report["episodes"].append(
                {
                    "public_challenge_id": challenge_id,
                    "parameters": episode["parameters"],
                    "public_path": public_rel,
                    "public_sha256": _sha256((out / public_rel).read_bytes()),
                    "private_path": private_rel,
                    "private_sha256": _sha256((out / private_rel).read_bytes()),
                    "rival_statuses": [row["status"] for row in scored["rivals"]],
                }
            )

        witness = execution_inputs[0]["input"]
        witness_outputs = {
            mode: predictions[mode][0] for mode in ALLOWED_PATH_MODES
        }
        _write_json(
            out / "private/cross_setting_witness.json",
            {
                "input": witness,
                "input_sha256": _json_sha256(witness),
                "outputs": witness_outputs,
                "output_sha256": {
                    mode: _json_sha256(output)
                    for mode, output in witness_outputs.items()
                },
                "pairwise_outputs_distinct": len(
                    {_json_sha256(output) for output in witness_outputs.values()}
                )
                == len(ALLOWED_PATH_MODES),
            },
        )

        public_leaks = []
        for public_path in sorted((out / "public").glob("*.json")):
            challenge = json.loads(public_path.read_text(encoding="utf-8"))
            expected_name = public_id(challenge) + ".json"
            if public_path.name != expected_name:
                public_leaks.append(f"content ID mismatch: {public_path.name}")
            if len(challenge.get("train", [])) != TRAIN_COUNT:
                public_leaks.append(f"wrong train count: {public_path.name}")
            if len(challenge.get("test", [])) != QUERY_COUNT:
                public_leaks.append(f"wrong test count: {public_path.name}")
            if any(set(pair) != {"input"} for pair in challenge.get("test", [])):
                public_leaks.append(f"query label leak: {public_path.name}")
            body = public_path.read_text(encoding="utf-8")
            if any(
                token in body
                for token in (
                    "path_mode",
                    "diagonal_first",
                    "straight_first",
                    "rule!",
                    "seed",
                    "parameters",
                )
            ):
                public_leaks.append(f"private token leak: {public_path.name}")
        _write_json(
            out / "private/public_export_audit.json",
            {
                "checked_files": len(report["episodes"]),
                "findings": public_leaks,
                "status": "pass" if not public_leaks else "fail",
            },
        )

        report["summary"] = {
            "episodes": len(episodes),
            "episode_pairs": len(execution_inputs),
            "demonstrations": len(episodes) * TRAIN_COUNT,
            "queries": len(episodes) * QUERY_COUNT,
            "racket_rule_applications": len(execution_inputs)
            * len(ALLOWED_PATH_MODES),
            "racket_canaries": len(ALLOWED_PATH_MODES),
            "python_mirror_matches": parity_matches,
            "rival_checks": len(rival_rows),
            "refuted_rivals": sum(
                row["status"] == "refuted_by_demonstrations" for row in rival_rows
            ),
            "rivals_with_all_queries_disagreeing": sum(
                row["all_queries_disagree"] for row in rival_rows
            ),
            "public_export_findings": len(public_leaks),
        }
        if _source_bindings() != report["source_sha256"]:
            raise RuntimeError("bound source files changed during evidence execution")
        if any(row["status"] != "refuted_by_demonstrations" for row in rival_rows):
            report["status"] = "ambiguity"
        elif not all(row["all_queries_disagree"] for row in rival_rows):
            report["status"] = "query_collision"
        elif public_leaks:
            report["status"] = "public_export_failure"
        else:
            report["status"] = "pass"
    except Exception as exc:
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
    parser.add_argument("--base-seed", type=int, default=20261023)
    parser.add_argument("--racket-path", default=None)
    args = parser.parse_args(argv)
    report = run_evidence(
        args.out,
        base_seed=args.base_seed,
        racket_path=args.racket_path,
    )
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

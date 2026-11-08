"""Runnable evidence builder for a proposed bounding-box halo-radius parameter.

This task-local prototype preserves the canonical component, bounding-box, clipping,
and zero-only painting semantics.  It varies only the expansion radius, chosen once
per four-pair episode.  It is not imported by the production generator.
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

TASK_ID = "7185b8225f1c"
PROTOTYPE_VERSION = "bbox-halo-radius-prototype-v1"
ALLOWED_HALO_RADII = (1, 2)
DEFAULT_HALO_RADIUS = 1
TRAIN_COUNT = 3
PAIR_COUNT = 4
CANONICAL_RULE = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g)))\n           (let* ((hh (rows g))\n                  (ww (cols g))\n                  (visited (make-hash))\n                  (result (make-hash)))\n             (for* ((r (range 0 hh)) (c (range 0 ww)))\n                   (hash-set! result (list r c) (at g r c)))\n             (for* ((r (range 0 hh)) (c (range 0 ww)))\n                   (when\n                     (and (= (at g r c) 2) (not (hash-has-key? visited (list r c))))\n                     (let ((cells (list)))\n                       (let bfs\n                            ((q (list (list r c))))\n                            (unless\n                              (null? q)\n                              (let ((cr (first (car q)))\n                                    (cc (second (car q))))\n                                (cond\n                                  ((or\n                                     (hash-has-key? visited (list cr cc))\n                                     (< cr 0)\n                                     (>= cr hh)\n                                     (< cc 0)\n                                     (>= cc ww)\n                                     (!= (at g cr cc) 2)) (bfs (cdr q)))\n                                  (else (hash-set! visited (list cr cc) #t)\n                                        (set! cells (cons (list cr cc) cells))\n                                        (bfs (append (cdr q)\n                                                     (list (list (- cr 1) cc)\n                                                           (list (+ cr 1) cc)\n                                                           (list cr (- cc 1))\n                                                           (list cr (+ cc 1))))))))))\n                       (when\n                         (>= (length cells) 2)\n                         (let ((r1 (min-of first cells))\n                               (c1 (min-of second cells))\n                               (r2 (max-of first cells))\n                               (c2 (max-of second cells)))\n                           (for* ((br (range (- r1 1) (+ r2 2))) (bc (range (- c1 1) (+ c2 2))))\n                                 (when\n                                   (and\n                                     (>= br 0)\n                                     (< br hh)\n                                     (>= bc 0)\n                                     (< bc ww)\n                                     (zero? (hash-ref result (list br bc) 0)))\n                                   (hash-set! result (list br bc) 3))))))))\n             (build-grid hh ww (r c) (hash-ref result (list r c) 0))))))'
PROFILES = (
    ("horizontal_domino", 10, 11, ((0, 0), (0, 1))),
    ("vertical_domino", 12, 10, ((0, 0), (1, 0))),
    ("concave_l", 12, 13, ((0, 0), (1, 0), (1, 1))),
    ("rectangle", 14, 12, ((0, 0), (0, 1), (1, 0), (1, 1))),
)
ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
LIMITATIONS = [
    "Proposed task-local prototype only; it does not change the canonical generator, selected rule, or approval state.",
    "Only halo_radius in {1,2} is supported; radius 1 is the exact canonical program.",
    "Prototype multi-cell components stay at least two cells from every edge so both settings expose the complete added ring.",
    "Singletons are sampled outside each radius-2 expanded box to keep the parameter contrast visually direct.",
    "Evidence retains one four-pair episode per setting and tests all four query rotations against the other declared setting.",
    "Finite two-setting evidence does not establish unique induction against arbitrary programs or production training suitability.",
    "A labeled canary used for Racket bridge verification is private runtime plumbing, not a public episode.",
]


def _validate_radius(halo_radius: Any) -> int:
    if type(halo_radius) is not int or halo_radius not in ALLOWED_HALO_RADII:
        raise ValueError(
            f"halo_radius must be one of {ALLOWED_HALO_RADII}, got {halo_radius!r}"
        )
    return halo_radius


def rule_source(halo_radius: Any) -> str:
    """Return the exact Racket program for one proposed setting."""
    radius = _validate_radius(halo_radius)
    if radius == DEFAULT_HALO_RADIUS:
        return CANONICAL_RULE
    source = CANONICAL_RULE
    replacements = {
        "(range (- r1 1) (+ r2 2))": f"(range (- r1 {radius}) (+ r2 {radius + 1}))",
        "(range (- c1 1) (+ c2 2))": f"(range (- c1 {radius}) (+ c2 {radius + 1}))",
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise RuntimeError(f"canonical radius sentinel changed: {old}")
        source = source.replace(old, new)
    return source


def _validate_grid_shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not 8 <= len(grid) <= 30:
        raise ValueError("grid must contain eight through thirty rows")
    if not isinstance(grid[0], list) or not 8 <= len(grid[0]) <= 30:
        raise ValueError("grid must contain eight through thirty columns")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or cell not in (0, 2) for row in grid for cell in row):
        raise ValueError("prototype inputs may contain only literal black 0 and red 2")
    return len(grid), width


def _red_components(grid: list[list[int]]) -> tuple[frozenset[tuple[int, int]], ...]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }
    components: list[frozenset[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        reached = {start}
        frontier = [start]
        while frontier:
            row, col = frontier.pop()
            for dr, dc in ORTHOGONAL:
                neighbour = row + dr, col + dc
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    reached.add(neighbour)
                    frontier.append(neighbour)
        components.append(frozenset(reached))
    return tuple(sorted(components, key=lambda cells: (min(cells), len(cells))))


def validate_prototype_input(grid: Any) -> list[str]:
    try:
        height, width = _validate_grid_shape(grid)
    except ValueError as exc:
        return [str(exc)]
    components = _red_components(grid)
    multis = [cells for cells in components if len(cells) >= 2]
    singles = [cells for cells in components if len(cells) == 1]
    errors: list[str] = []
    if not multis:
        errors.append("at least one multi-cell red component is required")
    if not singles:
        errors.append("at least one red singleton is required")
    for cells in multis:
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        if min(rows) < 2 or min(cols) < 2 or max(rows) > height - 3 or max(cols) > width - 3:
            errors.append("every multi-cell component must expose a full radius-two ring")
    return errors


def python_mirror(grid: list[list[int]], halo_radius: Any) -> list[list[int]]:
    """Independent Python mirror, used only to cross-check Racket execution."""
    radius = _validate_radius(halo_radius)
    errors = validate_prototype_input(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    result = deepcopy(grid)
    for cells in _red_components(grid):
        if len(cells) < 2:
            continue
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        for row in range(max(0, min(rows) - radius), min(height, max(rows) + radius + 1)):
            for col in range(max(0, min(cols) - radius), min(width, max(cols) + radius + 1)):
                if result[row][col] == 0:
                    result[row][col] = 3
    return result


def _stream_rng(seed: int, stream: str) -> random.Random:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    digest = hashlib.sha256(f"{PROTOTYPE_VERSION}:{stream}:{seed}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def halo_radius_for_seed(seed: int) -> int:
    """Choose the hidden rule once from an episode-only deterministic stream."""
    return _stream_rng(seed, "rule").choice(ALLOWED_HALO_RADII)


def _translated(shape: tuple[tuple[int, int], ...], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + row, left + col) for row, col in shape}


def _expanded(cells: set[tuple[int, int]], radius: int, height: int, width: int) -> set[tuple[int, int]]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return {
        (row, col)
        for row in range(max(0, min(rows) - radius), min(height, max(rows) + radius + 1))
        for col in range(max(0, min(cols) - radius), min(width, max(cols) + radius + 1))
    }


def _sample_profile_input(
    rng: random.Random,
    height: int,
    width: int,
    shape: tuple[tuple[int, int], ...],
) -> list[list[int]]:
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    tops = list(range(2, height - shape_height - 1))
    lefts = list(range(2, width - shape_width - 1))
    if not tops or not lefts:
        raise RuntimeError("profile cannot expose a radius-two ring")
    cells = _translated(shape, rng.choice(tops), rng.choice(lefts))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in cells:
        grid[row][col] = 2

    forbidden = _expanded(cells, 2, height, width)
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in forbidden
    ]
    rng.shuffle(candidates)
    singleton_count = rng.randint(1, 3)
    singles: list[tuple[int, int]] = []
    for candidate in candidates:
        row, col = candidate
        if any(abs(row - other_row) + abs(col - other_col) == 1 for other_row, other_col in singles):
            continue
        singles.append(candidate)
        grid[row][col] = 2
        if len(singles) == singleton_count:
            break
    if len(singles) != singleton_count:
        raise RuntimeError("could not place isolated singleton contrast objects")
    errors = validate_prototype_input(grid)
    if errors:
        raise RuntimeError("sampled invalid prototype input: " + "; ".join(errors))
    if python_mirror(grid, 1) == python_mirror(grid, 2):
        raise RuntimeError("sampled input does not distinguish halo radii")
    return grid


def sample_inputs(seed: int) -> list[list[list[int]]]:
    """Draw four lawful inputs from a stream independent of the chosen rule."""
    rng = _stream_rng(seed, "inputs")
    return [
        _sample_profile_input(rng, height, width, shape)
        for _name, height, width, shape in PROFILES
    ]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _json_sha256(value: Any) -> str:
    return _sha256(_json_bytes(value))


def sample_episode(seed: int) -> dict[str, Any]:
    radius = halo_radius_for_seed(seed)
    inputs = sample_inputs(seed)
    return {
        "episode_id": "episode-" + _json_sha256(inputs)[:16],
        "seed": seed,
        "parameters": {"halo_radius": radius},
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
        found.setdefault(halo_radius_for_seed(seed), seed)
        if set(found) == set(ALLOWED_HALO_RADII):
            break
    if set(found) != set(ALLOWED_HALO_RADII):
        raise RuntimeError("could not find one deterministic seed per setting")
    return {
        "base_seed": base_seed,
        "examined_seeds": examined,
        "by_halo_radius": {str(radius): found[radius] for radius in ALLOWED_HALO_RADII},
        "seeds": [found[radius] for radius in ALLOWED_HALO_RADII],
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
    if set(predictions) != set(ALLOWED_HALO_RADII):
        raise ValueError("predictions must cover every declared halo_radius")
    if type(query_index) is not int or not 0 <= query_index < PAIR_COUNT:
        raise ValueError("query_index is out of range")
    if any(len(outputs) != PAIR_COUNT for outputs in predictions.values()):
        raise ValueError("each setting must predict exactly four pairs")
    demonstrations = [index for index in range(PAIR_COUNT) if index != query_index]
    rivals = []
    for radius in ALLOWED_HALO_RADII:
        if radius == chosen:
            continue
        mismatches = [
            index
            for index in demonstrations
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
                "halo_radius": radius,
                "status": status,
                "demonstration_mismatches": mismatches,
                "query_disagrees": query_disagrees,
            }
        )
    return {
        "chosen_halo_radius": chosen,
        "query_index": query_index,
        "demonstration_indices": demonstrations,
        "rivals": rivals,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _source_bindings() -> dict[str, str]:
    source = Path(__file__).resolve()
    readme = source.with_name("README.md")
    return {
        "prototype.py": _sha256(source.read_bytes()),
        "README.md": _sha256(readme.read_bytes()),
        "canonical_rule": _sha256(CANONICAL_RULE.encode()),
    }


def _private_canary() -> list[list[int]]:
    grid = [[0 for _ in range(9)] for _ in range(9)]
    grid[4][3] = grid[4][4] = 2
    grid[0][0] = 2
    return grid


def run_evidence(out: Path, *, base_seed: int, racket_path: str | None = None) -> dict[str, Any]:
    from arc_repl.isolated_verifier import verify_candidate

    out = out.resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    selection = select_seeds(base_seed)
    report: dict[str, Any] = {
        "schema": "arcpuzzles-parametric-prototype-report-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "running",
        "error": None,
        "parameters": {
            "halo_radius": {
                "allowed": list(ALLOWED_HALO_RADII),
                "default": DEFAULT_HALO_RADIUS,
                "selection": "one deterministic value per episode",
            }
        },
        "input_constraints": {
            "colors": [0, 2],
            "dimensions": "8..30 by 8..30",
            "multi_component_margin": 2,
            "required_objects": ["one multi-cell red component", "one or more red singletons"],
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
        for radius in ALLOWED_HALO_RADII:
            program = rule_source(radius)
            program_sha = _sha256(program.encode())
            rule_rel = f"private/rules/halo_radius_{radius}.rkt"
            receipt_rel = f"private/racket/halo_radius_{radius}.json"
            rule_path = out / rule_rel
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(program + "\n", encoding="utf-8")
            report["rules"].append(
                {
                    "parameters": {"halo_radius": radius},
                    "source": program,
                    "sha256": program_sha,
                    "path": rule_rel,
                    "execution_path": receipt_rel,
                    "canonical_default": radius == DEFAULT_HALO_RADIUS,
                }
            )
            canary_input = _private_canary()
            canary = {"input": canary_input, "output": python_mirror(canary_input, radius)}
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
                    f"Racket execution failed for halo_radius={radius}: {receipt.get('error')}"
                )
            predictions[radius] = receipt["test_outputs"]
            for row, observed in zip(execution_inputs, predictions[radius], strict=True):
                expected = python_mirror(row["input"], radius)
                if observed != expected:
                    _write_json(
                        out / "private/parity_failure.json",
                        {
                            "halo_radius": radius,
                            "input": row["input"],
                            "racket_output": observed,
                            "python_mirror": expected,
                        },
                    )
                    raise RuntimeError(f"Racket/Python mismatch at halo_radius={radius}")
                parity_matches += 1

        offset = 0
        rotation_rows: list[dict[str, Any]] = []
        for episode in episodes:
            chosen = episode["parameters"]["halo_radius"]
            episode_predictions = {
                radius: predictions[radius][offset : offset + PAIR_COUNT]
                for radius in ALLOWED_HALO_RADII
            }
            offset += PAIR_COUNT
            pairs = [
                {"input": grid, "output": output}
                for grid, output in zip(episode["inputs"], episode_predictions[chosen], strict=True)
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
                        for radius in ALLOWED_HALO_RADII
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
            for radius in ALLOWED_HALO_RADII
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
                ) == len(ALLOWED_HALO_RADII),
            },
        )
        rival_rows = [rival for rotation in rotation_rows for rival in rotation["rivals"]]
        report["summary"] = {
            "episodes": len(episodes),
            "episode_pairs": len(execution_inputs),
            "racket_rule_applications": len(execution_inputs) * len(ALLOWED_HALO_RADII),
            "racket_canaries": len(ALLOWED_HALO_RADII),
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
    _write_json(
        out / "manifest.json",
        {
            "schema": "parametric-evidence-manifest-v1",
            "status": report["status"],
            "task_id": TASK_ID,
            "report": "report.json",
            "report_sha256": _sha256((out / "report.json").read_bytes()),
            "public_challenges": [row["public_path"] for row in report.get("episodes", [])],
            "private_evidence": [row["private_path"] for row in report.get("episodes", [])],
        },
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base-seed", type=int, default=20261020)
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

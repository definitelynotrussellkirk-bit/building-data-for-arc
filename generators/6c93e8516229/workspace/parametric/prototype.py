"""Proposed episode-level junction-degree variant for task 6c93e8516229.

The canonical task classifies each green component from local topology.  This
prototype keeps that complete reasoning pipeline and varies one nearby semantic
choice once per episode: whether a degree-3 or degree-4 junction is the red
class.  The canonical default is degree 3.  It is bounded authoring evidence,
not a production generator API or an approval claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "6c93e8516229"
ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
JUNCTION_DEGREES = (3, 4)
PARAMETER = {
    "name": "junction_degree",
    "values": [3, 4],
    "default": 3,
    "input_constraints": (
        "unchanged canonical tree-component grammar; demonstrations include "
        "both degree-3 and degree-4 junctions"
    ),
}
STATUS = "proposed prototype; canonical production behavior is unchanged"
EXAMPLES_NEEDED = 3
DIFFICULTY = "medium"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_record() -> dict[str, Any]:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                rows.append(record)
    if not rows:
        raise KeyError(f"canonical task {TASK_ID} not found")
    programs = {record.get("program_solution") for record in rows}
    if len(programs) != 1:
        raise ValueError(f"canonical rows for {TASK_ID} disagree on program_solution")
    return rows[0]


def _validate_degree(junction_degree: int) -> None:
    if type(junction_degree) is not int or junction_degree not in JUNCTION_DEGREES:
        raise ValueError(f"junction_degree must be one of {JUNCTION_DEGREES}")


def program_for(junction_degree: int = 3) -> str:
    """Materialize exact executable Racket for one parameter setting."""
    _validate_degree(junction_degree)
    canonical = canonical_record()["program_solution"]
    if junction_degree == 3:
        return canonical
    needle = "(= nbr-count 3)"
    if canonical.count(needle) != 1:
        raise ValueError("canonical junction predicate changed; review manually")
    return canonical.replace(needle, f"(= nbr-count {junction_degree})", 1)


def execute(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute exact ``(rule! ...)`` text through the bundled Racket bridge."""
    if not isinstance(program, str) or not program.lstrip().startswith("(rule!"):
        raise ValueError("program must be exact (rule! ...) Racket text")
    errors = GEN.self_check(grid)
    if errors:
        raise ValueError("prototype input violates canonical grammar: " + "; ".join(errors))
    bridge.define_grid("parametric_grid", grid)
    callable_rule = strip_rule_wrapper(strip_line_comments(program))
    value = bridge.eval_text(f"({callable_rule} parametric_grid)")
    if not isinstance(value, list):
        raise TypeError(f"Racket returned {type(value).__name__}, expected a grid")
    return value


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def episode_inputs(seed: int) -> list[list[list[int]]]:
    """Return three demonstrations and one query with both junction types.

    Even sample indices select the generator's degree-4 plus witness, while the
    ordinary red class always supplies a degree-3 T.  Thus every input remains
    canonical-lawful and each demonstration distinguishes the two settings.
    """
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative literal integer")
    input_seed = 6_093_851_000 + seed
    start = seed * 32
    inputs = [
        GEN.generate(input_seed, start + 2 * offset, difficulty=DIFFICULTY)
        for offset in range(EXAMPLES_NEEDED + 1)
    ]
    for index, grid in enumerate(inputs):
        stats = [GEN._shape_stats(cells) for cells in GEN._components(grid)]
        if not any(item["degree3"] for item in stats):
            raise AssertionError(f"episode input {index} lacks a degree-3 witness")
        if not any(item["degree4"] for item in stats):
            raise AssertionError(f"episode input {index} lacks a degree-4 witness")
    return inputs


def generate_episode(
    seed: int,
    bridge: RacketBridge,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one source-bound episode with the hidden rule fixed once."""
    inputs = episode_inputs(seed)
    selected = JUNCTION_DEGREES[seed % len(JUNCTION_DEGREES)]
    programs = {degree: program_for(degree) for degree in JUNCTION_DEGREES}
    outputs = {
        degree: [execute(bridge, program, grid) for grid in inputs]
        for degree, program in programs.items()
    }

    canonical_outputs = outputs[3]
    for index, (grid, output) in enumerate(zip(inputs, canonical_outputs)):
        if output != GEN._solve_canonical(grid):
            raise AssertionError(
                f"canonical Racket default diverges from the independent mirror at {index}"
            )

    selected_outputs = outputs[selected]
    public = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(
                inputs[:EXAMPLES_NEEDED], selected_outputs[:EXAMPLES_NEEDED]
            )
        ],
        "test": [{"input": inputs[-1]}],
    }

    rival_checks: dict[str, Any] = {}
    for degree in JUNCTION_DEGREES:
        matches = [
            candidate == expected
            for candidate, expected in zip(
                outputs[degree][:EXAMPLES_NEEDED],
                selected_outputs[:EXAMPLES_NEEDED],
            )
        ]
        rival_checks[str(degree)] = {
            "matches_all_demonstrations": all(matches),
            "distinguishing_demo_indices": [
                index for index, matches_selected in enumerate(matches)
                if not matches_selected
            ],
            "query_matches_selected": outputs[degree][-1] == selected_outputs[-1],
        }

    rival = 4 if selected == 3 else 3
    if rival_checks[str(rival)]["matches_all_demonstrations"]:
        raise AssertionError("demonstrations do not identify junction_degree")
    if rival_checks[str(rival)]["query_matches_selected"]:
        raise AssertionError("query does not distinguish junction_degree settings")

    private = {
        "schema": "6c93e8516229-junction-degree-evidence-v1",
        "status": STATUS,
        "seed": seed,
        "parameter": {"junction_degree": selected},
        "parameter_contract": PARAMETER,
        "difficulty": DIFFICULTY,
        "generator_source": str(GENERATOR_SOURCE.relative_to(ROOT)),
        "generator_sha256": GENERATOR_SHA256,
        "canonical_rule_hash": GEN.RULE_HASH,
        "program": programs[selected],
        "program_sha256": sha256_bytes(programs[selected].encode()),
        "all_program_sha256": {
            str(degree): sha256_bytes(program.encode())
            for degree, program in programs.items()
        },
        "input_sha256": [_grid_hash(grid) for grid in inputs],
        "query_answers": [selected_outputs[-1]],
        "rival_checks": rival_checks,
        "runtime_identity": bridge.runtime_identity,
        "limitations": [
            "prototype only; it does not alter the canonical generator API, rule hash, or approval state",
            "bounded evidence covers two junction-degree settings and the listed seeds",
            "the hidden degree is inferred from demonstrations rather than encoded in query inputs",
            "the input grammar remains the generator's finite tree-prototype distribution",
        ],
    }
    return public, private


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(
    out_dir: str | Path,
    *,
    seeds: Iterable[int] = (0, 1),
) -> dict[str, Any]:
    """Execute both settings and retain clean public plus private evidence."""
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"evidence directory already exists and is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)
    seed_values = list(seeds)
    if not seed_values:
        raise ValueError("at least one evidence seed is required")
    if any(type(seed) is not int or seed < 0 for seed in seed_values):
        raise ValueError("evidence seeds must be non-negative literal integers")

    program_hashes = {}
    for degree in JUNCTION_DEGREES:
        program = program_for(degree)
        program_hashes[str(degree)] = sha256_bytes(program.encode())
        rule_path = out / "rules" / f"junction-degree-{degree}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(program, encoding="utf-8")

    episode_receipts = []
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=64) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seed_values:
            public, private = generate_episode(seed, bridge)
            _write_json(out / "public" / f"seed-{seed}.json", public)
            _write_json(out / "private" / f"seed-{seed}.json", private)
            episode_receipts.append(
                {
                    "seed": seed,
                    "junction_degree": private["parameter"]["junction_degree"],
                    "public_sha256": sha256_bytes(
                        json.dumps(public, sort_keys=True, separators=(",", ":")).encode()
                    ),
                    "private_sha256": sha256_bytes(
                        json.dumps(private, sort_keys=True, separators=(",", ":")).encode()
                    ),
                    "rival_checks": private["rival_checks"],
                }
            )

    source = Path(__file__)
    manifest = {
        "schema": "6c93e8516229-junction-degree-manifest-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": PARAMETER,
        "program_sha256": program_hashes,
        "prototype_source": str(source.relative_to(ROOT)),
        "prototype_sha256": sha256_bytes(source.read_bytes()),
        "generator_source": str(GENERATOR_SOURCE.relative_to(ROOT)),
        "generator_sha256": GENERATOR_SHA256,
        "runtime_identity": runtime_identity,
        "episodes": episode_receipts,
        "recommended_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric/junction-degree",
            "--seeds",
            "0",
            "1",
        ],
        "limitations": [
            "finite two-seed evidence, not exhaustive proof over all generated inputs",
            "variant remains proposed and separate from canonical production selection",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="new evidence directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    args = parser.parse_args(argv)
    manifest = write_evidence(args.out, seeds=args.seeds)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

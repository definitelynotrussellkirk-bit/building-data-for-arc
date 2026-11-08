"""Proposed episode-level cycle-direction variant for task a4863798ed70.

This is bounded authoring evidence, not a production generator API and not an
approval claim.  The canonical ``generate`` function remains fixed to the
canonical clockwise Racket authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root, load_selected_generator
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper


TASK_ID = "a4863798ed70"
ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
DIRECTIONS = ("clockwise", "counterclockwise")
PARAMETER = {
    "name": "cycle_direction",
    "values": list(DIRECTIONS),
    "default": "clockwise",
    "input_constraints": "unchanged; 3..5 distinct-color framed icons",
}
STATUS = "proposed prototype; not production-approved"
PROFILE = "canonical_4x5_22x21"
DIFFICULTY = "medium"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_record() -> dict[str, Any]:
    """Return the unique canonical ledger row for this task."""
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if not rows:
        raise KeyError(TASK_ID)
    programs = {row.get("program_solution") for row in rows}
    if len(programs) != 1:
        raise ValueError(
            f"canonical variants for {TASK_ID} disagree on program_solution"
        )
    return rows[0]


def program_for(cycle_direction: str = "clockwise") -> str:
    """Return exact executable Racket for one bounded direction setting."""
    if cycle_direction not in DIRECTIONS:
        raise ValueError(f"cycle_direction must be one of {DIRECTIONS}")
    canonical = canonical_record()["program_solution"]
    if cycle_direction == "clockwise":
        return canonical

    expression = "(mod (+ i 1) n)"
    if canonical.count(expression) != 1:
        raise ValueError("canonical direction expression changed; review prototype manually")
    alternative = canonical.replace(
        ";; Frame i receives the icon color from the next clockwise frame.",
        ";; Frame i receives the icon color from the previous clockwise frame.",
        1,
    ).replace(expression, "(mod (+ i (- n 1)) n)", 1)
    return alternative


def execute(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute exact ``(rule! ...)`` text through the protected Racket bridge."""
    if not isinstance(program, str) or not program.lstrip().startswith("(rule!"):
        raise ValueError("program must be exact (rule! ...) Racket text")
    errors = GEN.self_check(grid)
    if errors:
        raise ValueError("prototype input violates canonical grammar: " + "; ".join(errors))
    bridge.define_grid("prototype_grid", grid)
    callable_rule = strip_rule_wrapper(strip_line_comments(program))
    value = bridge.eval_text(f"({callable_rule} prototype_grid)")
    if not isinstance(value, list):
        raise TypeError(f"Racket returned non-grid value {type(value).__name__}")
    return value


def _episode_inputs(seed: int) -> list[list[list[int]]]:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    # Four frames make the two directions observably distinct.  The semantic
    # parameter is selected once below; only ordinary input draws vary here.
    input_seed = 486_379_800 + seed
    base_index = seed * (GEN.EXAMPLES_NEEDED + 1)
    return [
        GEN.generate(
            input_seed,
            base_index + offset,
            difficulty=DIFFICULTY,
            scene_profile=PROFILE,
        )
        for offset in range(GEN.EXAMPLES_NEEDED + 1)
    ]


def generate_episode(seed: int, bridge) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one complete challenge with one hidden direction fixed per episode."""
    inputs = _episode_inputs(seed)
    chosen = DIRECTIONS[seed % len(DIRECTIONS)]
    programs = {direction: program_for(direction) for direction in DIRECTIONS}
    executed: dict[str, list[list[list[int]]]] = {
        direction: [execute(bridge, program, grid) for grid in inputs]
        for direction, program in programs.items()
    }

    # Independently pin the default prototype to the production task mirror.
    for grid, output in zip(inputs, executed["clockwise"]):
        if output != GEN.rule_mirror(grid):
            raise AssertionError("canonical Racket default diverges from selected generator mirror")

    selected_outputs = executed[chosen]
    public = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(inputs[: GEN.EXAMPLES_NEEDED], selected_outputs[: GEN.EXAMPLES_NEEDED])
        ],
        "test": [{"input": inputs[-1]}],
    }

    rival_checks = {}
    for direction in DIRECTIONS:
        matches = [
            candidate == expected
            for candidate, expected in zip(
                executed[direction][: GEN.EXAMPLES_NEEDED],
                selected_outputs[: GEN.EXAMPLES_NEEDED],
            )
        ]
        rival_checks[direction] = {
            "matches_all_demonstrations": all(matches),
            "distinguishing_demo_indices": [index for index, match in enumerate(matches) if not match],
            "query_matches_selected": executed[direction][-1] == selected_outputs[-1],
        }

    rival = next(direction for direction in DIRECTIONS if direction != chosen)
    if rival_checks[rival]["matches_all_demonstrations"]:
        raise AssertionError("demonstrations do not identify the hidden cycle direction")
    if executed[rival][-1] == selected_outputs[-1]:
        raise AssertionError("query does not distinguish the cycle-direction settings")

    private = {
        "schema": "a4863798ed70-cycle-direction-evidence-v1",
        "status": STATUS,
        "seed": seed,
        "parameter": {"cycle_direction": chosen},
        "parameter_contract": PARAMETER,
        "profile": PROFILE,
        "difficulty": DIFFICULTY,
        "generator_source": str(GENERATOR_SOURCE.relative_to(ROOT)),
        "generator_sha256": GENERATOR_SHA256,
        "canonical_rule_hash": GEN.RULE_HASH,
        "program": programs[chosen],
        "program_sha256": digest(programs[chosen].encode()),
        "all_program_sha256": {
            direction: digest(program.encode()) for direction, program in programs.items()
        },
        "query_answers": [selected_outputs[-1]],
        "rival_checks": rival_checks,
        "limitations": [
            "prototype only; it does not change the canonical generator API or approval state",
            "evidence uses two directions, one four-frame profile, medium difficulty, and the listed seeds",
            "the hidden direction is inferred from demonstrations and is not encoded in the query input",
        ],
    }
    return public, private


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence(out_dir: str | Path, *, seeds: Iterable[int] = (0, 1)) -> dict[str, Any]:
    """Materialize public/private episodes, exact rules, and a bounded manifest."""
    from arc_repl.racket_bridge import RacketBridge

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seed_values = list(seeds)
    if not seed_values:
        raise ValueError("at least one evidence seed is required")
    if any(type(seed) is not int or seed < 0 for seed in seed_values):
        raise ValueError("evidence seeds must be non-negative literal integers")

    program_hashes = {}
    for direction in DIRECTIONS:
        program = program_for(direction)
        program_hashes[direction] = digest(program.encode())
        path = out / "rules" / f"{direction}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program, encoding="utf-8")

    episode_receipts = []
    with RacketBridge() as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seed_values:
            public, private = generate_episode(seed, bridge)
            _write_json(out / "public" / f"seed-{seed}.json", public)
            _write_json(out / "private" / f"seed-{seed}.json", private)
            episode_receipts.append(
                {
                    "seed": seed,
                    "cycle_direction": private["parameter"]["cycle_direction"],
                    "public_sha256": digest(
                        json.dumps(public, sort_keys=True, separators=(",", ":")).encode()
                    ),
                    "private_sha256": digest(
                        json.dumps(private, sort_keys=True, separators=(",", ":")).encode()
                    ),
                }
            )

    source = Path(__file__)
    manifest = {
        "schema": "a4863798ed70-cycle-direction-manifest-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameter": PARAMETER,
        "program_sha256": program_hashes,
        "prototype_source": str(source.relative_to(ROOT)),
        "prototype_sha256": digest(source.read_bytes()),
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
            "../checks/parametric/cycle-direction-v1",
            "--seeds",
            *[str(seed) for seed in seed_values],
        ],
        "limitations": [
            "bounded authoring evidence only; no production parametric API is added",
            "public challenges intentionally omit hidden parameters, Racket text, and query answers",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="evidence output directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    args = parser.parse_args(argv)
    manifest = write_evidence(args.out, seeds=args.seeds)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

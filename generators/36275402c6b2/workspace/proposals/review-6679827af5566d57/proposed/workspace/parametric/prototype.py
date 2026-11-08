"""Proposed episode-level border-policy variant for task 36275402c6b2.

The canonical task crops the largest component's bounding box and applies every
outside ``(replacement, source)`` pair to the crop.  This prototype preserves
that pipeline and varies one nearby semantic choice once per episode: whether
source cells on the crop border are recolored or preserved.  The canonical
default is ``recolor``.  It is bounded authoring evidence, not a production API
or an approval claim.
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

TASK_ID = "36275402c6b2"
ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BORDER_POLICIES = ("recolor", "preserve")
PARAMETER = {
    "name": "border_policy",
    "values": ["recolor", "preserve"],
    "default": "recolor",
    "input_constraints": (
        "unchanged canonical rectangle-and-legend grammar; every episode input "
        "contains a non-corner border source witness"
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


def _validate_policy(border_policy: str) -> None:
    if type(border_policy) is not str or border_policy not in BORDER_POLICIES:
        raise ValueError(f"border_policy must be one of {BORDER_POLICIES}")


def program_for(border_policy: str = "recolor") -> str:
    """Materialize exact executable Racket for one parameter setting."""
    _validate_policy(border_policy)
    canonical = canonical_record()["program_solution"]
    if border_policy == "recolor":
        return canonical

    needle = "(if mapping (first mapping) v)"
    if canonical.count(needle) != 1:
        raise ValueError("canonical recoloring expression changed; review manually")
    replacement = """(if (or (= r 0)
                                                             (= c 0)
                                                             (= r (- rect-h 1))
                                                             (= c (- rect-w 1)))
                                                         v
                                                         (if mapping (first mapping) v))"""
    return canonical.replace(needle, replacement, 1)


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
    """Return three demonstrations and one query with border-source witnesses.

    Odd sample indices select the production generator's border-and-side profile.
    Every input is therefore canonical-lawful and distinguishes recoloring all
    sources from preserving source cells on the crop border.
    """
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative literal integer")
    input_seed = 362_754_020 + seed
    start = seed * 32
    inputs = [
        GEN.generate(
            input_seed,
            2 * (start + offset) + 1,
            difficulty=DIFFICULTY,
        )
        for offset in range(EXAMPLES_NEEDED + 1)
    ]
    for index, grid in enumerate(inputs):
        errors = GEN.self_check(grid)
        if errors:
            raise AssertionError(
                f"episode input {index} violates canonical grammar: {'; '.join(errors)}"
            )
        if not GEN._has_border_source(grid):
            raise AssertionError(f"episode input {index} lacks a border-source witness")
    return inputs


def generate_episode(
    seed: int,
    bridge: RacketBridge,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build one source-bound episode with the hidden rule fixed once."""
    inputs = episode_inputs(seed)
    selected = BORDER_POLICIES[seed % len(BORDER_POLICIES)]
    programs = {policy: program_for(policy) for policy in BORDER_POLICIES}
    outputs = {
        policy: [execute(bridge, program, grid) for grid in inputs]
        for policy, program in programs.items()
    }

    for index, grid in enumerate(inputs):
        if outputs["recolor"][index] != GEN.rule_mirror(grid):
            raise AssertionError(
                f"canonical Racket default diverges from the independent mirror at {index}"
            )
        if outputs["preserve"][index] != GEN._rival_preserve_border_sources(grid):
            raise AssertionError(
                f"preserve-border Racket variant diverges from its independent mirror at {index}"
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
    for policy in BORDER_POLICIES:
        matches = [
            candidate == expected
            for candidate, expected in zip(
                outputs[policy][:EXAMPLES_NEEDED],
                selected_outputs[:EXAMPLES_NEEDED],
            )
        ]
        rival_checks[policy] = {
            "matches_all_demonstrations": all(matches),
            "distinguishing_demo_indices": [
                index for index, matches_selected in enumerate(matches)
                if not matches_selected
            ],
            "query_matches_selected": outputs[policy][-1] == selected_outputs[-1],
        }

    rival = "preserve" if selected == "recolor" else "recolor"
    if rival_checks[rival]["matches_all_demonstrations"]:
        raise AssertionError("demonstrations do not identify border_policy")
    if rival_checks[rival]["query_matches_selected"]:
        raise AssertionError("query does not distinguish border_policy settings")

    private = {
        "schema": "36275402c6b2-border-policy-evidence-v1",
        "status": STATUS,
        "seed": seed,
        "parameter": {"border_policy": selected},
        "parameter_contract": PARAMETER,
        "difficulty": DIFFICULTY,
        "generator_source": str(GENERATOR_SOURCE.relative_to(ROOT)),
        "generator_sha256": GENERATOR_SHA256,
        "canonical_rule_hash": GEN.RULE_HASH,
        "program": programs[selected],
        "program_sha256": sha256_bytes(programs[selected].encode()),
        "all_program_sha256": {
            policy: sha256_bytes(program.encode())
            for policy, program in programs.items()
        },
        "input_sha256": [_grid_hash(grid) for grid in inputs],
        "query_answers": [selected_outputs[-1]],
        "rival_checks": rival_checks,
        "runtime_identity": bridge.runtime_identity,
        "limitations": [
            "prototype only; it does not alter the canonical generator API, rule hash, or approval state",
            "bounded evidence covers two border-policy settings and the listed seeds",
            "the hidden policy is inferred from demonstrations rather than encoded in query inputs",
            "episode inputs intentionally use the generator's border-and-side schedule profile",
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
    for policy in BORDER_POLICIES:
        program = program_for(policy)
        program_hashes[policy] = sha256_bytes(program.encode())
        rule_path = out / "rules" / f"border-policy-{policy}.rkt"
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
                    "border_policy": private["parameter"]["border_policy"],
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
        "schema": "36275402c6b2-border-policy-manifest-v1",
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
            "../checks/parametric/border-policy",
            "--seeds",
            "0",
            "1",
        ],
        "limitations": [
            "finite listed-seed evidence, not exhaustive proof over all generated inputs",
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

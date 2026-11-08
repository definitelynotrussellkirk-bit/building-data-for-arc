#!/usr/bin/env python3
"""Executable proposed depth-policy variant for the crossing-bars ARC task.

This is finite review evidence, not a production generator or an approved task
variant.  The episode-level ``depth_policy`` parameter changes only which bar
owns the overlap in the output.  The default ``toggle`` setting preserves the
canonical Racket source byte-for-byte.  Every retained label and rival
prediction is executed by the packet's protected Racket bridge.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "2f0a4d589c58"
PROTOTYPE_VERSION = "proposed-depth-policy-v1"
DEPTH_POLICIES = ("toggle", "horizontal_front", "vertical_front")
DEFAULT_DEPTH_POLICY = "toggle"
CANONICAL_TARGET = "(if (and rd cd (!= rd cd)) (if (= v rd) cd rd) v)"
_POLICY_REPLACEMENTS = {
    "toggle": CANONICAL_TARGET,
    "horizontal_front": "(if (and rd cd (!= rd cd)) rd v)",
    "vertical_front": "(if (and rd cd (!= rd cd)) cd v)",
}


def _sha256(value: bytes | str) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_policy(policy: Any) -> str:
    if type(policy) is not str or policy not in DEPTH_POLICIES:
        raise ValueError("depth_policy must be toggle, horizontal_front, or vertical_front")
    return policy


def canonical_program(*, root: Path | str | None = None) -> str:
    """Load the one canonical Racket program for this content ID."""
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    programs: list[str] = []
    with canonical_path(resolved_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str):
                    raise ValueError("canonical row has no Racket program_solution")
                programs.append(source)
    if len(programs) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}, got {len(programs)}")
    if programs[0].count(CANONICAL_TARGET) != 1:
        raise ValueError("canonical rule does not contain exactly one depth-toggle site")
    return programs[0]


def instantiate(
    canonical: str,
    depth_policy: str = DEFAULT_DEPTH_POLICY,
) -> str:
    """Instantiate one policy while preserving the canonical default exactly."""
    policy = _validate_policy(depth_policy)
    if not isinstance(canonical, str):
        raise TypeError("canonical program must be text")
    if canonical.count(CANONICAL_TARGET) != 1:
        raise ValueError("source must contain exactly one canonical depth-toggle site")
    if policy == DEFAULT_DEPTH_POLICY:
        return canonical
    return canonical.replace(CANONICAL_TARGET, _POLICY_REPLACEMENTS[policy], 1)


def _paint_fixture(
    height: int,
    width: int,
    horizontal_start: int,
    horizontal_thickness: int,
    vertical_start: int,
    vertical_thickness: int,
    horizontal_color: int,
    vertical_color: int,
    occluder: str,
) -> list[list[int]]:
    grid = [[0 for _ in range(width)] for _ in range(height)]
    horizontal_rows = range(horizontal_start, horizontal_start + horizontal_thickness)
    vertical_cols = range(vertical_start, vertical_start + vertical_thickness)
    for row in horizontal_rows:
        for column in range(width):
            grid[row][column] = horizontal_color
    for column in vertical_cols:
        for row in range(height):
            grid[row][column] = vertical_color
    overlap_color = horizontal_color if occluder == "horizontal" else vertical_color
    for row in horizontal_rows:
        for column in vertical_cols:
            grid[row][column] = overlap_color
    return grid


def fixture_inputs(seed: int) -> list[list[list[int]]]:
    """Return four authored lawful inputs, with palettes varied by seed.

    Geometry is intentionally fixed and transparent.  The first three inputs
    contain both possible input occluders, making every non-selected parameter
    setting demonstrably wrong before the query.  The fourth (query) input has
    a vertical occluder and a multi-cell overlap.
    """
    _validate_seed(seed)
    rng = random.Random(f"{TASK_ID}:{PROTOTYPE_VERSION}:fixtures:{seed}")
    specifications = (
        # h, w, h_start, h_thick, v_start, v_thick, input occluder
        (8, 7, 3, 1, 2, 1, "horizontal"),
        (7, 9, 3, 1, 2, 2, "vertical"),
        (11, 6, 0, 3, 4, 2, "horizontal"),
        (13, 13, 10, 2, 0, 1, "vertical"),
    )
    fixtures: list[list[list[int]]] = []
    for spec in specifications:
        horizontal_color = rng.randint(1, 9)
        offset = rng.randint(1, 8)
        vertical_color = ((horizontal_color - 1 + offset) % 9) + 1
        fixtures.append(
            _paint_fixture(
                *spec[:-1],
                horizontal_color,
                vertical_color,
                spec[-1],
            )
        )
    return fixtures


def _crossing_facts(grid: Any) -> dict[str, Any]:
    clean = normalize_grid(grid)
    height, width = len(clean), len(clean[0])
    horizontal_rows = [
        row for row in range(height) if all(clean[row][column] != 0 for column in range(width))
    ]
    vertical_cols = [
        column for column in range(width) if all(clean[row][column] != 0 for row in range(height))
    ]
    if not horizontal_rows or not vertical_cols:
        raise ValueError("fixture must contain crossing full-span bars")
    row_set, col_set = set(horizontal_rows), set(vertical_cols)
    horizontal_flank = {
        clean[row][column]
        for row in horizontal_rows
        for column in range(width)
        if column not in col_set
    }
    vertical_flank = {
        clean[row][column]
        for column in vertical_cols
        for row in range(height)
        if row not in row_set
    }
    overlap = {
        clean[row][column] for row in horizontal_rows for column in vertical_cols
    }
    if len(horizontal_flank) != 1 or len(vertical_flank) != 1 or len(overlap) != 1:
        raise ValueError("fixture does not have uniform bar flanks and overlap")
    horizontal_color = next(iter(horizontal_flank))
    vertical_color = next(iter(vertical_flank))
    overlap_color = next(iter(overlap))
    if (
        0 in (horizontal_color, vertical_color, overlap_color)
        or horizontal_color == vertical_color
        or overlap_color not in (horizontal_color, vertical_color)
    ):
        raise ValueError("fixture colors do not encode two bars and one front bar")
    return {
        "grid": clean,
        "horizontal_rows": horizontal_rows,
        "vertical_cols": vertical_cols,
        "horizontal_color": horizontal_color,
        "vertical_color": vertical_color,
        "overlap_color": overlap_color,
        "input_occluder": (
            "horizontal" if overlap_color == horizontal_color else "vertical"
        ),
    }


def python_apply(grid: Any, depth_policy: str = DEFAULT_DEPTH_POLICY) -> list[list[int]]:
    """Independent, compact oracle used only to check Racket executions."""
    policy = _validate_policy(depth_policy)
    facts = _crossing_facts(grid)
    output = copy.deepcopy(facts["grid"])
    if policy == "horizontal_front":
        output_color = facts["horizontal_color"]
    elif policy == "vertical_front":
        output_color = facts["vertical_color"]
    else:
        output_color = (
            facts["vertical_color"]
            if facts["overlap_color"] == facts["horizontal_color"]
            else facts["horizontal_color"]
        )
    for row in facts["horizontal_rows"]:
        for column in facts["vertical_cols"]:
            output[row][column] = output_color
    return output


def execute(
    bridge: RacketBridge,
    program: str,
    grid: Any,
) -> list[list[int]]:
    """Execute the actual instantiated Racket program on one normalized grid."""
    if not isinstance(bridge, RacketBridge):
        raise TypeError("bridge must be a live RacketBridge")
    if not isinstance(program, str) or not program.lstrip().startswith("(rule!"):
        raise ValueError("program must be a (rule! ...) Racket source string")
    clean = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in clean
    ) + ")"
    result = bridge.eval_text(f"({strip_rule_wrapper(program)} {literal})")
    return normalize_grid(result)


def parameters(seed: int) -> dict[str, str]:
    """Draw exactly one episode-level parameter from a seed-local RNG."""
    _validate_seed(seed)
    rng = random.Random(f"{TASK_ID}:{PROTOTYPE_VERSION}:policy:{seed}")
    return {"depth_policy": rng.choice(DEPTH_POLICIES)}


def representative_seeds() -> dict[str, int]:
    """Return the first small seed selecting each policy."""
    result: dict[str, int] = {}
    for seed in range(10_000):
        policy = parameters(seed)["depth_policy"]
        result.setdefault(policy, seed)
        if len(result) == len(DEPTH_POLICIES):
            return {policy: result[policy] for policy in DEPTH_POLICIES}
    raise RuntimeError("failed to find representative seeds for every depth policy")


def episode(seed: int, canonical: str, bridge: RacketBridge) -> dict[str, Any]:
    """Build one private labeled episode and its explicit parameter rivals."""
    selected = parameters(seed)["depth_policy"]
    inputs = fixture_inputs(seed)
    programs = {policy: instantiate(canonical, policy) for policy in DEPTH_POLICIES}
    outputs: dict[str, list[list[list[int]]]] = {}
    for policy, source in programs.items():
        policy_outputs = [execute(bridge, source, grid) for grid in inputs]
        expected = [python_apply(grid, policy) for grid in inputs]
        if policy_outputs != expected:
            raise AssertionError(f"Racket/Python mismatch for depth_policy={policy}")
        outputs[policy] = policy_outputs

    pairs = [
        {
            "fixture_index": index,
            "input_occluder": _crossing_facts(grid)["input_occluder"],
            "input": grid,
            "output": outputs[selected][index],
            "input_sha256": _sha256(json.dumps(grid, separators=(",", ":"))),
            "output_sha256": _sha256(
                json.dumps(outputs[selected][index], separators=(",", ":"))
            ),
        }
        for index, grid in enumerate(inputs)
    ]
    rivals = []
    for policy in DEPTH_POLICIES:
        if policy == selected:
            continue
        demo_differences = [
            index for index in range(3) if outputs[policy][index] != outputs[selected][index]
        ]
        query_differs = outputs[policy][3] != outputs[selected][3]
        if query_differs and not demo_differences:
            raise AssertionError(
                f"query-changing rival {policy} is not refuted by demonstrations"
            )
        rivals.append(
            {
                "depth_policy": policy,
                "program_sha256": _sha256(programs[policy]),
                "demo_differences": demo_differences,
                "query_differs": query_differs,
                "status": (
                    "refuted_by_demonstrations"
                    if demo_differences
                    else "matches_selected_episode"
                ),
                "train_predictions": outputs[policy][:3],
                "query_predictions": outputs[policy][3:],
            }
        )

    selected_program = programs[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "status": "prototype",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {"depth_policy": selected},
        "parameter_selection": "one seed-local RNG choice before any pair",
        "program": selected_program,
        "program_sha256": _sha256(selected_program),
        "default_program_exact": instantiate(canonical) == canonical,
        "label_authority": "protected Racket bridge",
        "racket_evaluations": len(DEPTH_POLICIES) * len(inputs),
        "train": pairs[:3],
        "test": pairs[3:],
        "rivals": rivals,
    }


def public_challenge(private_episode: dict[str, Any]) -> dict[str, Any]:
    """Allowlist a public challenge; never copy private query labels."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in private_episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in private_episode["test"]
        ],
    }


def materialize(out: Path | str) -> dict[str, Any]:
    """Write a finite, reproducible public/private evidence bundle."""
    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        canonical = canonical_program()
        seeds = representative_seeds()
        rule_rows = []
        for policy in DEPTH_POLICIES:
            source = instantiate(canonical, policy)
            rule_path = destination / "private" / "rules" / f"{policy}.rkt"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_bytes(source.encode("utf-8"))
            rule_rows.append(
                {
                    "depth_policy": policy,
                    "path": str(rule_path.relative_to(destination)),
                    "sha256": _sha256(rule_path.read_bytes()),
                    "canonical_exact": policy == DEFAULT_DEPTH_POLICY and source == canonical,
                }
            )

        episode_rows = []
        private_episodes = []
        with RacketBridge() as bridge:
            for policy in DEPTH_POLICIES:
                seed = seeds[policy]
                private = episode(seed, canonical, bridge)
                if private["parameters"]["depth_policy"] != policy:
                    raise AssertionError("representative seed selected the wrong policy")
                public = public_challenge(private)
                private_path = destination / "private" / f"episode-{policy}.json"
                public_path = destination / "public" / f"episode-{policy}.json"
                _write_json(private_path, private)
                _write_json(public_path, public)
                private_episodes.append(private)
                episode_rows.append(
                    {
                        "depth_policy": policy,
                        "seed": seed,
                        "private_path": str(private_path.relative_to(destination)),
                        "public_path": str(public_path.relative_to(destination)),
                        "program_sha256": private["program_sha256"],
                        "rivals": [
                            {
                                "depth_policy": rival["depth_policy"],
                                "demo_differences": rival["demo_differences"],
                                "query_differs": rival["query_differs"],
                                "status": rival["status"],
                            }
                            for rival in private["rivals"]
                        ],
                    }
                )

        witness_inputs = fixture_inputs(20261020)[:2]
        witness = {
            "description": "one horizontal-front and one vertical-front input",
            "inputs": witness_inputs,
            "outputs_by_policy": {
                policy: [python_apply(grid, policy) for grid in witness_inputs]
                for policy in DEPTH_POLICIES
            },
        }
        _write_json(destination / "private" / "witness.json", witness)

        source_root = Path(__file__).resolve().parents[3]
        source_paths = [
            Path(__file__).resolve(),
            Path(__file__).resolve().parent / "README.md",
            source_root / TASK_ID / "tests" / "test_parametric_depth_policy.py",
        ]
        source_rows = [
            {
                "path": str(path),
                "sha256": _sha256(path.read_bytes()),
            }
            for path in source_paths
            if path.is_file()
        ]
        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "status": "prototype",
            "approved": False,
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "parameter": {
                "name": "depth_policy",
                "allowed_values": list(DEPTH_POLICIES),
                "default": DEFAULT_DEPTH_POLICY,
                "draw_scope": "once per episode",
                "changes_input_constraints": False,
            },
            "default_program_exact": instantiate(canonical) == canonical,
            "canonical_program_sha256": _sha256(canonical),
            "runtime": racket_runtime_status(),
            "rules": rule_rows,
            "episodes": episode_rows,
            "sources": source_rows,
            "counts": {
                "episodes": len(private_episodes),
                "train_pairs": sum(len(row["train"]) for row in private_episodes),
                "query_pairs": sum(len(row["test"]) for row in private_episodes),
                "racket_labels_and_rival_predictions": sum(
                    row["racket_evaluations"] for row in private_episodes
                ),
                "settings_exercised": len(DEPTH_POLICIES),
            },
            "limitations": [
                "Proposed task-local prototype only; no production API or canonical authority change.",
                "Evidence covers four authored crossing-bar inputs and one representative seed per policy.",
                "Rival checks enumerate only the three declared depth_policy settings.",
                "The Python oracle is a cross-check; retained labels are produced by Racket execution.",
            ],
            "process_argv": list(sys.argv),
            "effective_cwd": str(Path.cwd()),
        }
        _write_json(destination / "report.json", report)
        return report
    except BaseException as exc:
        _write_json(
            destination / "failure.json",
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    report = materialize(args.out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "report": str(args.out / "report.json"),
                "counts": report["counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

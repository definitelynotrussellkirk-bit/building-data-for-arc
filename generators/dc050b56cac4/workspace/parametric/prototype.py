"""Task-local prototype for an episode-level diagonal movement direction.

This module does not alter the production generator or selected canonical rule.
It instantiates nearby Racket variants, constructs controlled episodes, executes
all labels through the included Racket bridge, and writes public/private evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "dc050b56cac4"
DIRECTIONS = ("down_left", "down_right", "up_left", "up_right")
DEFAULT_DIRECTION = "down_left"
DIRECTION_OPERATORS = {
    "down_left": ("+", "-"),
    "down_right": ("+", "+"),
    "up_left": ("-", "-"),
    "up_right": ("-", "+"),
}
CANONICAL_ROW_BINDING = "(nr (+ cross-row n))"
CANONICAL_COL_BINDING = "(nc (- cross-col n))"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def canonical_record(root: Path) -> dict:
    matches = []
    with canonical_path(root).open(encoding="utf-8") as source:
        for line in source:
            if line.strip():
                row = json.loads(line)
                # The canonical catalog may also contain augmented descendants
                # that retain the parent's task_id.  The root row is uniquely
                # identified by its own content hash.
                if row.get("content_hash") == TASK_ID:
                    matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}")
    return matches[0]


def canonical_program(root: Path) -> str:
    return canonical_record(root)["program_solution"]


def instantiate(program: str, direction: str = DEFAULT_DIRECTION) -> str:
    """Materialize one exact Racket rule setting from the canonical text."""
    if direction not in DIRECTION_OPERATORS:
        raise ValueError(f"unsupported direction {direction!r}")
    if program.count(CANONICAL_ROW_BINDING) != 1:
        raise ValueError("canonical row binding changed")
    if program.count(CANONICAL_COL_BINDING) != 1:
        raise ValueError("canonical column binding changed")
    row_op, col_op = DIRECTION_OPERATORS[direction]
    return program.replace(
        CANONICAL_ROW_BINDING,
        f"(nr ({row_op} cross-row n))",
        1,
    ).replace(
        CANONICAL_COL_BINDING,
        f"(nc ({col_op} cross-col n))",
        1,
    )


def parameters(seed) -> dict[str, str]:
    """Choose the hidden setting once for a complete episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return {"direction": DIRECTIONS[seed % len(DIRECTIONS)]}


def _marker_points(index: int, h: int, w: int, n: int, cross_row: int, cross_col: int):
    """Four controlled layouts, including one canonical-linked top-right stack."""
    if index == 0:
        points = [(r, w - 1) for r in range(n)]
    elif index == 1:
        points = [(h - 1, c) for c in range(n)]
    elif index == 2:
        points = [(0, 0), (0, w - 1), (h - 1, 0)][:n]
    else:
        points = [(h - n + offset, 0) for offset in range(n)]
    if len(set(points)) != n:
        raise RuntimeError("marker fixture contains duplicates")
    if any(r == cross_row or c == cross_col for r, c in points):
        raise RuntimeError("marker fixture collided with the cross")
    return points


def fixture_inputs(seed) -> list[list[list[int]]]:
    """Construct four varied inputs on which every direction is executable."""
    parameters(seed)  # validates the episode seed
    rng = random.Random(seed ^ 0xDC050B56)
    specs = ((10, 10, 1), (11, 12, 2), (12, 11, 3), (13, 13, 2))
    colors = rng.sample((1, 2, 3, 4, 6, 7, 8, 9), len(specs))
    inputs = []
    for index, ((h, w, n), color) in enumerate(zip(specs, colors)):
        # All four signed moves remain in bounds, making every rival executable.
        cross_row = rng.randint(n, h - 1 - n)
        cross_col = rng.randint(n, w - 1 - n)
        grid = [[0] * w for _ in range(h)]
        for c in range(w):
            grid[cross_row][c] = color
        for r in range(h):
            grid[r][cross_col] = color
        for r, c in _marker_points(index, h, w, n, cross_row, cross_col):
            grid[r][c] = 5
        inputs.append(grid)
    return inputs


def execute(bridge: RacketBridge, program: str, grid):
    """Execute the exact instantiated rule body with the input bound to ``g``."""
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("expected a rule! wrapper")
    bridge.define_grid("g", grid)
    # Removing the executor-only ``rule!`` wrapper exposes a lambda.  Apply it
    # to the bound grid instead of merely evaluating it (which returns a
    # serialized procedure descriptor rather than a grid).
    output = bridge.eval_text(f"({program[len('(rule! ') : -1]} g)")
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(not isinstance(row, list) or len(row) != len(output[0]) for row in output)
    ):
        raise ValueError("Racket did not return a nonempty rectangular grid")
    return output


def episode(seed: int, canonical: str, bridge: RacketBridge) -> dict:
    params = parameters(seed)
    chosen = params["direction"]
    program = instantiate(canonical, chosen)
    inputs = fixture_inputs(seed)
    pairs = [{"input": grid, "output": execute(bridge, program, grid)} for grid in inputs]

    rivals = []
    for rival_direction in DIRECTIONS:
        if rival_direction == chosen:
            continue
        rival_program = instantiate(canonical, rival_direction)
        outputs = [execute(bridge, rival_program, grid) for grid in inputs]
        demo_differences = [
            index for index, pair in enumerate(pairs[:3]) if pair["output"] != outputs[index]
        ]
        query_differs = pairs[3]["output"] != outputs[3]
        rivals.append(
            {
                "direction": rival_direction,
                "program_sha256": sha256(rival_program.encode()),
                "demo_differences": demo_differences,
                "query_differs": query_differs,
                "status": "distinguished" if demo_differences else "ambiguous",
            }
        )
        if query_differs and not demo_differences:
            raise ValueError(
                f"query needs {chosen!r} versus {rival_direction!r}, but demos do not distinguish them"
            )

    return {
        "seed": seed,
        "parameters": params,
        "program": program,
        "program_sha256": sha256(program.encode()),
        "train": pairs[:3],
        "test": pairs[3:],
        "rivals": rivals,
    }


def public_challenge(private: dict) -> dict:
    """Remove hidden parameters, rule text, and query labels."""
    return {
        "train": private["train"],
        "test": [{"input": pair["input"]} for pair in private["test"]],
    }


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _source_hashes() -> dict[str, str]:
    parent = Path(__file__).resolve().parent
    return {
        path.name: sha256(path.read_bytes())
        for path in sorted(parent.iterdir())
        if path.is_file() and path.suffix in {".py", ".md"}
    }


def _write_manifest(output: Path) -> dict:
    members = {}
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            rel = path.relative_to(output).as_posix()
            members[rel] = {"bytes": path.stat().st_size, "sha256": sha256(path.read_bytes())}
    manifest = {"schema": "dc050b56-parametric-evidence-v1", "members": members}
    write_json(output / "manifest.json", manifest)
    return manifest


def materialize(output: Path) -> dict:
    """Execute and retain four complete settings plus a common differing witness."""
    output = Path(output)
    root = find_root(__file__)
    canonical = canonical_program(root)
    sources = _source_hashes()
    bridge = RacketBridge()
    try:
        records = [episode(seed, canonical, bridge) for seed in range(4)]
        distinct_settings = [record["parameters"]["direction"] for record in records]
        if distinct_settings != list(DIRECTIONS):
            raise AssertionError("retained seeds do not cover every direction exactly once")

        for index, record in enumerate(records):
            record["prototype_source_sha256"] = sources
            record["label_authority"] = "included Racket bridge; exact instantiated rule body"
            write_json(output / "public" / f"episode-{index}.json", public_challenge(record))
            write_json(output / "private" / f"episode-{index}.json", record)
            rule_path = output / "private" / f"episode-{index}.rkt"
            rule_path.parent.mkdir(parents=True, exist_ok=True)
            rule_path.write_text(record["program"], encoding="utf-8")

        witness_input = fixture_inputs(0)[0]
        witness_outputs = {}
        witness_programs = {}
        for direction in DIRECTIONS:
            program = instantiate(canonical, direction)
            witness_programs[direction] = sha256(program.encode())
            witness_outputs[direction] = execute(bridge, program, witness_input)
        if len({grid_key(grid) for grid in witness_outputs.values()}) != len(DIRECTIONS):
            raise AssertionError("common witness does not separate every direction")
        write_json(
            output / "private" / "differing-witness.json",
            {
                "input": witness_input,
                "outputs": witness_outputs,
                "program_sha256": witness_programs,
            },
        )

        canonical_checks = []
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute(bridge, instantiate(canonical), pair["input"])
            if actual != pair["output"]:
                raise AssertionError("default prototype changed a canonical label")
            canonical_checks.append(
                {
                    "variant": pair.get("variant"),
                    "split": pair.get("split"),
                    "pair_index": pair.get("pair_index"),
                    "input": pair["input"],
                    "expected_output": pair["output"],
                    "racket_output": actual,
                }
            )
        write_json(
            output / "private" / "canonical-default.json",
            {
                "program_sha256": sha256(canonical.encode()),
                "default_program_exact": instantiate(canonical) == canonical,
                "checks": canonical_checks,
            },
        )

        report = {
            "schema": "dc050b56-parametric-report-v1",
            "status": "prototype",
            "task_id": TASK_ID,
            "parameter": {
                "name": "direction",
                "allowed": list(DIRECTIONS),
                "original_default": DEFAULT_DIRECTION,
            },
            "default_program_exact": instantiate(canonical) == canonical,
            "episode_count": len(records),
            "demonstrations_per_episode": 3,
            "queries_per_episode": 1,
            "distinct_settings": distinct_settings,
            "labels_executed_in_racket": 16,
            "rival_outputs_executed_in_racket": 48,
            "common_witness_outputs_executed_in_racket": 4,
            "canonical_pairs_executed_in_racket": len(canonical_checks),
            "rival_results": [record["rivals"] for record in records],
            "program_sha256": {
                direction: sha256(instantiate(canonical, direction).encode())
                for direction in DIRECTIONS
            },
            "prototype_source_sha256": sources,
            "scope": (
                "four deterministic seeds and controlled all-direction-safe fixtures; "
                "separate from production generation and not variant approval"
            ),
            "limitations": [
                "direction is hidden at episode level and inferred only from demonstrations",
                "controlled fixtures do not establish coverage for every lawful marker arrangement",
                "the production generator and canonical authority remain fixed to down_left",
            ],
        }
        write_json(output / "report.json", report)
        manifest = _write_manifest(output)
        report["manifest_member_count"] = len(manifest["members"])
        # Rewrite report once so its final bytes are included when an external tool hashes the tree.
        write_json(output / "report.json", report)
        _write_manifest(output)
        return report
    finally:
        bridge.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(materialize(args.out), indent=2, sort_keys=True))

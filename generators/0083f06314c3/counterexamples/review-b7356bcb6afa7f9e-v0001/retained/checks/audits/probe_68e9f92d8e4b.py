"""Replayable adversarial audit for generator 68e9f92d8e4b.

The probe tests a rival that treats each nonzero 4-connected component as an
indivisible object and completes it only when that entire component is one
monochrome L-tromino.  The rival agrees with the generated distribution but
disagrees with the canonical rule on touching, differently colored Ls.  It also
records whether the generator's own self_check accepts canonical inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import types
from copy import deepcopy
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
# The review packet stores the production ``scripts`` package under
# ``shared/tools``. Register a namespace alias so rule_wrap can import it.
scripts_package = types.ModuleType("scripts")
scripts_package.__path__ = [str(REPO / "shared" / "tools")]
sys.modules.setdefault("scripts", scripts_package)

from puzzle_generators import runner  # noqa: E402

TASK_ID = "68e9f92d8e4b"
EXPECTED_GENERATOR_SHA256 = "5770a10e12df236525c985898ddc2a5824167b0ef85dd4a00c366ab96d331c8b"


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("audit_68_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_grid(grid: Any):
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return grid


def _as_pairs(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    return [value] if isinstance(value, dict) else value


def _canonical_material(task_id: str) -> tuple[str, list[dict[str, Any]]]:
    source = None
    pairs: list[dict[str, Any]] = []
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            source = source or row.get("program_solution")
            for pair in _as_pairs(row.get("train")) + _as_pairs(row.get("test")):
                if isinstance(pair, dict) and pair.get("input") is not None:
                    pairs.append(
                        {
                            "input": _normalize_grid(pair["input"]),
                            "output": _normalize_grid(pair.get("output")),
                        }
                    )
    if not isinstance(source, str) or not source.strip():
        raise RuntimeError(f"no canonical rule source for {task_id}")
    return source, pairs


def _nonzero_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Match the generator's object ontology: connectivity ignores color."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def component_isolated_rival(grid: list[list[int]]) -> list[list[int]]:
    """Complete only whole nonzero components that are monochrome 3-cell Ls."""
    out = deepcopy(grid)
    for cells in _nonzero_components(grid):
        colors = {grid[r][c] for r, c in cells}
        if len(cells) != 3 or len(colors) != 1:
            continue
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        if (r1 - r0 + 1, c1 - c0 + 1) != (2, 2):
            continue
        component = set(cells)
        box = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        missing = list(box - component)
        if len(missing) == 1:
            mr, mc = missing[0]
            out[mr][mc] = next(iter(colors))
    return out

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws-per-band", type=int, default=40)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = REPO / "generators" / TASK_ID / "generator.py"
    generator_sha = _sha256(generator_path)
    if generator_sha != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError(
            f"generator hash drift: {generator_sha} != {EXPECTED_GENERATOR_SHA256}"
        )
    gen = _load_generator(generator_path)
    rule_source, canonical_pairs = _canonical_material(TASK_ID)
    rule_hash = hashlib.sha256(" ".join(rule_source.split()).encode()).hexdigest()[:12]

    bridge, function_name = runner._open_bridge_with_rule(runner.wrap_rule(rule_source))
    generated_total = generated_rival_fits = 0
    generated_self_check_failures: list[dict[str, Any]] = []
    canonical_rows = []
    counterexample = None
    try:
        for difficulty_index, difficulty in enumerate(("easy", "medium", "hard")):
            for index in range(args.draws_per_band):
                seed = 68_000 + difficulty_index * 10_000 + index
                sample_index = index % 12
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                findings = gen.self_check(deepcopy(grid))
                if findings:
                    generated_self_check_failures.append(
                        {"difficulty": difficulty, "seed": seed, "sample_index": sample_index, "findings": findings}
                    )
                actual = runner._apply_rule(bridge, function_name, grid)
                rival = component_isolated_rival(grid)
                generated_total += 1
                generated_rival_fits += int(rival == actual)

        for index, pair in enumerate(canonical_pairs):
            grid = pair["input"]
            actual = runner._apply_rule(bridge, function_name, grid)
            rival = component_isolated_rival(grid)
            findings = gen.self_check(deepcopy(grid))
            row = {
                "index": index,
                "self_check_findings": findings,
                "stored_output_matches_racket": pair["output"] == actual,
                "component_isolated_rival_matches_racket": rival == actual,
            }
            canonical_rows.append(row)
            if counterexample is None and rival != actual:
                counterexample = {
                    "canonical_pair_index": index,
                    "input": grid,
                    "actual_racket_output": actual,
                    "component_isolated_rival_output": rival,
                    "self_check_findings": findings,
                }
    finally:
        bridge.shutdown()

    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path.relative_to(PACKET)),
        "generator_sha256": generator_sha,
        "canonical_rule_hash": rule_hash,
        "rival": "complete only whole nonzero 4-connected components that are monochrome 3-cell L-trominoes",
        "generated_census": {
            "bands": ["easy", "medium", "hard"],
            "draws_per_band": args.draws_per_band,
            "total": generated_total,
            "rival_matches_racket": generated_rival_fits,
            "self_check_failures": generated_self_check_failures,
        },
        "canonical_census": {
            "total": len(canonical_rows),
            "self_check_rejected": sum(bool(row["self_check_findings"]) for row in canonical_rows),
            "rival_matches_racket": sum(row["component_isolated_rival_matches_racket"] for row in canonical_rows),
            "rows": canonical_rows,
        },
        "counterexample": counterexample,
        "finding_reproduced": (
            generated_total > 0
            and generated_rival_fits == generated_total
            and not generated_self_check_failures
            and counterexample is not None
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "finding_reproduced": report["finding_reproduced"],
        "generated_rival_fit": f"{generated_rival_fits}/{generated_total}",
        "canonical_rejected": report["canonical_census"]["self_check_rejected"],
        "counterexample": counterexample is not None,
    }, sort_keys=True))
    return 0 if report["finding_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

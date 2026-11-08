from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]


def load_source(name: str, relpath: str):
    path = ROOT / relpath
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_task(task_id: str) -> dict:
    path = ROOT / "repo/shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == task_id:
            return record
    raise KeyError(task_id)


def complete_2x2(grid: list[list[int]]) -> list[list[int]]:
    """Literal single-pass mirror of f4d60fd96dde's written/canonical rule."""
    out = [row[:] for row in grid]
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            cells = ((row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1))
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                for r, c in cells:
                    if grid[r][c] == 0:
                        out[r][c] = nonzero[0]
    return out


def same_color_components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def bbox_fill(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: fill each same-color component's bounding rectangle."""
    out = [row[:] for row in grid]
    for color, cells in same_color_components(grid):
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def audit_unknown_override() -> dict:
    generator, path = load_source("audit_db95939a5dd0", "repo/generators/db95939a5dd0/generator.py")
    accepted = changed = 0
    examples = []
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            sample_index = seed + 17
            base = generator.generate(seed, sample_index, difficulty=band)
            try:
                typo = generator.generate(seed, sample_index, difficulty=band, typo_axis=123)
            except Exception as exc:
                continue
            accepted += 1
            if typo != base:
                changed += 1
                if len(examples) < 6:
                    examples.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "base_dims": [len(base), len(base[0])],
                            "typo_dims": [len(typo), len(typo[0])],
                        }
                    )
    return {
        "schema": "arcpuzzles-audit-reproducer-v1",
        "task_id": "db95939a5dd0",
        "generator_sha256": sha256(path),
        "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "finding": "unknown override accepted and changes the default sampling path",
        "method": {
            "bands": ["easy", "medium", "hard"],
            "seeds_per_band": 40,
            "seed_range": "0..39",
            "sample_index": "seed + 17",
            "unknown_override": {"typo_axis": 123},
            "denominator": 120,
        },
        "accepted": accepted,
        "changed_vs_no_override": changed,
        "examples": examples,
        "status": "reproduced" if accepted == 120 and changed else "not_reproduced",
    }


def audit_bbox_shortcut() -> tuple[dict, list[list[list[int]]]]:
    generator, path = load_source("audit_f4d60fd96dde", "repo/generators/f4d60fd96dde/generator.py")
    canonical = canonical_task("f4d60fd96dde")
    canonical_pairs = list(canonical["train"]) + list(canonical["test"])
    canonical_matches = sum(
        bbox_fill(pair["input"]) == pair["output"] == complete_2x2(pair["input"])
        for pair in canonical_pairs
    )

    draws = []
    matches = 0
    unique = set()
    self_check_failures = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for ordinal in range(200):
            seed = 100_000 * (band_index + 1) + ordinal
            sample_index = 31 + ordinal
            grid = generator.generate(seed, sample_index, difficulty=band)
            draws.append(grid)
            unique.add(json.dumps(grid, separators=(",", ":")))
            errors = generator.self_check(grid, difficulty=band)
            if errors:
                self_check_failures.append(
                    {"band": band, "seed": seed, "sample_index": sample_index, "errors": errors}
                )
            if bbox_fill(grid) == complete_2x2(grid):
                matches += 1

    counterexample = [
        [4, 4, 0, 0],
        [4, 0, 0, 0],
        [4, 4, 4, 0],
        [0, 0, 0, 0],
    ]
    canonical_output = complete_2x2(counterexample)
    rival_output = bbox_fill(counterexample)
    result = {
        "schema": "arcpuzzles-audit-reproducer-v1",
        "task_id": "f4d60fd96dde",
        "generator_sha256": sha256(path),
        "generator_version": generator.VERSION,
        "rule_hash": "43946341d62f",
        "finding": "bounding-rectangle fill is observationally equivalent on canonical and generated support",
        "canonical_pairs": len(canonical_pairs),
        "bbox_rival_matches_canonical": canonical_matches,
        "generated_method": {
            "bands": ["easy", "medium", "hard"],
            "draws_per_band": 200,
            "seed_formula": "100000 * (band_index + 1) + ordinal",
            "sample_index_formula": "31 + ordinal",
            "denominator": len(draws),
        },
        "generated_draws": len(draws),
        "unique_inputs": len(unique),
        "bbox_rival_matches_python_rule_mirror": matches,
        "generated_self_check_failures": self_check_failures,
        "counterexample": {
            "input": counterexample,
            "self_check": generator.self_check(counterexample),
            "canonical_rule_mirror_output": canonical_output,
            "bbox_rival_output": rival_output,
            "outputs_differ": canonical_output != rival_output,
            "supported_racket_evidence": "checks/audit/f4d60fd96dde/racket.json",
        },
        "limits": [
            "The 600-draw census compares an independent literal Python mirror of the published single-pass rule; the saved Racket apply receipt independently executes the concrete counterexample.",
            "Finite sampling does not prove the shortcut fits every possible generator output, but the generator constructs eroded rectangles by design.",
        ],
        "status": "reproduced" if canonical_matches == len(canonical_pairs) and matches == len(draws) and canonical_output != rival_output else "not_reproduced",
    }
    return result, draws[:64]


def main() -> None:
    db = audit_unknown_override()
    f4, racket_batch = audit_bbox_shortcut()
    db_path = ROOT / "checks/audit/db95939a5dd0/unknown-override.json"
    f4_path = ROOT / "checks/audit/f4d60fd96dde/rival.json"
    batch_path = ROOT / "checks/audit/f4d60fd96dde/racket-batch-input.json"
    db_path.write_text(json.dumps(db, indent=2, sort_keys=True) + "\n")
    f4_path.write_text(json.dumps(f4, indent=2, sort_keys=True) + "\n")
    batch_path.write_text(json.dumps(racket_batch, separators=(",", ":")) + "\n")
    print(json.dumps({"db95939a5dd0": db, "f4d60fd96dde": f4}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

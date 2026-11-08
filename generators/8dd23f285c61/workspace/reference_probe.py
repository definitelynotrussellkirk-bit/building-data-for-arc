"""Independent oracle and distribution probe for task 8dd23f285c61.

This is review/test tooling, not a replacement label authority.  It derives
expected grids from the written ray semantics without importing helpers from the
selected generator.  ``--racket`` additionally checks the unchanged canonical
Racket program through the public Catalog.apply route.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "8dd23f285c61"


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_task() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical_task()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def _shape(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return len(grid), width


def wall_components(grid) -> list[set[tuple[int, int]]]:
    """Return 4-connected color-5 components without generator code."""
    h, w = _shape(grid)
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        components.append(component)
    return components


def ray_output(grid, *, ignore_tiny_walls: bool = False):
    """Independent implementation of the visible ray rule or its named rival."""
    h, w = _shape(grid)
    if any(type(value) is not int for row in grid for value in row):
        raise ValueError("cells must be literal integers")
    tiny = set()
    if ignore_tiny_walls:
        tiny = set().union(*(component for component in wall_components(grid) if len(component) <= 2))
    output = deepcopy(grid)
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    for sr, sc in seeds:
        output[sr][sc] = 8
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, c = sr + dr, sc + dc
            while 0 <= r < h and 0 <= c < w:
                if grid[r][c] == 5:
                    if (r, c) not in tiny:
                        break
                else:
                    output[r][c] = 8
                r += dr
                c += dc
    return output


def observed(grid) -> dict[str, int]:
    h, w = _shape(grid)
    return {
        "grid_h": h,
        "grid_w": w,
        "n_seeds": sum(value == 2 for row in grid for value in row),
        "n_wall_components": len(wall_components(grid)),
    }


def tiny_wall_witness() -> list[list[int]]:
    """Exact rival counterexample: a one-cell wall must stop the east ray."""
    grid = [[0] * 9 for _ in range(7)]
    grid[3][1] = 2
    grid[6][7] = 2
    grid[3][4] = 5
    # A canonical-looking substantial wall keeps the example from reducing to
    # "the lone gray cell is obviously special" while staying disconnected.
    for row in range(0, 3):
        grid[row][7] = 5
    return grid


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the canonical authority through the public repository API."""
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog

    grids = list(grids)
    receipt = Catalog(ROOT).apply(TASK, grids, reference="canonical", timeout=300)
    if not receipt.get("rule_hash_matches_catalog"):
        raise RuntimeError("executed rule hash did not match the catalog")
    errors = [row.get("error") for row in receipt["results"]]
    if any(error is not None for error in errors):
        raise RuntimeError(f"Racket apply failed: {errors}")
    return [row["output"] for row in receipt["results"]]


def _safe_rule_eval(rule, grid, expected) -> tuple[bool, str | None]:
    """Run a declared rival without letting one bad callable hide the audit."""
    try:
        return rule(grid) == expected, None
    except Exception as exc:  # diagnostic boundary: preserve the exact failure
        return False, f"{type(exc).__name__}: {exc}"


def audit(module, count: int, *, use_racket: bool) -> dict:
    canonical = canonical_pairs()
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(module, "SEMANTIC_WITNESSES", {}))

    canonical_shortcuts: dict[str, dict] = {}
    for name, rival in sorted(shortcuts.items()):
        matches = 0
        errors: list[dict] = []
        for index, pair in enumerate(canonical):
            matched, error = _safe_rule_eval(rival, pair["input"], pair["output"])
            matches += matched
            if error:
                errors.append({"pair": index, "error": error})
        canonical_shortcuts[name] = {
            "matches": matches,
            "total": len(canonical),
            "errors": errors,
        }

    lesson_competitors: dict[str, dict] = {}
    for name, rival in sorted(competitors.items()):
        matches = 0
        errors: list[dict] = []
        for index, pair in enumerate(canonical):
            matched, error = _safe_rule_eval(rival, pair["input"], pair["output"])
            matches += matched
            if error:
                errors.append({"pair": index, "error": error})
        lesson_competitors[name] = {
            "canonical_matches": matches,
            "canonical_total": len(canonical),
            "errors": errors,
        }

    by_band: dict[str, dict] = {}
    retained: list[list[list[int]]] = []
    examples_needed = int(getattr(module, "EXAMPLES_NEEDED", 3))
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes: set[tuple[int, int]] = set()
        wall_counts: set[int] = set()
        seed_counts: set[int] = set()
        inputs: set[str] = set()
        witness_hits = Counter({name: 0 for name in witnesses})
        competitor_disagreements = Counter({name: 0 for name in competitors})
        competitor_errors: dict[str, list[dict]] = {name: [] for name in competitors}
        grids: list[list[list[int]]] = []
        expected_outputs: list[list[list[int]]] = []

        for index in range(count):
            seed = 1009 + index
            sample_index = 7 * index + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            expected = ray_output(grid)
            grids.append(grid)
            expected_outputs.append(expected)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            counts["non_identity"] += expected != grid
            counts["tiny_wall_counterexamples"] += expected != ray_output(
                grid, ignore_tiny_walls=True
            )
            for name, witness in witnesses.items():
                try:
                    witness_hits[name] += bool(witness(grid))
                except Exception as exc:
                    counts["witness_errors"] += 1
                    competitor_errors.setdefault(f"witness:{name}", []).append(
                        {"sample": index, "error": f"{type(exc).__name__}: {exc}"}
                    )
            for name, rival in competitors.items():
                matched, error = _safe_rule_eval(rival, grid, expected)
                competitor_disagreements[name] += not matched
                if error:
                    competitor_errors[name].append({"sample": index, "error": error})
            stats = observed(grid)
            shapes.add((stats["grid_h"], stats["grid_w"]))
            wall_counts.add(stats["n_wall_components"])
            seed_counts.add(stats["n_seeds"])
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if index < 4:
                retained.append(grid)

        lesson_failures: list[dict] = []
        if not hasattr(module, "lesson_identifiable"):
            lesson_failures.append({"start": None, "reasons": ["missing lesson_identifiable"]})
        else:
            # Test every cyclic start, not merely individual witness frequency.
            # The next item after each demonstration window is the query.
            for start in range(count):
                demos = []
                for offset in range(examples_needed):
                    idx = (start + offset) % count
                    demos.append({"input": grids[idx], "output": expected_outputs[idx]})
                query_index = (start + examples_needed) % count
                query = {
                    "input": grids[query_index],
                    "output": expected_outputs[query_index],
                }
                reasons = module.lesson_identifiable(demos, query)
                if reasons:
                    lesson_failures.append({"start": start, "reasons": reasons})

        by_band[str(band)] = dict(
            counts,
            distinct_shapes=len(shapes),
            wall_counts=sorted(wall_counts),
            seed_counts=sorted(seed_counts),
            distinct_inputs=len(inputs),
            witness_hits=dict(witness_hits),
            competitor_disagreements=dict(competitor_disagreements),
            competitor_errors={name: rows for name, rows in competitor_errors.items() if rows},
            lesson_contract_failures=len(lesson_failures),
            lesson_failure_examples=lesson_failures[:10],
        )

    report = {
        "schema": "8dd23f285c61-independent-audit-v2",
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "canonical_pairs": len(canonical),
        "canonical_python_matches": sum(ray_output(pair["input"]) == pair["output"] for pair in canonical),
        "canonical_shortcut_matches": sum(
            ray_output(pair["input"], ignore_tiny_walls=True) == pair["output"] for pair in canonical
        ),
        "canonical_shortcuts": canonical_shortcuts,
        "lesson_competitors": lesson_competitors,
        "lesson_policy": {
            "assembly": "EXAMPLES_NEEDED consecutive generated demos plus the next generated query, cyclic",
            "examples_needed": examples_needed,
            "cyclic_starts_per_band": count,
        },
        "by_band": by_band,
        "witness": {
            "input": tiny_wall_witness(),
            "intended_python": ray_output(tiny_wall_witness()),
            "ignore_tiny_walls": ray_output(tiny_wall_witness(), ignore_tiny_walls=True),
        },
        "racket_executed": use_racket,
    }
    if use_racket:
        grids = [pair["input"] for pair in canonical] + [tiny_wall_witness()] + retained
        actual = racket_outputs(grids)
        predicted = [ray_output(grid) for grid in grids]
        report["racket_cases"] = len(grids)
        report["racket_matches"] = sum(a == b for a, b in zip(actual, predicted))
        report["racket_all_match"] = actual == predicted
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator")
    parser.add_argument("--count", type=int, default=256)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    report = audit(load_generator(args.generator), args.count, use_racket=args.racket)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    bad = report["canonical_python_matches"] != report["canonical_pairs"]
    bad |= report["canonical_shortcut_matches"] != report["canonical_pairs"]
    bad |= any(
        row["matches"] != row["total"] or row["errors"]
        for row in report["canonical_shortcuts"].values()
    )
    bad |= any(row["self_check_errors"] or row["nondeterministic"] for row in report["by_band"].values())
    bad |= any(row["tiny_wall_counterexamples"] != row["samples"] for row in report["by_band"].values())
    bad |= any(row["lesson_contract_failures"] for row in report["by_band"].values())
    bad |= any(row["competitor_errors"] for row in report["by_band"].values())
    bad |= any(
        any(hits == 0 for hits in row["witness_hits"].values())
        for row in report["by_band"].values()
    )
    bad |= any(
        any(hits == 0 for hits in row["competitor_disagreements"].values())
        for row in report["by_band"].values()
    )
    if args.racket:
        bad |= not report.get("racket_all_match", False)
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())

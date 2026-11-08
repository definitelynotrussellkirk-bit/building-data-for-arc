#!/usr/bin/env python3
"""Reproduce the two assigned adversarial-audit censuses without editing targets."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str) -> tuple[ModuleType, Path]:
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_pairs(task_id: str) -> list[dict]:
    pairs: list[dict] = []
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            for split in ("train", "test"):
                raw = row.get(split) or []
                if isinstance(raw, dict):
                    raw = [raw]
                pairs.extend(pair for pair in raw if "input" in pair and "output" in pair)
    if not pairs:
        raise RuntimeError(f"no canonical pairs for {task_id}")
    return pairs


def numeric_grid(grid: list) -> list[list[int]]:
    """Decode canonical compact rows or defensively copy an integer matrix."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if all(isinstance(row, str) for row in grid):
        width = len(grid[0])
        if width == 0 or any(len(row) != width or not row.isdigit() for row in grid):
            raise ValueError("compact grid rows must be equal-length digit strings")
        return [[int(cell) for cell in row] for row in grid]
    if all(isinstance(row, list) and row for row in grid):
        width = len(grid[0])
        if any(len(row) != width for row in grid):
            raise ValueError("matrix grid must be rectangular")
        if any(isinstance(cell, bool) or not isinstance(cell, int) for row in grid for cell in row):
            raise ValueError("matrix grid cells must be integers")
        return [list(row) for row in grid]
    raise ValueError("grid rows must be all strings or all integer lists")


def pinned_seed(task_id: str, band: str, index: int) -> int:
    text = f"profile-floor:v1:{task_id}:{band}:{index}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:12], 16)


def grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def components(grid: list[list[int]], color: int = 4) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                point = stack.pop()
                cells.append(point)
                for dr, dc in CARDINAL:
                    nxt = (point[0] + dr, point[1] + dc)
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(cells)
    return result


def border_two_rival(grid: list[list[int]]) -> list[list[int]]:
    answer = deepcopy(grid)
    for component in components(grid):
        if min(c for _, c in component) <= 1:
            for r, c in component:
                answer[r][c] = 3
    return answer


def audit_or_generator() -> None:
    task_id = "9c26c4b2c305"
    gen, path = load_generator(task_id)
    pairs = canonical_pairs(task_id)
    shortcut_fit = {
        name: {"fit": sum(fn(deepcopy(pair["input"])) == pair["output"] for pair in pairs),
               "total": len(pairs)}
        for name, fn in sorted(gen.CANONICAL_SHORTCUTS.items())
    }
    report = {
        "schema": "audit-9c26c4b2c305-lesson-census-v1",
        "task_id": task_id,
        "generator_sha256": sha(path),
        "rule_hash": gen.RULE_HASH,
        "canonical_shortcut_fit": shortcut_fit,
        "per_band": {},
        "failures": [],
    }
    all_hashes: set[str] = set()
    for band in ("easy", "medium", "hard"):
        unique: set[str] = set()
        residues: Counter[int] = Counter()
        competitors = {
            name: {"refuted": 0, "survived": 0, "errors": 0}
            for name in sorted(gen.LESSON_COMPETITORS)
        }
        identifiable = 0
        for index in range(100):
            seed = pinned_seed(task_id, f"lesson:{band}", index)
            start = index * 11
            residues[start % len(gen.SCHEDULE_PROFILES)] += 1
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, start + offset, difficulty=band)
                output = gen.rule_mirror(deepcopy(grid))
                demos.append({"input": grid, "output": output})
                digest = grid_hash(grid)
                unique.add(digest)
                all_hashes.add(digest)
            query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(deepcopy(query_grid))}
            digest = grid_hash(query_grid)
            unique.add(digest)
            all_hashes.add(digest)
            reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
            if reasons:
                report["failures"].append({
                    "band": band, "index": index, "seed": seed,
                    "sample_index": start, "reasons": reasons,
                })
            else:
                identifiable += 1
            for name, rival in sorted(gen.LESSON_COMPETITORS.items()):
                try:
                    survives = all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
                except Exception as exc:
                    competitors[name]["errors"] += 1
                    report["failures"].append({
                        "band": band, "index": index, "competitor": name,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                else:
                    competitors[name]["survived" if survives else "refuted"] += 1
        report["per_band"][band] = {
            "lessons": 100,
            "identifiable": identifiable,
            "unique_inputs": len(unique),
            "cyclic_start_residues": {
                str(i): residues[i] for i in range(len(gen.SCHEDULE_PROFILES))
            },
            "competitors": competitors,
        }
    report["unique_inputs_across_bands"] = len(all_hashes)
    report["all_passed"] = (
        not report["failures"]
        and all(row["fit"] == row["total"] for row in shortcut_fit.values())
    )
    out = ROOT / "checks/audit" / task_id / "lesson_census.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def audit_leftmost_generator() -> None:
    task_id = "691d467ddb4d"
    gen, path = load_generator(task_id)
    raw_pairs = canonical_pairs(task_id)
    pairs = [
        {"input": numeric_grid(pair["input"]), "output": numeric_grid(pair["output"])}
        for pair in raw_pairs
    ]
    candidates: list[tuple[int, dict]] = []
    for index, pair in enumerate(pairs):
        comps = components(pair["input"])
        if not comps:
            continue
        leftmost = min(min(c for _, c in component) for component in comps)
        if (
            leftmost == 2
            and border_two_rival(pair["input"]) != pair["output"]
            and gen.self_check(deepcopy(pair["input"])) == []
        ):
            candidates.append((index, pair))
    if len(candidates) != 1:
        raise RuntimeError(f"expected one canonical counterexample, found {len(candidates)}")
    test_index, test_pair = candidates[0]
    outdir = ROOT / "checks/audit" / task_id
    input_grid = test_pair["input"]
    (outdir / "input.json").write_text(
        json.dumps({"input": input_grid}, indent=2) + "\n", encoding="utf-8"
    )
    (outdir / "rival.json").write_text(
        json.dumps({
            "name": "recolor_component_touching_first_two_columns",
            "description": "Recolor any yellow component whose minimum column is 0 or 1; otherwise do nothing.",
            "output": border_two_rival(input_grid),
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    rows = []
    failures = []
    min_columns: Counter[int] = Counter()
    unique: set[str] = set()
    offsets = {"easy": 0, "medium": 10_000, "hard": 20_000}
    for band in ("easy", "medium", "hard"):
        for index in range(200):
            seed = 100_000 + offsets[band] + index
            try:
                grid = gen.generate(seed, index, difficulty=band)
            except Exception as exc:
                failures.append({
                    "band": band, "index": index, "seed": seed,
                    "error": f"{type(exc).__name__}: {exc}",
                })
                continue
            comps = components(grid)
            left = min(min(c for _, c in component) for component in comps)
            min_columns[left] += 1
            unique.add(grid_hash(grid))
            rows.append({"min_left_col": left, "self_check": gen.self_check(grid)})
    census = {
        "schema": "audit-691d467ddb4d-sampler-census-v1",
        "task_id": task_id,
        "generator_sha256": sha(path),
        "draws_requested": 600,
        "draws_generated": len(rows),
        "unique_inputs": len(unique),
        "seed_policy": "easy seeds 100000..100199; medium 110000..110199; hard 120000..120199; sample_index 0..199",
        "min_left_column_counts": {str(k): v for k, v in sorted(min_columns.items())},
        "self_check_failures": sum(bool(row["self_check"]) for row in rows),
        "generation_failures": failures,
        "all_generated_selected_objects_touch_first_two_columns": all(row["min_left_col"] <= 1 for row in rows),
        "canonical_training_shortcut_fit": [
            border_two_rival(pair["input"]) == pair["output"]
            for index, pair in enumerate(pairs)
            if index != test_index
        ],
        "canonical_test_self_check": gen.self_check(input_grid),
        "canonical_test_leftmost_column": min(
            min(c for _, c in component) for component in components(input_grid)
        ),
    }
    (outdir / "sampler_census.json").write_text(
        json.dumps(census, indent=2) + "\n", encoding="utf-8"
    )

    racket_path = outdir / "racket.json"
    if racket_path.is_file():
        racket = json.loads(racket_path.read_text(encoding="utf-8"))
        rival = json.loads((outdir / "rival.json").read_text(encoding="utf-8"))
        result = racket["results"][0]
        compact = {
            "schema": "audit-691d467ddb4d-counterexample-v1",
            "task_id": task_id,
            "generator_sha256": racket["generator_sha256"],
            "rule_hash": racket["executed_rule_hash"],
            "input_sha256": result["input_sha256"],
            "actual_output_sha256": result["output_sha256"],
            "rival_output_differs": result["output"] != rival["output"],
            "input_passes_target_validator": census["canonical_test_self_check"] == [],
            "sampler_census": "sampler_census.json",
            "input": "input.json",
            "racket": "racket.json",
            "rival": "rival.json",
            "finding": "The sampler always anchors the selected object at columns 0 or 1, so a border-touch shortcut fits all generated draws and both canonical training pairs but fails this validator-accepted canonical test whose leftmost object begins at column 2.",
        }
        (outdir / "counterexample.json").write_text(
            json.dumps(compact, indent=2) + "\n", encoding="utf-8"
        )


def main() -> int:
    audit_or_generator()
    audit_leftmost_generator()
    print(json.dumps({
        "9c26c4b2c305": "checks/audit/9c26c4b2c305/lesson_census.json",
        "691d467ddb4d": "checks/audit/691d467ddb4d/sampler_census.json",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

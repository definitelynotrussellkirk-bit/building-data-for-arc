#!/usr/bin/env python3
"""Independent source-bound audit for ee37b0acdd32 generators.

This intentionally does not call the candidate's private analyzer.  It rebuilds
monochrome components, the contact graph, shortest-path counts, and the expected
output from emitted grids.  It can audit both the retained pre-repair generator
and the active candidate, and writes a compact replayable JSON report.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "ee37b0acdd32"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO = TASK_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
for path in (REPO / "src", RUNTIME):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
Cell = tuple[int, int]
Grid = list[list[int]]


def load_generator(path: Path):
    name = f"audit_{TASK_ID}_{hashlib.sha256(path.read_bytes()).hexdigest()[:10]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def components(grid: Grid) -> tuple[list[set[Cell]], list[int]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    found: list[set[Cell]] = []
    colors: list[int] = []
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0 or (r, c) in seen:
                continue
            part = {(r, c)}
            seen.add((r, c))
            stack = [(r, c)]
            while stack:
                rr, cc = stack.pop()
                for dr, dc in NEIGHBORS:
                    nxt = rr + dr, cc + dc
                    if not (0 <= nxt[0] < h and 0 <= nxt[1] < w):
                        continue
                    if nxt in seen or grid[nxt[0]][nxt[1]] != value:
                        continue
                    seen.add(nxt)
                    part.add(nxt)
                    stack.append(nxt)
            found.append(part)
            colors.append(value)
    return found, colors


def analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["not a non-empty row grid"]}
    h, w = len(grid), len(grid[0])
    if not w or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["ragged or empty rows"]}
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"invalid value {value!r}")
                break
    if errors:
        return {"errors": errors}

    parts, colors = components(grid)
    owner = {cell: index for index, part in enumerate(parts) for cell in part}
    adjacency = [set() for _ in parts]
    for (r, c), first in owner.items():
        for dr, dc in NEIGHBORS:
            second = owner.get((r + dr, c + dc))
            if second is not None and second != first:
                adjacency[first].add(second)
                adjacency[second].add(first)
    blue = [i for i, color in enumerate(colors) if color == 1]
    red = [i for i, color in enumerate(colors) if color == 2]
    if len(blue) != 1:
        errors.append(f"blue components={len(blue)}")
    if len(red) != 1:
        errors.append(f"red components={len(red)}")

    connected: set[int] = set()
    if parts:
        connected.add(0)
        stack = [0]
        while stack:
            cur = stack.pop()
            for nxt in adjacency[cur]:
                if nxt not in connected:
                    connected.add(nxt)
                    stack.append(nxt)
    edges = sum(map(len, adjacency)) // 2
    graph_is_tree = bool(parts) and len(connected) == len(parts) and edges == len(parts) - 1

    path: list[int] = []
    path_count = 0
    if len(blue) == len(red) == 1:
        start, goal = blue[0], red[0]
        distance = {start: 0}
        parent: dict[int, int | None] = {start: None}
        ways = {start: 1}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            for nxt in sorted(adjacency[cur]):
                candidate = distance[cur] + 1
                if nxt not in distance:
                    distance[nxt] = candidate
                    parent[nxt] = cur
                    ways[nxt] = ways[cur]
                    queue.append(nxt)
                elif distance[nxt] == candidate:
                    ways[nxt] = min(2, ways[nxt] + ways[cur])
        if goal in parent:
            cur: int | None = goal
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            path.reverse()
            path_count = ways[goal]
        else:
            errors.append("endpoints disconnected")
    path_set = set(path)
    branches = [index for index in range(len(parts)) if index not in path_set]
    branch_leaf_ok = all(
        len(adjacency[index]) == 1 and next(iter(adjacency[index])) in path_set
        for index in branches
    )
    output = [[0] * w for _ in range(h)]
    for index in path:
        for r, c in parts[index]:
            output[r][c] = 8
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "palette_size": len({value for row in grid for value in row}),
        "component_count": len(parts),
        "colors": colors,
        "component_sizes": [len(part) for part in parts],
        "adjacency": [sorted(row) for row in adjacency],
        "edge_count": edges,
        "graph_is_tree": graph_is_tree,
        "path": path,
        "path_len": len(path),
        "shortest_path_count": path_count,
        "branches": branches,
        "branch_count": len(branches),
        "branch_leaf_ok": branch_leaf_ok,
        "output": output,
    }


def canonical_pairs() -> list[dict[str, Grid]]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return list(row["train"]) + list(test)
    raise RuntimeError(f"canonical row {TASK_ID} missing")


def frozen(grid: Grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def audit(generator_path: Path, samples_per_band: int, include_overrides: bool) -> dict[str, Any]:
    gen = load_generator(generator_path)
    failures: list[dict[str, Any]] = []
    profile_counts: Counter[str] = Counter()
    signature_counts: Counter[str] = Counter()
    witness_hits: Counter[str] = Counter()
    rival_disagreements: Counter[str] = Counter()
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    totals = Counter()

    def fail(kind: str, **detail: Any) -> None:
        totals[f"failure_{kind}"] += 1
        if len(failures) < 80:
            failures.append({"kind": kind, **detail})

    for pair_index, pair in enumerate(canonical_pairs()):
        info = analyze(pair["input"])
        if info["errors"] or info["output"] != pair["output"]:
            fail("canonical_independent_oracle", pair_index=pair_index, errors=info["errors"])
        checker = getattr(gen, "self_check", None)
        if checker is None or checker(pair["input"]):
            fail("canonical_self_check", pair_index=pair_index)
        mirror = getattr(gen, "rule_mirror", None)
        if mirror is None or mirror(pair["input"]) != pair["output"]:
            fail("canonical_rule_mirror", pair_index=pair_index)

    bands = ("easy", "medium", "hard")
    for band_index, band in enumerate(bands):
        for sample_index in range(samples_per_band):
            seed = 100_000 + band_index * 1_000_000 + sample_index
            totals["default_samples"] += 1
            try:
                grid = gen.generate(seed, sample_index, difficulty=band)
            except Exception as exc:  # noqa: BLE001 - audit must retain candidate crashes
                fail("generate_crash", band=band, seed=seed, sample_index=sample_index, error=repr(exc))
                continue
            unique_inputs.add(frozen(grid))
            info = analyze(grid)
            if info["errors"]:
                fail("invalid_grid", band=band, seed=seed, sample_index=sample_index, errors=info["errors"])
                continue
            signature_counts[str((info["height"], info["width"], info["palette_size"]))] += 1
            profile = None
            if hasattr(gen, "schedule_profile"):
                profile = gen.schedule_profile(seed, sample_index, band)
                profile_counts[str(profile)] += 1
            if not info["graph_is_tree"]:
                fail("graph_not_tree", band=band, seed=seed, sample_index=sample_index)
            if info["shortest_path_count"] != 1:
                fail("path_not_unique", band=band, seed=seed, sample_index=sample_index, count=info["shortest_path_count"])
            if not 4 <= info["path_len"] <= 6:
                fail("path_len", band=band, seed=seed, sample_index=sample_index, value=info["path_len"])
            if not 1 <= info["branch_count"] <= 2 or not info["branch_leaf_ok"]:
                fail("branch_contract", band=band, seed=seed, sample_index=sample_index, count=info["branch_count"])
            checker = getattr(gen, "self_check", None)
            if checker is None or checker(grid, difficulty=band):
                fail("self_check_rejects_emission", band=band, seed=seed, sample_index=sample_index)
            mirror = getattr(gen, "rule_mirror", None)
            if mirror is not None and mirror(grid) != info["output"]:
                fail("mirror_mismatch", band=band, seed=seed, sample_index=sample_index)
            for name, witness in getattr(gen, "SEMANTIC_WITNESSES", {}).items():
                if witness(grid):
                    witness_hits[name] += 1
            for name, rival in getattr(gen, "LESSON_COMPETITORS", {}).items():
                try:
                    if rival(grid) != info["output"]:
                        rival_disagreements[name] += 1
                except Exception as exc:  # noqa: BLE001
                    fail("rival_crash", rival=name, error=repr(exc))

    override_cases = 0
    if include_overrides and set(getattr(gen, "AXES", {})) >= {
        "grid_h", "grid_w", "path_len", "branch_count"
    }:
        for band in bands:
            for h in (8, 14):
                for w in (10, 16):
                    for path_len in (4, 5, 6):
                        for branch_count in (1, 2):
                            request = {
                                "grid_h": h,
                                "grid_w": w,
                                "path_len": path_len,
                                "branch_count": branch_count,
                            }
                            override_cases += 1
                            try:
                                grid = gen.generate(700_000 + override_cases, override_cases, difficulty=band, **request)
                                info = analyze(grid)
                                observed = {
                                    "grid_h": info.get("height"),
                                    "grid_w": info.get("width"),
                                    "path_len": info.get("path_len"),
                                    "branch_count": info.get("branch_count"),
                                }
                                if info["errors"] or observed != request:
                                    fail("override_mismatch", band=band, request=request, observed=observed, errors=info["errors"])
                                public_observed = getattr(gen, "observe_overrides", lambda _grid: {})(grid)
                                if public_observed != request:
                                    fail("observe_overrides_mismatch", band=band, request=request, observed=public_observed)
                            except Exception as exc:  # noqa: BLE001
                                fail("override_crash", band=band, request=request, error=repr(exc))

    lesson_windows = 0
    if hasattr(gen, "lesson_identifiable") and hasattr(gen, "rule_mirror"):
        for band in bands:
            for start in range(12):
                episode = []
                for index in range(start, start + 4):
                    grid = gen.generate(900_000 + start, index, difficulty=band)
                    episode.append({"input": grid, "output": gen.rule_mirror(grid)})
                lesson_windows += 1
                reasons = gen.lesson_identifiable(episode[:3], episode[3])
                if reasons:
                    fail("lesson_not_identifiable", band=band, start=start, reasons=reasons)

    canonical_shortcuts = {}
    for name, rival in getattr(gen, "CANONICAL_SHORTCUTS", {}).items():
        matches = [rival(pair["input"]) == pair["output"] for pair in canonical_pairs()]
        canonical_shortcuts[name] = {"matches": sum(matches), "pairs": len(matches)}
        if not all(matches):
            fail("false_canonical_shortcut_claim", rival=name, matches=matches)

    source_bytes = generator_path.read_bytes()
    return {
        "schema": "ee37b0acdd32-contact-graph-audit-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "samples_per_band": samples_per_band,
        "default_samples": totals["default_samples"],
        "unique_default_inputs": len(unique_inputs),
        "override_cases": override_cases,
        "lesson_windows": lesson_windows,
        "profile_counts": dict(sorted(profile_counts.items())),
        "signature_counts": dict(sorted(signature_counts.items())),
        "witness_hits": dict(sorted(witness_hits.items())),
        "rival_disagreements": dict(sorted(rival_disagreements.items())),
        "canonical_shortcuts": canonical_shortcuts,
        "failure_counts": {
            key.removeprefix("failure_"): value
            for key, value in sorted(totals.items())
            if key.startswith("failure_")
        },
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=TASK_HOME / "generator.py")
    parser.add_argument("--samples-per-band", type=int, default=200)
    parser.add_argument("--skip-overrides", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.generator.resolve(), args.samples_per_band, not args.skip_overrides)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

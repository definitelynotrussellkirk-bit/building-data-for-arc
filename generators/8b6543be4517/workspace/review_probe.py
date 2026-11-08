#!/usr/bin/env python3
"""Source-bound mirror coverage / actual-Racket probe. Never imports a sibling repo.

Run from a full review packet:
  python3 run_with_racket.py python3 generators/8b6543be4517/workspace/review_probe.py \
      --repo . --out ../checks/probe-after --require-coverage

Use --generator-source ../.review/baseline/repo/generators/8b6543be4517/generator.py
and omit --require-coverage to measure the frozen baseline. Output must be new.
The copied runtime lives in a TemporaryDirectory and is removed after the run.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import html
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

TASK_ID = "8b6543be4517"
BANDS = ("easy", "medium", "hard")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixel_features(grid: list[list[int]]) -> dict[str, Any]:
    """Independent, pixel-only feature oracle; no generator helper calls."""
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("expected a rectangular nonempty ARC integer grid")
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(v == 8 for v in grid[r])]
    cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(rows) + len(cols) != 1:
        raise ValueError("expected exactly one full divider")
    axis, mid = ("row", rows[0]) if rows else ("col", cols[0])
    sevens = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7}
    paired, oob, targets, collisions = set(), set(), set(), set()
    for r, c in sevens:
        q = (2 * mid - r, c) if rows else (r, 2 * mid - c)
        if not (0 <= q[0] < h and 0 <= q[1] < w):
            oob.add((r, c))
        elif q in sevens:
            paired.add((r, c))
        else:
            targets.add(q)
            if grid[q[0]][q[1]] not in (0, 7, 8):
                collisions.add(q)
    return {"height": h, "width": w, "axis": axis, "mid": mid,
            "centered": 2 * mid == (h if rows else w) - 1,
            "sevens": len(sevens), "paired_cells": len(paired),
            "oob": len(oob), "additions": len(targets),
            "collisions": len(collisions), "targets": sorted(targets)}


def pixel_mirror(grid: list[list[int]], *, zero_only: bool = False) -> list[list[int]]:
    f = pixel_features(grid)
    out = copy.deepcopy(grid)
    for r, c in f["targets"]:
        if not zero_only or grid[r][c] == 0:
            out[r][c] = 7
    return out


def collision_witness() -> list[list[int]]:
    grid = [[0] * 11 for _ in range(8)]
    for row in grid:
        row[4] = 8
    grid[1][2], grid[1][6], grid[5][7], grid[6][1] = 7, 5, 7, 5
    return grid


def transpose(grid):
    return [list(row) for row in zip(*grid)]


def flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def flip_ud(grid):
    return list(reversed(copy.deepcopy(grid)))


def _grid_html(grid) -> str:
    colors = ("#111111", "#1875ce", "#e73c3c", "#21ae5b", "#ffdc38",
              "#999999", "#b639bd", "#ff8a25", "#42dbe8", "#9c303e")
    rows = []
    for row in grid:
        rows.append("<tr>" + "".join(
            f'<td style="background:{colors[v]};color:{"#111" if v in (4, 7, 8) else "#fff"}">{v}</td>'
            for v in row) + "</tr>")
    return '<table class="grid">' + "".join(rows) + "</table>"


def write_witness_html(path: Path, cases: list[dict]) -> None:
    sections = []
    for case in cases:
        panels = []
        for key in ("input", "racket_output", "zero_only_output"):
            if key in case:
                panels.append(f'<div><h3>{html.escape(key)}</h3>{_grid_html(case[key])}</div>')
        sections.append(f'<section><h2>{html.escape(case["name"])}</h2><div class="panels">'
                        + "".join(panels) + "</div></section>")
    path.write_text('''<!doctype html><meta charset="utf-8"><title>Mirror review witnesses</title>
<style>body{font:16px system-ui;margin:24px;max-width:1500px}h1{margin-bottom:8px}
.panels{display:flex;flex-wrap:wrap;gap:24px}.grid{border-collapse:collapse}
.grid td{width:24px;height:24px;text-align:center;border:1px solid #ddd;font:12px monospace}
section{border-top:1px solid #ddd;margin-top:24px;padding-top:10px}</style>
<h1>8b6543be4517: executed counterexamples</h1><p>Outputs labelled racket_output were
executed through the packet's selected canonical Racket program. The zero-only
rival fits all five canonical pairs but refuses occupied targets. Cell coordinates
in the JSON evidence are zero-based.</p>''' + "".join(sections), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--generator-source", type=Path)
    ap.add_argument("--draws-per-band", type=int, default=512)
    ap.add_argument("--racket-per-band", type=int, default=64)
    ap.add_argument("--seed", type=int, default=20261002)
    ap.add_argument("--require-coverage", action="store_true")
    args = ap.parse_args(argv)
    if args.draws_per_band < 24 or not 1 <= args.racket_per_band <= args.draws_per_band:
        ap.error("draws-per-band must be >=24, and 1 <= racket-per-band <= draws-per-band")
    repo, out = args.repo.resolve(), args.out.resolve()
    source = (args.generator_source.resolve() if args.generator_source else
              repo / "generators" / TASK_ID / "generator.py")
    if out.exists():
        ap.error(f"output already exists: {out}")
    if not (repo / "src/arcpuzzles/runtime.py").is_file() or not source.is_file():
        ap.error("repo or generator source is missing")
    out.mkdir(parents=True)
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime

    failures: list[dict[str, Any]] = []
    witnesses: list[dict[str, Any]] = []
    oracle_calls = 0
    oracle_matches = 0
    canonical_matches = 0
    transforms_checked = 0
    override_checked = 0
    windows_checked = 0
    generator_digest = sha256(source)
    report: dict[str, Any] = {"schema": "mirror-review-probe-v1", "task_id": TASK_ID,
        "generator_sha256": generator_digest,
        "canonical_file_sha256": sha256(repo / "shared/data/canonical/puzzles.jsonl"),
        "probe_sha256": sha256(Path(__file__)),
        "parameters": {"draws_per_band": args.draws_per_band,
                       "racket_per_band": args.racket_per_band, "seed": args.seed,
                       "require_coverage": args.require_coverage}, "failures": failures}

    with tempfile.TemporaryDirectory(prefix="mirror-review-") as directory:
        runtime = Path(directory)
        prepare_runtime(Catalog(repo), runtime, TASK_ID)
        staged = runtime / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
        staged.write_bytes(source.read_bytes())
        if sha256(staged) != generator_digest:
            raise RuntimeError("source changed during staging")
        sys.path.insert(0, str(runtime))
        old_cwd = Path.cwd()
        os.chdir(runtime)
        try:
            gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
            from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, canonical_rule_hash
            from puzzle_generators import runner
            report["version"] = gen.VERSION
            report["rule_hash"] = canonical_rule_hash(TASK_ID)
            report["examples_needed"] = gen.EXAMPLES_NEEDED
            bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(canonical_rule_source(TASK_ID)))
            with (out / "oracle_cases.jsonl").open("w") as oracle_log:
                def official(grid, label):
                    nonlocal oracle_calls, oracle_matches
                    frozen = copy.deepcopy(grid)
                    value = runner._apply_rule(bridge, name, copy.deepcopy(grid))
                    expected = pixel_mirror(grid)
                    match = value == expected == gen.rule_mirror(grid) and frozen == grid
                    oracle_calls += 1
                    oracle_matches += int(match)
                    oracle_log.write(json.dumps({"case": label, "input": grid, "output": value,
                                                "independent_match": match}, separators=(",", ":")) + "\n")
                    if not match:
                        failures.append({"kind": "racket_parity", "case": label})
                    return value
                try:
                    canonical = canonical_pairs(TASK_ID)
                    canonical_rows = []
                    for i, pair in enumerate(canonical):
                        actual = official(pair["input"], f"canonical:{i}")
                        matches = actual == pair["output"]
                        canonical_matches += int(matches)
                        if not matches or gen.self_check(pair["input"]) or gen.strict_canonical_like(pair["input"]):
                            failures.append({"kind": "canonical", "index": i})
                        canonical_rows.append({"index": i, "racket_matches_stored": matches,
                            "zero_only_matches_stored": pixel_mirror(pair["input"], zero_only=True) == pair["output"],
                            "features": pixel_features(pair["input"])})
                    report["canonical"] = canonical_rows
                    grid = collision_witness()
                    actual = official(grid, "hand-built:collision")
                    witnesses.append({"name": "canonical-fitting zero-only rival counterexample",
                        "input": grid, "racket_output": actual,
                        "zero_only_output": pixel_mirror(grid, zero_only=True),
                        "self_check": gen.self_check(grid), "strict_canonical_like": gen.strict_canonical_like(grid)})
                    coverage = {}
                    stride = max(1, args.draws_per_band // args.racket_per_band)
                    for band in BANDS:
                        counts, additions, pair_counts, oobs = Counter(), Counter(), Counter(), Counter()
                        centered, collisions, profiles = Counter(), Counter(), Counter()
                        seen = set()
                        checked_racket = 0
                        for i in range(args.draws_per_band):
                            seed = args.seed + 1009 * i
                            grid = gen.generate(seed, i, difficulty=band)
                            f = pixel_features(grid)
                            counts[f["sevens"]] += 1; additions[f["additions"]] += 1
                            pair_counts[f["paired_cells"]] += 1; oobs[f["oob"]] += 1
                            centered[f"{f['axis']}:{f['centered']}"] += 1
                            collisions[f["collisions"]] += 1
                            observed = gen.observe_overrides(grid).get("scene_profile")
                            profiles[str(observed)] += 1
                            seen.add(json.dumps(grid, separators=(",", ":")))
                            if gen.self_check(grid) or gen.strict_canonical_like(grid) or observed is None:
                                failures.append({"kind": "draw_grammar", "band": band, "seed": seed, "sample_index": i})
                            if i % stride == 0 and checked_racket < args.racket_per_band:
                                official(grid, f"census:{band}:{seed}:{i}")
                                checked_racket += 1
                            if i < 8:
                                actual = official(grid, f"witness:{band}:{seed}:{i}")
                                witnesses.append({"name": f"{band} seed={seed} sample_index={i}",
                                    "input": grid, "racket_output": actual,
                                    "zero_only_output": pixel_mirror(grid, zero_only=True), "features": f})
                                for transform in (transpose, flip_lr, flip_ud):
                                    transformed = transform(grid)
                                    changed = official(transformed, f"metamorphic:{transform.__name__}:{band}:{seed}:{i}")
                                    transforms_checked += 1
                                    if changed != transform(actual):
                                        failures.append({"kind": "metamorphic", "band": band, "index": i,
                                                         "transform": transform.__name__})
                            if i % 29 == 0 and grid != gen.generate(seed, i, difficulty=band):
                                failures.append({"kind": "nondeterministic", "band": band, "index": i})
                        coverage[band] = {"draws": args.draws_per_band, "unique_inputs": len(seen),
                            "input_seven_counts": dict(sorted(counts.items())),
                            "addition_counts": dict(sorted(additions.items())),
                            "paired_cell_counts": dict(sorted(pair_counts.items())),
                            "oob_counts": dict(sorted(oobs.items())),
                            "centered_by_orientation": dict(sorted(centered.items())),
                            "collision_counts": dict(sorted(collisions.items())),
                            "profiles": dict(sorted(profiles.items()))}
                        if args.require_coverage:
                            checks = {"count_support": len(counts) >= 5,
                                "additions": 2 in additions and max(additions) > 3,
                                "centered_both_axes": centered["row:True"] > 0 and centered["col:True"] > 0,
                                "clean_and_collision": collisions[0] > 0 and sum(v for k, v in collisions.items() if k) > 0,
                                "clipped_and_unclipped": oobs[0] > 0 and sum(v for k, v in oobs.items() if k) > 0,
                                "optional_pairs": pair_counts[0] > 0 and sum(v for k, v in pair_counts.items() if k) > 0}
                            for key, valid in checks.items():
                                if not valid:
                                    failures.append({"kind": "coverage", "band": band, "requirement": key})
                    report["coverage"] = coverage
                    # Exact profile inverses must remain exact in every band,
                    # including profiles that are not scheduled in that band.
                    for band in BANDS:
                        for profile in gen.SCENE_PROFILES:
                            for i in range(4):
                                seed = args.seed + i
                                grid = gen.generate(seed, i, difficulty=band, scene_profile=profile)
                                official(grid, f"override:{band}:{profile}:{seed}:{i}")
                                override_checked += 1
                                if gen.observe_overrides(grid) != {"scene_profile": profile}:
                                    failures.append({"kind": "override", "band": band, "profile": profile, "index": i})
                    # Test every start residue of the LCM(6,4)=12 schedule,
                    # using actual Racket labels and two future queries.
                    for band in BANDS:
                        for seed in (0, 17, 987654321):
                            grids = [gen.generate(seed, i, difficulty=band) for i in range(18)]
                            outputs = [official(g, f"lesson:{band}:{seed}:{i}") for i, g in enumerate(grids)]
                            for start in range(12):
                                n = gen.EXAMPLES_NEEDED
                                demos = [{"input": grids[i], "output": outputs[i]} for i in range(start, start + n)]
                                for qi in (start + n, start + n + 1):
                                    findings = gen.lesson_identifiable(demos, {"input": grids[qi], "output": outputs[qi]})
                                    windows_checked += 1
                                    if findings:
                                        failures.append({"kind": "lesson", "band": band, "seed": seed,
                                                         "start": start, "query_index": qi, "findings": findings})
                    report["runtime_identity"] = bridge.runtime_identity
                finally:
                    bridge.shutdown()
        finally:
            os.chdir(old_cwd)
    report.update({"oracle_calls": oracle_calls, "oracle_matches": oracle_matches,
                   "canonical_matches": canonical_matches, "override_cases": override_checked,
                   "metamorphic_cases": transforms_checked, "lesson_query_checks": windows_checked,
                   "passed": not failures})
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "witnesses.json").write_text(json.dumps(witnesses, indent=2) + "\n")
    write_witness_html(out / "witnesses.html", witnesses)
    print(json.dumps({k: report[k] for k in ("version", "generator_sha256", "oracle_calls",
        "oracle_matches", "canonical_matches", "override_cases", "metamorphic_cases",
        "lesson_query_checks", "passed")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

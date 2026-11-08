#!/usr/bin/env python3
"""Reusable source-bound probe for a selected ARCpuzzles generator.

Uses the repository's real portable runtime, canonical parser and Racket verifier.
Reads rival names from the loaded generator, never from a copied name list.
Failures retain exact inputs, overrides, source hashes, and reference outputs.
Run via the packet's run_with_racket.py wrapper; see workspace/README.md.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import AbstractContextManager
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_root():
    for parent in Path(__file__).resolve().parents:
        if (parent / "catalog/puzzles.jsonl").is_file():
            return parent
    raise RuntimeError("run this tool within a native ARCpuzzles source tree")


class ReviewContext(AbstractContextManager):
    """One independent runtime, reference interpreter and selected module set."""
    def __init__(self, task_ids, *, repo=None, racket=True, generator_paths=None):
        self.repo = Path(repo).resolve() if repo else source_root()
        sys.path.insert(0, str(self.repo / "src"))
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.runtime import prepare_runtime
        self.tmp = tempfile.TemporaryDirectory(prefix="arcpuzzles-review-probe-")
        self.runtime = Path(self.tmp.name)
        prepare_runtime(Catalog(self.repo), self.runtime, task_ids=list(task_ids))
        sys.path.insert(0, str(self.runtime))
        self.modules, self.identity, self.rows = {}, {}, {}
        from scripts.coder_synth_verify import ProgramVerifier, _as_pairs, _norm_grid
        self.normal_pairs = lambda row: [
            {"input": _norm_grid(p["input"]), "output": _norm_grid(p["output"])}
            for split in ("train", "test") for p in _as_pairs(row.get(split, []))
            if p.get("input") is not None and p.get("output") is not None
        ]
        for line in (self.runtime / "data/canonical/puzzles.jsonl").open():
            row = json.loads(line)
            if row.get("task_id") in task_ids:
                self.rows[row["task_id"]] = row
        for tid in task_ids:
            original = self.repo / "generators" / tid / "generator.py"
            chosen = Path((generator_paths or {}).get(tid, original)).resolve()
            staged = self.runtime / "puzzle_generators/per_puzzle" / tid / "generator.py"
            staged.write_bytes(chosen.read_bytes())
            # Unique module names prevent stale source reuse in this process.
            name = "review_probe_" + tid + "_" + sha256(staged)[:12]
            spec = importlib.util.spec_from_file_location(name, staged)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            self.modules[tid] = module
            program = self.rows[tid]["program_solution"]
            self.identity[tid] = {
                "task_id": tid, "generator_sha256": sha256(chosen),
                "rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
                "canonical_row_sha256": hashlib.sha256(json.dumps(self.rows[tid], sort_keys=True).encode()).hexdigest(),
                "canonical_file_sha256": sha256(self.runtime / "data/canonical/puzzles.jsonl"),
                "prelude_sha256": sha256(self.runtime / "arc_repl/racket_prelude/arc-prelude.rkt"),
                "generator_version": getattr(module, "VERSION", None),
                "copied_generator_matches_selected_source": sha256(staged) == sha256(chosen),
            }
        self.verifier = ProgramVerifier() if racket else None

    def reference(self, task_id, grid):
        if self.verifier is None:
            raise RuntimeError("Racket was not enabled; no reference output available")
        return self.verifier.apply(self.rows[task_id]["program_solution"], grid)

    def __exit__(self, exc_type, exc, tb):
        if self.verifier is not None:
            self.verifier.close()
        self.tmp.cleanup()
        return False


def components(grid, diagonal=False):
    """Independent input-only geometry, not a labeler."""
    todo = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    out = []
    while todo:
        start = min(todo)
        color = grid[start[0]][start[1]]
        stack, cells = [start], {start}
        todo.remove(start)
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc) or (not diagonal and abs(dr)+abs(dc) != 1):
                        continue
                    p = r+dr, c+dc
                    if p in todo and grid[p[0]][p[1]] == color:
                        todo.remove(p); cells.add(p); stack.append(p)
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        out.append({"color": color, "cells": sorted(cells), "bbox": (r0, c0, r1, c1),
                    "h": r1-r0+1, "w": c1-c0+1,
                    "solid": len(cells) == (r1-r0+1)*(c1-c0+1)})
    return out


def scene_features(grid):
    items = components(grid)
    return {
        "fat_rectangles": sum(o["solid"] and min(o["h"], o["w"]) >= 2 for o in items),
        "non_solid": sum(not o["solid"] for o in items),
        "thin_lines": sum(o["solid"] and min(o["h"], o["w"]) == 1 and len(o["cells"]) >= 3 for o in items),
        "singletons": sum(len(o["cells"]) == 1 for o in items),
        "same_color_diagonal_join": len(components(grid, diagonal=True)) < len(items),
    }


def run(args):
    repo = source_root()
    override_paths = {}
    if args.baseline:
        override_paths[args.task_id] = repo.parent / ".review/baseline/repo/generators" / args.task_id / "generator.py"
    command = {"cwd": "repo", "argv": ["python3", str(Path(__file__).resolve().relative_to(repo)), *sys.argv[1:]]}
    with ReviewContext([args.task_id], repo=repo, racket=args.racket, generator_paths=override_paths) as ctx:
        gen = ctx.modules[args.task_id]
        report = {"schema": "arcpuzzles-source-bound-probe-v1", "phase": args.phase,
                  "source": ctx.identity[args.task_id], "command": command,
                  "seed_range_inclusive": [0, args.seeds-1],
                  "sample_index_range_inclusive": [0, args.samples-1],
                  "bands": args.bands, "texture_requests": args.textures,
                  "runtime_directory": str(ctx.runtime),
                  "racket_enabled": args.racket, "failures": [], "groups": {},
                  "canonical_shortcuts": {}, "rival_witnesses": {},
                  "lessons": {"policy": "consecutive demos, then one query; all cyclic starts per seed/band",
                              "total": 0, "all_competitors_refuted": 0, "query_identifiable": 0}}
        rivals = dict(getattr(gen, "LESSON_COMPETITORS", {}))
        canonical = ctx.normal_pairs(ctx.rows[args.task_id])
        report["canonical_pair_count"] = len(canonical)
        report["canonical_reference_matches"] = 0
        for i, pair in enumerate(canonical):
            if args.racket:
                actual = ctx.reference(args.task_id, pair["input"])
                report["canonical_reference_matches"] += actual == pair["output"]
                if actual != pair["output"]:
                    report["failures"].append({"kind": "canonical_reference_mismatch", "pair_index": i,
                                               "input": pair["input"], "canonical_output": pair["output"], "racket_output": actual})
        for name, rival in getattr(gen, "CANONICAL_SHORTCUTS", {}).items():
            report["canonical_shortcuts"][name] = {
                "matches": sum(rival(p["input"]) == p["output"] for p in canonical), "total": len(canonical)}
        all_hashes = set()
        generated, reference_calls = 0, len(canonical) if args.racket else 0
        for band in args.bands:
            for texture in args.textures:
                group = Counter()
                key = f"{band}/{texture}"
                report["groups"][key] = group
                group_hashes = set()
                for seed in range(args.seeds):
                    episode = []
                    for index in range(args.samples):
                        request = {"seed": seed, "sample_index": index, "difficulty": band,
                                   "overrides": {} if texture == "default" else {"texture": texture}}
                        try:
                            grid = gen.generate(seed, index, difficulty=band, **request["overrides"])
                        except Exception as exc:
                            report["failures"].append({"kind": "generation_exception", **request, "error": repr(exc)})
                            continue
                        generated += 1; group["generated"] += 1
                        digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
                        all_hashes.add(digest); group_hashes.add(digest)
                        features = scene_features(grid)
                        for name, value in features.items():
                            group["with_" + name] += bool(value)
                        output = ctx.reference(args.task_id, grid) if args.racket else None
                        reference_calls += args.racket
                        row = {**request, "input": grid, "input_sha256": digest,
                               "racket_output": output, "features": features}
                        episode.append({"input": grid, "output": output})
                        errors = gen.self_check(grid, difficulty=band) if callable(getattr(gen, "self_check", None)) else None
                        if errors:
                            group["validator_failures"] += 1
                            report["failures"].append({"kind": "self_check", "errors": errors, **row})
                        missing = ((texture in ("blob", "l_merge") and not features["non_solid"])
                                   or (texture == "thin" and not features["thin_lines"]))
                        if missing:
                            group["missing_requested_witness"] += 1
                            report["failures"].append({"kind": "missing_requested_witness", **row})
                        mirror = getattr(gen, "expected_output", getattr(gen, "rule_mirror", None))
                        if args.racket and callable(mirror) and mirror(grid) != output:
                            report["failures"].append({"kind": "mirror_disagrees_with_racket", "mirror_output": mirror(grid), **row})
                        for name, rival in rivals.items():
                            candidate = rival(grid)
                            if args.racket and candidate != output:
                                group["refutes_" + name] += 1
                                report["rival_witnesses"].setdefault(name, {**row, "rival_output": candidate})
                    if texture == "default" and rivals and args.racket:
                        n = getattr(gen, "EXAMPLES_NEEDED", 3)
                        period = len(getattr(gen, "SCHEDULE_PROFILES", (None,)))
                        for start in range(min(period, len(episode)-n)):
                            demos, query = episode[start:start+n], episode[start+n]
                            surviving = [name for name, rival in rivals.items()
                                         if all(rival(p["input"]) == p["output"] for p in demos)]
                            harmful = [name for name in surviving if rivals[name](query["input"]) != query["output"]]
                            report["lessons"]["total"] += 1
                            report["lessons"]["all_competitors_refuted"] += not surviving
                            report["lessons"]["query_identifiable"] += not harmful
                            if harmful:
                                report["failures"].append({"kind": "lesson_surviving_query_rivals", "seed": seed,
                                                           "difficulty": band, "start": start, "rivals": harmful,
                                                           "demos": demos, "query": query})
                group["unique_inputs"] = len(group_hashes)
        report.update(generated_samples=generated, unique_inputs=len(all_hashes), racket_executions=reference_calls,
                      failure_count=len(report["failures"]))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({k: report[k] for k in ("phase", "generated_samples", "unique_inputs", "racket_executions", "failure_count", "lessons")}))
        return int(bool(report["failures"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--phase", required=True, choices=("before", "intermediate", "final", "audit"))
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--bands", nargs="+", default=["easy", "medium", "hard"])
    parser.add_argument("--textures", nargs="+", default=["default"])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1 or args.samples < 1:
        parser.error("seeds and samples must be positive")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())

"""Findings-only, live-Racket audits for the two immutable assigned targets."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def keep_topmost(grid):
    out = [[0] * len(grid[0]) for _ in grid]
    for col in range(len(grid[0])):
        for row in range(len(grid)):
            if grid[row][col]:
                out[row][col] = grid[row][col]
                break
    return out


def score(rivals, demos, query):
    result = {"refuted": [], "survived_all": [], "query_discriminates": []}
    for name, rival in sorted(rivals.items()):
        if any(rival(p["input"]) != p["output"] for p in demos):
            result["refuted"].append(name)
        elif rival(query["input"]) == query["output"]:
            result["survived_all"].append(name)
        else:
            result["query_discriminates"].append(name)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path("repo"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    library, output = args.library.resolve(), args.out.resolve()
    if output.exists():
        parser.error("refusing to overwrite evidence")
    ids = ("4b1c57a69862", "4842b1ca59e2")
    sys.path.insert(0, str(library / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    canonical = {tid: [] for tid in ids}
    for line in (library / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        tid = row.get("task_id")
        if tid in canonical:
            test = row.get("test", [])
            for pair in row.get("train", []) + (test if isinstance(test, list) else [test]):
                if pair.get("output") is not None:
                    canonical[tid].append({side: [[int(c) for c in r] for r in pair[side]]
                                           for side in ("input", "output")})
    report = {"schema": "assigned-audits-v1", "oracle": "canonical_racket",
              "command": ["python3", "checks/audit_probes.py", "--library", "repo", "--out", "checks/audit-results.json"],
              "cwd": "packet_root", "targets": {}}
    cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-two-audits-") as temp:
        runtime = Path(temp)
        prepare_runtime(Catalog(library), runtime, task_ids=list(ids))
        sys.path.insert(0, str(runtime)); os.chdir(runtime)
        from puzzle_generators import runner
        try:
            for tid in ids:
                bundle = runner._load_bundle(tid)
                g = bundle.generator_module
                bridge, fn = runner._open_bridge_with_rule(bundle.rule_callable_text)
                try:
                    def apply(grid):
                        return runner._apply_rule(bridge, fn, grid)
                    source_path = library / "generators" / tid / "generator.py"
                    result = {"generator_sha256": digest(source_path),
                              "normalized_rule_sha256": normalized(bundle.rule_source),
                              "rule_sha256": hashlib.sha256(bundle.rule_source.encode()).hexdigest(),
                              "source_unchanged": True}
                    unique_pairs = list({json.dumps(p, sort_keys=True): p for p in canonical[tid]}.values())
                    result["canonical_counts"] = {"rows_with_pairs": len(canonical[tid]),
                                                   "unique_pairs": len(unique_pairs),
                                                   "unique_inputs": len({json.dumps(p['input']) for p in unique_pairs})}
                    canonical_checks = []
                    for i, pair in enumerate(unique_pairs):
                        actual = apply(pair["input"])
                        canonical_checks.append({"pair_index": i, "input": pair["input"],
                                                 "stored_output": pair["output"], "actual_racket_output": actual,
                                                 "stored_matches_racket": actual == pair["output"],
                                                 "validator_errors": g.self_check(pair["input"])})
                    result["canonical_checks"] = canonical_checks
                    if tid == ids[0]:
                        rivals = dict(g.LESSON_COMPETITORS)
                        rivals.update(g.CANONICAL_SHORTCUTS)
                        result["declared_competitors"] = sorted(g.LESSON_COMPETITORS)
                        result["declared_shortcuts"] = sorted(g.CANONICAL_SHORTCUTS)
                        result["shortcut_canonical_fit"] = {}
                        for name, rival in g.CANONICAL_SHORTCUTS.items():
                            fits = [rival(p["input"]) == p["output"] for p in unique_pairs]
                            mismatch = next((i for i, x in enumerate(fits) if not x), None)
                            result["shortcut_canonical_fit"][name] = {"matched": sum(fits), "total": len(fits)}
                            if mismatch is not None:
                                p = unique_pairs[mismatch]
                                result["shortcut_canonical_fit"][name]["counterexample"] = {
                                    "canonical_pair_index": mismatch, "input": p["input"],
                                    "actual_racket_output": canonical_checks[mismatch]["actual_racket_output"],
                                    "rival_output": rival(p["input"]),
                                    "validator_errors": g.self_check(p["input"]),
                                    "documented_domain": "canonical published input"}
                        mismatches, invalid, failed, hooks = [], [], [], []
                        profile_counts, refutations = Counter(), Counter()
                        for band in ("easy", "medium", "hard"):
                            for seed in range(32):
                                pairs = []
                                for si in range(8):
                                    grid = g.generate(seed, si, difficulty=band)
                                    actual = apply(grid)
                                    errors = g.self_check(grid)
                                    if errors:
                                        invalid.append({"seed": seed, "sample_index": si, "band": band, "errors": errors})
                                    if actual != g._climb(grid):
                                        mismatches.append({"seed": seed, "sample_index": si, "band": band,
                                                           "input": grid, "actual_racket_output": actual,
                                                           "mirror_output": g._climb(grid)})
                                    profile_counts[g.observe_overrides(grid)["scene_profile"]] += 1
                                    pairs.append({"input": grid, "output": actual})
                                for start in range(4):
                                    demos, query = pairs[start:start+4], pairs[start+4]
                                    scored = score(rivals, demos, query)
                                    refutations.update(scored["refuted"])
                                    if scored["query_discriminates"]:
                                        failed.append({"seed": seed, "start": start, "band": band, "scores": scored})
                                    reasons = g.lesson_identifiable(demos, query)
                                    if reasons:
                                        hooks.append({"seed": seed, "start": start, "band": band, "reasons": reasons})
                        result["census"] = {"seed_range": [0,31], "sample_range": [0,7],
                            "bands": ["easy", "medium", "hard"], "draws": 768,
                            "overlapping_lessons": 384, "start_range": [0,3],
                            "profile_counts": dict(profile_counts), "rival_refutation_counts": dict(refutations),
                            "invalid_draws": invalid, "racket_mirror_mismatches": mismatches,
                            "query_discriminating_lessons": failed, "hook_failures": hooks}
                    else:
                        inp = g.generate(0, 0, difficulty="easy")
                        result["generated_counterexample"] = {
                            "seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": {},
                            "input": inp, "actual_racket_output": apply(inp), "rival_output": keep_topmost(inp),
                            "rival_description": "the topmost-retention rule described in generator SUMMARY/docstring",
                            "validator_errors": g.self_check(inp),
                            "documented_domain": "ordinary default generator draw, accepted by self_check"}
                        baseline = g.generate(0, 0)
                        overrides = {"palette_size": 1, "n_distinct_colors": 1, "palette_kind": "warm"}
                        pinned = g.generate(0, 0, **overrides)
                        result["ignored_palette_counterexample"] = {
                            "seed": 0, "sample_index": 0, "difficulty": None, "overrides": overrides,
                            "input": pinned, "actual_racket_output": apply(pinned), "rival_output": keep_topmost(pinned),
                            "identical_to_unpinned": pinned == baseline,
                            "observed_nonzero_colors": sorted({v for r in pinned for v in r if v}),
                            "validator_errors": g.self_check(pinned),
                            "documented_domain": "declared axis request, accepted by generator and validator"}
                        result["canonical_rejected_count"] = sum(bool(p["validator_errors"]) for p in canonical_checks)
                    result["source_unchanged"] = digest(source_path) == result["generator_sha256"]
                    report["targets"][tid] = result
                    print(tid, "audited", flush=True)
                finally:
                    bridge.shutdown()
        finally:
            os.chdir(cwd)
    with output.open("x") as handle:
        json.dump(report, handle, indent=2); handle.write("\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

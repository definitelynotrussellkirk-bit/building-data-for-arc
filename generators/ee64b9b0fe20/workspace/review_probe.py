#!/usr/bin/env python3
"""Source-bound Racket census, exact rival witnesses, and read-only audit probes.

Run from the extracted packet:
  python3 run_with_racket.py python3 generators/ee64b9b0fe20/workspace/review_probe.py \
      --out ../checks/final-probe --seeds 64 --samples 8 --audits

This is an AUTHORING/REVIEW tool. Never run it during a closed-reference solve.
It reads reference programs and canonical answers. Dataset/solve labels are
never produced by the diagnostic Python mirrors.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time
import tempfile
import shutil
from collections import Counter

TASK_ID = "ee64b9b0fe20"
BANDS = ("easy", "medium", "hard")


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ambiguous_rivals(rivals, demos, query):
    """Survives every visible demo AND changes the authoritative query answer."""
    return [name for name, rival in rivals.items()
            if all(rival(demo["input"]) == demo["output"] for demo in demos)
            and rival(query["input"]) != query["output"]]


def prepare_review_runtime(repo, destination, task_ids):
    """Use the public copier; never reconstruct its source-to-runtime mapping."""
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    return prepare_runtime(Catalog(repo), destination, task_ids=task_ids)


def load_generator(repo, task_id):
    path = repo / "generators" / task_id / "generator.py"
    if not path.is_file():
        path = repo / "puzzle_generators/per_puzzle" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location("review_gen_" + task_id, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_authorities(repo, task_ids):
    result = {task_id: [] for task_id in task_ids}
    for line in (repo / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") in result:
            result[row["task_id"]].append(row)
    for task_id, rows in result.items():
        if not rows:
            raise ValueError("no canonical authority for " + task_id)
        programs = {row["program_solution"] for row in rows}
        if len(programs) != 1:
            raise ValueError("ambiguous canonical programs for " + task_id)
    return result


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def scene_record(mod, grid, output):
    return {"input_sha256": digest_json(grid), "output_sha256": digest_json(output),
            "self_check": mod.self_check(grid), "observables": mod.semantic_observables(grid),
            "mirror_matches_racket": mod.rule_mirror(grid) == output}


def gravity(grid, *, ignore_bottom=False):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        values = [grid[r][c] for r in range(h - int(ignore_bottom)) if grid[r][c]]
        for r, value in enumerate(values, h - len(values)):
            out[r][c] = value
    return out


def shifts(grid, stationary_colors=()):
    delta = {7: (-2, 0), 2: (0, -2), 9: (2, 0), 1: (0, 1)}
    h, w = len(grid), len(grid[0])
    out = [[8] * w for _ in range(h)]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 8:
                continue
            dr, dc = (0, 0) if color in stationary_colors else delta[color]
            if 0 <= r + dr < h and 0 <= c + dc < w:
                out[r + dr][c + dc] = color
    return out


def audit_targets(repo, rules, execute, sources, command):
    a_id, b_id = "22304ccc509c", "3ba75376d7f1"
    a, b = load_generator(repo, a_id), load_generator(repo, b_id)
    result = {}
    # Audit A: a canonical input, not an invented out-of-domain grid, proves
    # why always-empty bottom rows leave a harmful shortcut unchallenged.
    canonical = rules[a_id][0]["train"][0]
    actual = execute(a_id, canonical["input"])
    a_counts, a_draws = Counter(), []
    for band in BANDS:
        for seed in range(40):
            grid = a.generate(seed, 0, difficulty=band)
            output = execute(a_id, grid)
            a_draws.append({"seed": seed, "sample_index": 0, "difficulty": band,
                            "input_sha256": digest_json(grid), "output_sha256": digest_json(output)})
            a_counts["samples"] += 1
            a_counts["empty_bottom_row"] += int(not any(grid[-1]))
            a_counts["self_check_failures"] += bool(a.self_check(grid))
            a_counts["rival_matches"] += gravity(grid, ignore_bottom=True) == output
            a_counts["python_mirror_matches"] += gravity(grid) == output
    palette_grid = a.generate(0, 0, difficulty="medium", palette_size=1)
    result[a_id] = {
        "source": sources[a_id], "command": command,
        "census": dict(a_counts), "draw_manifest": a_draws,
        "distinct_input_hashes": len({row["input_sha256"] for row in a_draws}), "seed_range": [0, 39], "sample_indices": [0], "bands": list(BANDS),
        "counterexample": {"source_kind": "canonical train[0]", "input": canonical["input"],
                           "racket_output": actual, "rival_output": gravity(canonical["input"], ignore_bottom=True),
                           "rival_name": "ignore_bottom_input_row", "self_check": a.self_check(canonical["input"]),
                           "matches_canonical_label": actual == canonical["output"],
                           "in_canonical_domain": True,
                           "in_documented_generated_support": False,
                           "support_reason": "the constructor samples range(h-1); a canonical bottom-row 8 cannot be emitted"},
        "override_failure": {"seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"palette_size": 1},
                             "actual_palette_size": len({v for row in palette_grid for v in row if v}),
                             "input": palette_grid, "self_check": a.self_check(palette_grid)},
    }
    b_counts, per_offset, first_failure, b_draws = Counter(), Counter(), None, []
    for seed in range(12):
        pairs = []
        for index in range(11):
            grid = b.generate(seed, index, difficulty="medium")
            output = execute(b_id, grid)
            pairs.append({"input": grid, "output": output})
            b_counts["draws"] += 1
            b_draws.append({"seed": seed, "sample_index": index, "difficulty": "medium",
                            "input_sha256": digest_json(grid), "output_sha256": digest_json(output)})
            b_counts["self_check_failures"] += bool(b.self_check(grid))
            b_counts["python_mirror_matches"] += shifts(grid) == output
        for start in range(8):
            demos, query = pairs[start:start + 3], pairs[start + 3]
            seen = {v for p in demos for row in p["input"] for v in row if v != 8}
            query_colors = {v for row in query["input"] for v in row if v != 8}
            unseen = query_colors - seen
            rival = shifts(query["input"], unseen)
            b_counts["lesson_windows"] += 1
            if unseen and rival != query["output"]:
                b_counts["ambiguous_windows"] += 1
                per_offset[str(start)] += 1
                if first_failure is None:
                    first_failure = {"seed": seed, "difficulty": "medium", "demo_indices": list(range(start, start + 3)),
                                     "query_index": start + 3, "unseen_colors": sorted(unseen),
                                     "demos": demos, "input": query["input"], "racket_output": query["output"],
                                     "rival_output": rival, "rival_name": "leave unseen colors stationary",
                                     "rival_matches_every_demo": all(shifts(p["input"], unseen) == p["output"] for p in demos),
                                     "self_check": b.self_check(query["input"]), "in_documented_generated_support": True}
    base = b.generate(0, 0)
    typo = b.generate(0, 0, bogus_axis=123)
    result[b_id] = {"source": sources[b_id], "command": command, "census": dict(b_counts), "draw_manifest": b_draws,
                    "distinct_input_hashes": len({row["input_sha256"] for row in b_draws}),
                    "seed_range": [0, 11], "sample_index_range": [0, 10], "lesson_start_range": [0, 7],
                    "ambiguous_by_offset": dict(per_offset), "counterexample": first_failure,
                    "unknown_override": {"seed": 0, "sample_index": 0, "overrides": {"bogus_axis": 123},
                                         "accepted": True, "byte_equivalent_grid": base == typo, "input": typo}}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--audits", action="store_true")
    args = parser.parse_args(argv)
    if args.seeds < 1 or args.samples < 3:
        parser.error("--seeds >= 1 and --samples >= 3 are required")
    if args.out.exists():
        parser.error("output path already exists; preserve evidence and choose a new path")
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True)
    task_ids = [TASK_ID] + (["22304ccc509c", "3ba75376d7f1"] if args.audits else [])
    runtime = Path(tempfile.mkdtemp(prefix="ee64-review-runtime-"))
    manifest = prepare_review_runtime(repo, runtime, task_ids)
    write_json(out / "runtime_manifest.json", manifest)
    sys.path.insert(0, str(runtime))
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    rules = read_authorities(repo, task_ids)
    mod = load_generator(runtime, TASK_ID)
    sources = {tid: {"task_id": tid, "generator_sha256": digest_file(repo / "generators" / tid / "generator.py"),
                     "canonical_rule_sha256": hashlib.sha256(rules[tid][0]["program_solution"].encode()).hexdigest()}
               for tid in task_ids}
    command = {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]}
    started, failures, totals, census, witnesses = time.monotonic(), [], Counter(), [], {}
    by_band, lessons, canon = {}, Counter(), []
    calls, occurrences, bridge = 0, 0, None
    original_cwd = Path.cwd()

    def execute(tid, grid):
        nonlocal calls
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        answer = bridge.eval_text(f"({wrapped[tid]} {literal})")
        calls += 1
        return answer

    try:
        os.chdir(runtime)
        command["actual_runtime_cwd"] = str(runtime)
        wrapped = {tid: wrap_rule(rules[tid][0]["program_solution"]) for tid in task_ids}
        bridge = RacketBridge(timeout=20)
        # Keep all row occurrences for provenance, execute each unique pair once.
        unique = {}
        occurrences = 0
        for row in rules[TASK_ID]:
            for split in ("train", "test"):
                for pair in row.get(split, []):
                    occurrences += 1
                    unique.setdefault(digest_json(pair), pair)
        for key, pair in unique.items():
            actual = execute(TASK_ID, pair["input"])
            record = scene_record(mod, pair["input"], actual)
            record.update({"pair_sha256": key, "matches_canonical_label": actual == pair["output"],
                           "rival_matches": {name: rival(pair["input"]) == actual for name, rival in mod.SEMANTIC_RIVALS.items()}})
            canon.append(record)
            if record["self_check"] or not record["mirror_matches_racket"] or not record["matches_canonical_label"]:
                failures.append({"canonical": record, "input": pair["input"], "actual": actual})
        for band in BANDS:
            stats = Counter()
            for seed in range(args.seeds):
                pairs = []
                for index in range(args.samples):
                    grid = mod.generate(seed, index, difficulty=band)
                    actual = execute(TASK_ID, grid)
                    record = scene_record(mod, grid, actual)
                    record.update({"seed": seed, "sample_index": index, "difficulty": band})
                    census.append(record)
                    obs = record["observables"]
                    stats["samples"] += 1
                    stats["canonical_10x10"] += (len(grid), len(grid[0])) == (10, 10)
                    stats["zero_object"] += obs["zero_object"]
                    stats["object_at_least_12_cells"] += max(obs["shape_sizes"]) >= 12
                    stats["shared_colors"] += obs["palette_size"] < obs["shape_count"]
                    stats["different_colors_touch"] += obs["different_colors_touch"]
                    stats["frame_present"] += obs["frame"]
                    stats["nonrectangular"] += obs["nonrectangular"]
                    if record["self_check"] or not record["mirror_matches_racket"]:
                        failures.append({"case": record, "input": grid, "racket_output": actual})
                    for name, rival in mod.SEMANTIC_RIVALS.items():
                        other = rival(grid)
                        if other != actual:
                            stats["refutes_" + name] += 1
                            if name not in witnesses:
                                witnesses[name] = {"source": sources[TASK_ID], "seed": seed, "sample_index": index,
                                                   "difficulty": band, "overrides": {}, "input": grid,
                                                   "racket_output": actual, "rival_output": other,
                                                   "rival_name": name, "self_check": record["self_check"],
                                                   "in_documented_generated_support": True, "command": command}
                    pairs.append({"input": grid, "output": actual})
                for offset in range(args.samples - 2):
                    demos, query = pairs[offset:offset + 2], pairs[offset + 2]
                    ambiguous = ambiguous_rivals(mod.SEMANTIC_RIVALS, demos, query)
                    hook_errors = mod.lesson_identifiable(demos, query)
                    lessons["overlapping_two_demo_windows"] += 1
                    lessons["ambiguous_windows"] += bool(ambiguous)
                    lessons["hook_failures"] += bool(hook_errors)
                    if ambiguous or hook_errors:
                        failures.append({"lesson": {"seed": seed, "band": band, "offset": offset},
                                         "ambiguous": ambiguous, "hook_errors": hook_errors})
                if seed % 16 == 15:
                    print(f"{band}: {seed + 1}/{args.seeds} seeds verified through real Racket", flush=True)
            by_band[band] = dict(stats)
            totals.update(stats)
        audits = audit_targets(runtime, rules, execute, sources, command) if args.audits else {}
        for tid, result in audits.items():
            write_json(out / f"audit_{tid}.json", result)
        for name, result in witnesses.items():
            write_json(out / f"counterexample_{name}.json", result)
        for tid, source in sources.items():
            if digest_file(repo / "generators" / tid / "generator.py") != source["generator_sha256"]:
                failures.append({"source_drift_during_run": tid})
    except Exception as exc:
        failures.append({"fatal_exception": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        if bridge is not None:
            bridge.close()
        os.chdir(original_cwd)
        with (out / "census.jsonl").open("w") as stream:
            for record in census:
                stream.write(json.dumps(record, sort_keys=True) + "\n")
        report = {"schema": "ee64b9b0fe20-review-census-v1", "phase": "final-source",
                  "python_version": platform.python_version(), "sources": sources,
                  "tool_sha256": digest_file(__file__), "canonical_ledger_sha256": digest_file(repo / "shared/data/canonical/puzzles.jsonl"),
                  "command": command, "actual_runtime_cwd": str(runtime), "runtime_manifest": "runtime_manifest.json",
                  "seed_range": [0, args.seeds - 1], "sample_index_range": [0, args.samples - 1],
                  "bands": list(BANDS), "totals": dict(totals), "by_band": by_band,
                  "unique_input_hashes": len({row["input_sha256"] for row in census}),
                  "canonical": {"occurrences": occurrences, "unique_pairs": len(canon), "results": canon},
                  "lessons": dict(lessons), "racket_calls": calls,
                  "wall_seconds": round(time.monotonic() - started, 3), "failures": failures,
                  "passed": not failures, "audit_findings_are_not_included_in_pass_flag": bool(args.audits)}
        write_json(out / "summary.json", report)
        print(json.dumps({k: report[k] for k in ("totals", "lessons", "racket_calls", "wall_seconds", "passed")}), flush=True)
        shutil.rmtree(runtime)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

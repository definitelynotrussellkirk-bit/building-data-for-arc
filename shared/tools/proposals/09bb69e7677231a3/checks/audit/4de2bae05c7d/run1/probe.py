"""Bounded, source-bound connectivity audit; run through outer review.py run.

Search uses the source's Python mirror only to identify a candidate. Every
claimed canonical/lesson output is subsequently obtained from real Racket.
No generator or shared source is modified. Exit 1 means a reproduced finding;
exit 2 means infrastructure/probe error, with the diagnostic retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "4de2bae05c7d"


def digest_bytes(body):
    return hashlib.sha256(body).hexdigest()


def json_hash(value):
    return digest_bytes(json.dumps(value, separators=(",", ":")).encode())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def connected_components(grid, connectivity):
    h, w = len(grid), len(grid[0])
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    visited, result = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 4 or (r, c) in visited:
                continue
            cells, stack = [], [(r, c)]
            visited.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in deltas:
                    cell = (rr + dr, cc + dc)
                    if (0 <= cell[0] < h and 0 <= cell[1] < w
                            and grid[cell[0]][cell[1]] == 4
                            and cell not in visited):
                        visited.add(cell)
                        stack.append(cell)
            result.append(sorted(cells))
    return result


def recolor_eight_connected_l(grid):
    """Plausible rival: identify same-yellow components with eight neighbors."""
    out = [row[:] for row in grid]
    for cells in connected_components(grid, 8):
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if (len(cells) == 3 and max(rows) - min(rows) == 1
                and max(cols) - min(cols) == 1):
            for r, c in cells:
                out[r][c] = 1
    return out


def differences(expected, actual):
    return [{"row": r, "col": c, "canonical": value, "rival": actual[r][c]}
            for r, row in enumerate(expected) for c, value in enumerate(row)
            if value != actual[r][c]]


def main(args):
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "probe_result.json"
    report = {
        "schema": "arcpuzzles-task-audit-connectivity-v1", "task_id": TASK,
        "status": "running", "started_unix": time.time(),
        "actual_payload_cwd": str(Path.cwd()), "payload_argv": sys.argv,
        "claim_scope": "ordered production, five demonstrations and one final query; no rotations",
        "search_bound": {"seeds": [0, args.seeds - 1], "start_index": 0,
                         "difficulty": "easy", "n_train": 5, "n_test": 1},
    }
    write_json(report_path, report)
    try:
        root = find_root(__file__)
        gen, source_path, source_sha = load_selected_generator(TASK, root=root)
        canon_path = canonical_path(root)
        canon_matches = []
        for line_no, line in enumerate(canon_path.read_text().splitlines(), 1):
            row = json.loads(line)
            if row.get("task_id") == TASK:
                canon_matches.append((line_no, line, row))
        assert len(canon_matches) == 1, "Canonical authority must be unique"
        line_no, raw_line, row = canon_matches[0]
        rule = row["program_solution"]
        report["source"] = {
            "generator_path": str(source_path), "generator_sha256": source_sha,
            "generator_version": gen.VERSION, "declared_rule_hash": gen.RULE_HASH,
            "canonical_path": str(canon_path), "canonical_line": line_no,
            "canonical_line_sha256": digest_bytes(raw_line.encode()),
            "rule_sha256": digest_bytes(rule.encode()),
            "probe_sha256": digest_bytes(Path(__file__).read_bytes()),
            "review_index_present": (source_path.parent / "evidence/review_index.json").exists(),
        }
        (out / "audited_generator.py").write_bytes(source_path.read_bytes())
        write_json(out / "canonical_row.json", row)
        (out / "canonical_rule.rkt").write_text(rule + "\n")
        candidates = []
        search_rows = []
        for seed in range(args.seeds):
            grids = [gen.generate(seed, si, difficulty="easy") for si in range(6)]
            fits = [recolor_eight_connected_l(grid) == gen.rule_mirror(grid)
                    for grid in grids]
            search_rows.append({"seed": seed, "eight_rival_agreement": fits})
            if all(fits[:5]) and not fits[5]:
                candidates.append((seed, grids))
                break
        report["search"] = {
            "method": "direct generate plus Python mirror screening, stop at first candidate",
            "completed_lessons": len(search_rows), "rows": search_rows,
            "candidate_seed": candidates[0][0] if candidates else None,
            "not_a_population_rate": True,
        }

        # Exact 20-index sample per band to establish the declared schedule's
        # profile support. This is a focused measurement, not the public gate.
        canon_profiles = {(len(p["input"]), len(p["input"][0]),
                           len({v for rr in p["input"] for v in rr}))
                          for split in ("train", "test") for p in row[split]}
        minima = [min(p[i] for p in canon_profiles) for i in range(3)]
        maxima = [max(p[i] for p in canon_profiles) for i in range(3)]
        profile_rows = []
        for band in ("easy", "medium", "hard"):
            for si in range(20):
                grid = gen.generate(101, si, difficulty=band)
                profile = (len(grid), len(grid[0]), len({v for rr in grid for v in rr}))
                profile_rows.append({
                    "seed": 101, "sample_index": si, "difficulty": band,
                    "profile": profile, "exact": profile in canon_profiles,
                    "envelope": all(minima[i] <= profile[i] <= maxima[i] for i in range(3)),
                    "input_sha256": json_hash(grid),
                })
        report["focused_profile_measurement"] = {
            "canonical_profiles": sorted(canon_profiles), "sample_count": len(profile_rows),
            "exact_count": sum(p["exact"] for p in profile_rows),
            "envelope_count": sum(p["envelope"] for p in profile_rows),
            "rows": profile_rows,
            "limit": "Not a public profile_floor invocation; seed 101, indices 0..19, all bands.",
        }
        write_json(report_path, report)
        print(json.dumps({"candidate_seed": report["search"]["candidate_seed"],
                          "screened_lessons": len(search_rows),
                          "profile_envelope_count": report["focused_profile_measurement"]["envelope_count"]}), flush=True)

        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators import runner

        # Keep any unexpected runner rejection artifact inside the audit scope.
        runner.REJECT_DIR = out / "runtime_rejections"
        bundle = runner.GeneratorBundle(
            task_id=TASK, rule_task_id=TASK, rule_source=rule,
            rule_callable_text=runner.wrap_rule(rule),
            rule_file=str(canon_path) + f":{line_no}", generator_module=gen,
        )
        with RacketBridge() as bridge:
            bridge.eval_text(f"(define __audit_rule {bundle.rule_callable_text})")
            report["runtime_identity"] = bridge.runtime_identity
            canonical_checks = []
            for split in ("train", "test"):
                for pi, pair in enumerate(row[split]):
                    actual = runner._apply_rule(bridge, "__audit_rule", pair["input"])
                    assert actual == pair["output"], f"Canonical {split}[{pi}] mismatch"
                    assert gen.self_check(pair["input"]) == []
                    canonical_checks.append({
                        "split": split, "pair_index": pi,
                        "racket_output": actual, "stored_label_equal": True,
                        "eight_rival_equal": recolor_eight_connected_l(pair["input"]) == actual,
                    })
            report["canonical_checks"] = canonical_checks
            if not candidates:
                report["status"] = "no_connectivity_counterexample_found_in_bound"
                report["exit_code"] = 0
            else:
                seed, screened_grids = candidates[0]
                lesson = runner.run_one(
                    TASK, seed, 0, n_train=5, n_test=1, bundle=bundle,
                    bridge=bridge, fn_name="__audit_rule", difficulty="easy",
                )
                pairs = lesson["train"] + lesson["test"]
                assert [p["input"] for p in pairs] == screened_grids
                assert lesson["sampling"]["rejections"] == []
                assert all(gen.self_check(p["input"]) == [] for p in pairs)
                results = []
                for pi, pair in enumerate(pairs):
                    predicted = recolor_eight_connected_l(pair["input"])
                    results.append({
                        "split": "train" if pi < 5 else "test", "pair_index": pi if pi < 5 else 0,
                        "sample_index": pi, "rival_prediction": predicted,
                        "rival_equal_racket": predicted == pair["output"],
                        "changed_cells": differences(pair["output"], predicted),
                        "observed_axes": gen.observe_overrides(pair["input"]),
                        "self_check": gen.self_check(pair["input"]),
                        "yellow_four_components": connected_components(pair["input"], 4),
                        "yellow_eight_components": connected_components(pair["input"], 8),
                    })
                assert all(r["rival_equal_racket"] for r in results[:5])
                assert not results[5]["rival_equal_racket"]
                witness = {
                    "schema": "arcpuzzles-concrete-teaching-counterexample-v1",
                    "source": report["source"], "racket_runtime": report["runtime_identity"],
                    "rival": "yellow exact L-triomino recolor with eight-way same-color connectivity",
                    "lesson": lesson, "lesson_sha256": json_hash(lesson),
                    "rival_results": results,
                    "generator_lesson_identifiable_reasons": gen.lesson_identifiable(lesson["train"], lesson["test"][0]),
                }
                write_json(out / "connectivity_counterexample.json", witness)
                report["witness"] = {
                    "path": "connectivity_counterexample.json", "seed": seed,
                    "train_agreement": [r["rival_equal_racket"] for r in results[:5]],
                    "query_agreement": results[5]["rival_equal_racket"],
                    "query_differing_cell_count": len(results[5]["changed_cells"]),
                    "lesson_identifiable_reasons": witness["generator_lesson_identifiable_reasons"],
                    "sampling": lesson["sampling"],
                }
                report["status"] = "reproduced_ordered_production_teaching_defect"
                report["exit_code"] = 1
        report["finished_unix"] = time.time()
        write_json(report_path, report)
        print(json.dumps({key: report.get(key) for key in ("status", "exit_code", "witness")}))
        return report["exit_code"]
    except Exception as exc:
        report.update(status="error", exit_code=2,
                      error={"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
                      finished_unix=time.time())
        write_json(report_path, report)
        print(report["error"]["traceback"], file=sys.stderr)
        return 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", type=int, default=100)
    raise SystemExit(main(parser.parse_args()))

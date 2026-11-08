"""Replayable, source-bound Racket census and findings-only audit reproducer.

Run from repo with the packet's run_with_racket.py wrapper. Public challenges
contain inputs only; reference answers and rival outputs go in private files.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import traceback

TASK = "7b6758552009"
AUDITS = ("410efa4c3988", "c47d6176a161")
REPO = Path(__file__).resolve().parents[3]


def positive(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("samples must be a positive integer")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def norm(grid):
    return [[int(v) for v in row] for row in grid]


def pairs(row: dict) -> list[dict]:
    result = []
    for split in ("train", "test"):
        entries = row.get(split, [])
        if isinstance(entries, dict):
            entries = [entries]
        result.extend({"input": norm(p["input"]), "output": norm(p["output"])} for p in entries)
    return result


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(args) -> dict:
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime

    selected = [TASK, *AUDITS] if args.audits else [TASK]
    with tempfile.TemporaryDirectory(prefix="palette-review-relocated-") as directory:
        runtime = Path(directory)
        manifest = prepare_runtime(Catalog(REPO), runtime, task_ids=selected)
        sys.path.insert(0, str(runtime))
        from arc_repl.racket_bridge import RacketBridge
        from scripts.rule_smoke import rule_application

        rows = {}
        for line in (runtime / "data/canonical/puzzles.jsonl").open():
            row = json.loads(line)
            if row["task_id"] in selected:
                rows[row["task_id"]] = row
        modules = {tid: load_module(runtime / f"puzzle_generators/per_puzzle/{tid}/generator.py", f"probe_{tid}") for tid in selected}
        current = modules[TASK]
        report = {"schema": "palette-review-census-v1", "task_id": TASK,
                  "samples_per_band": args.samples, "seed_base": args.seed,
                  "source_sha256": {tid: digest(runtime / f"puzzle_generators/per_puzzle/{tid}/generator.py") for tid in selected},
                  "canonical_ledger_sha256": digest(runtime / "data/canonical/puzzles.jsonl"),
                  "rule_sha256": hashlib.sha256(rows[TASK]["program_solution"].encode()).hexdigest(),
                  "runtime_manifest_sha256": hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
                  "oracle_calls": 0, "oracle_mismatches": [], "census": {}}
        bridge = RacketBridge(timeout=10, startup_timeout=30)
        try:
            report["runtime_identity"] = bridge.runtime_identity
            def oracle(tid, grid):
                report["oracle_calls"] += 1
                return bridge.eval_text(rule_application(rows[tid]["program_solution"], grid))

            canonical = pairs(rows[TASK])
            for i, pair in enumerate(canonical):
                actual = oracle(TASK, pair["input"])
                if actual != pair["output"]:
                    report["oracle_mismatches"].append({"source": "canonical", "index": i, "output": actual})
            report["canonical_pairs_checked"] = len(canonical)
            report["canonical_shortcut_fits"] = {
                name: sum(rival(p["input"]) == p["output"] for p in canonical)
                for name, rival in current.CANONICAL_SHORTCUTS.items()}

            versions = [("revised", current)]
            baseline = args.baseline
            if baseline is None:
                candidate = REPO.parent / f".review/baseline/repo/generators/{TASK}/generator.py"
                baseline = candidate if candidate.is_file() else None
            if baseline is not None:
                report["baseline_source_sha256"] = digest(baseline)
                versions.append(("baseline", load_module(baseline, "probe_baseline")))
            witnesses = {}
            metamorphic_checked = 0
            for version, module in versions:
                statistics = Counter()
                sizes, profiles, seen = Counter(), Counter(), set()
                rivals = Counter({name: 0 for name in current.SEMANTIC_RIVALS})
                per_band = {}
                for band in ("easy", "medium", "hard"):
                    band_counts = Counter()
                    for index in range(args.samples):
                        seed = args.seed + index
                        grid = module.generate(seed, index, difficulty=band)
                        reference = oracle(TASK, grid)
                        mirror = current.rule_mirror(grid)
                        if reference != mirror:
                            report["oracle_mismatches"].append({"source": version, "band": band, "seed": seed,
                                                                 "sample_index": index, "input": grid, "racket": reference, "mirror": mirror})
                        objs = current._components(grid)
                        statistics["draws"] += 1
                        statistics["selfcheck_rejections"] += bool(module.self_check(grid))
                        statistics["two_components"] += len(objs) == 2
                        statistics["repeated_colors"] += len({o["color"] for o in objs}) < len(objs)
                        statistics["left_column_ties"] += len({o["left"] for o in objs}) < len(objs)
                        statistics["old_fixed_anchor_pair_present"] += bool(grid[1][0] and grid[-2][0])
                        sizes.update(len(obj["cells"]) for obj in objs)
                        seen.add(tuple(map(tuple, grid)))
                        if hasattr(module, "schedule_profile"):
                            profiles[module.schedule_profile(seed, index, band)] += 1
                        for name, rival in current.SEMANTIC_RIVALS.items():
                            alternative = rival(grid)
                            if alternative != reference:
                                rivals[name] += 1
                                band_counts[name] += 1
                                if version == "revised" and name not in witnesses:
                                    witnesses[name] = {"id": name, "task_id": TASK, "seed": seed, "sample_index": index,
                                                       "difficulty": band, "input": grid, "output": reference, "rival_output": alternative}
                        if version == "revised" and index < 20:
                            # Translation leaves ordering unchanged; color permutation commutes
                            # with the palette extraction. Both are checked against real Racket.
                            pad = [[0] * (len(grid[0]) + 3)] + [[0, 0] + row + [0] for row in grid]
                            shifted = oracle(TASK, pad)
                            recolored = [[0 if v == 0 else v % 9 + 1 for v in row] for row in grid]
                            changed = oracle(TASK, recolored)
                            expected_color = [[v % 9 + 1 for v in row] for row in reference]
                            if shifted != reference or changed != expected_color:
                                report["oracle_mismatches"].append({"source": "metamorphic", "seed": seed, "sample_index": index, "band": band})
                            metamorphic_checked += 2
                    per_band[band] = dict(band_counts)
                report["census"][version] = {**dict(statistics), "unique_inputs": len(seen),
                    "component_size_histogram": dict(sizes), "scheduled_profiles": dict(profiles),
                    "rival_disagreements": dict(rivals), "per_band_rival_disagreements": per_band}
            report["metamorphic_checks"] = metamorphic_checked

            manual = [[0] * 10 for _ in range(6)]
            manual[1][1], manual[1][4], manual[1][7] = 4, 7, 4
            witnesses["minimal_repeated_color"] = {
                "id": "minimal_repeated_color", "task_id": TASK, "kind": "handwritten_within_sampler_bounds",
                "input": manual, "output": oracle(TASK, manual), "rival_output": current.SEMANTIC_RIVALS["unique_colors"](manual)}
            write(args.out / "witnesses.private.json", witnesses)
            with (args.out / "challenges.jsonl").open("w") as handle:
                for name, case in witnesses.items():
                    handle.write(json.dumps({"id": name, "task_id": TASK, "input": case["input"]}) + "\n")
            report["witness_ids"] = sorted(witnesses)

            if args.audits:
                maze, legend = modules[AUDITS[0]], modules[AUDITS[1]]
                illegal_passable = [list(map(int, row)) for row in ("5555555", "5550555", "5201035", "5555555", "5555555")]
                maze_case = {"input": illegal_passable, "self_check": maze.self_check(illegal_passable),
                             "racket_output": oracle(AUDITS[0], illegal_passable),
                             "kind": "out-of-grammar palette falsely accepted by checker"}
                saved = maze._has_tie_cell
                try:
                    maze._has_tie_cell = lambda grid, a, b: False
                    fallback = maze.generate(0, 0, difficulty="easy", grid_h=8, grid_w=10)
                finally:
                    maze._has_tie_cell = saved
                fallback_case = {"input": fallback, "self_check": maze.self_check(fallback),
                                 "racket_output": oracle(AUDITS[0], fallback),
                                 "kind": "forced rejection-loop exhaustion; not a naturally observed seed"}
                axis_identical = sum(
                    maze.generate(i, i, difficulty=band, seed_distance=2) == maze.generate(i, i, difficulty=band, seed_distance=8)
                    for band in ("easy", "medium", "hard") for i in range(16))

                def legend_rival(grid):
                    output = [row[:] for row in grid]
                    for r in range(1, len(grid)):
                        for c in range(1, len(grid[0])):
                            output[r][c] = grid[r][0] if grid[r][0] == grid[0][c] else 0
                    output[1][1] = 0  # forced-mismatch shortcut in the generator
                    return output
                legend_canonical = pairs(rows[AUDITS[1]])
                canon_matches = 0
                for pair in legend_canonical:
                    reference = oracle(AUDITS[1], pair["input"])
                    assert reference == pair["output"]
                    canon_matches += legend_rival(pair["input"]) == reference
                generated_matches = generated_count = 0
                for band in ("easy", "medium", "hard"):
                    for index in range(min(50, args.samples)):
                        grid = legend.generate(args.seed + index, index, difficulty=band)
                        generated_matches += legend_rival(grid) == oracle(AUDITS[1], grid)
                        generated_count += 1
                legend_input = [[0, 1, 2, 3], [1, 0, 0, 0], [2, 0, 0, 0], [1, 0, 0, 0]]
                legend_case = {"input": legend_input, "self_check": legend.self_check(legend_input),
                               "racket_output": oracle(AUDITS[1], legend_input), "rival_output": legend_rival(legend_input),
                               "canonical_rival_matches": canon_matches, "canonical_pairs": len(legend_canonical),
                               "generated_rival_matches": generated_matches, "generated_pairs": generated_count}
                assert maze_case["self_check"] == []
                assert not any(v for row in maze_case["racket_output"] for v in row)
                assert fallback_case["self_check"]
                assert legend_case["self_check"] == [] and legend_case["racket_output"] != legend_case["rival_output"]
                write(args.out / "audit_findings.json", {AUDITS[0]: {"palette_mismatch": maze_case,
                      "fallback_parity": fallback_case, "ignored_seed_distance_pairs": axis_identical, "override_pairs_checked": 48},
                      AUDITS[1]: legend_case})
            report["passed"] = not report["oracle_mismatches"] and all(
                report["census"]["revised"]["rival_disagreements"][name] > 0 for name in current.SEMANTIC_RIVALS)
            write(args.out / "summary.json", report)
            return report
        finally:
            bridge.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=positive, default=200, help="draws per difficulty band per version")
    parser.add_argument("--seed", type=int, default=20260928)
    parser.add_argument("--baseline", type=Path, help="optional earlier generator; defaults to immutable packet baseline when present")
    parser.add_argument("--audits", action="store_true", help="replay the two assigned findings-only audits")
    parser.add_argument("--out", type=Path, required=True, help="new directory, never overwritten")
    args = parser.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    try:
        report = run(args)
    except Exception as exc:
        write(args.out / "failure.json", {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
        raise
    print(json.dumps({"passed": report["passed"], "oracle_calls": report["oracle_calls"],
                      "summary": str(args.out / "summary.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

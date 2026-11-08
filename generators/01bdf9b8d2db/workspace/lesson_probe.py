#!/usr/bin/env python3
"""Source-bound lesson and shortcut audit for generator 01bdf9b8d2db.

The probe reproduces the semantic gate's current lesson sampler (100 lessons per
band by default), but records every denominator, unique-input count, declared
rival, canonical fit, witness hit, and source hash.  Its Python flood fill is an
independent supplementary oracle.  With --racket, every canonical and generated
input is also executed by the selected canonical Racket source in one staged
runtime; there is no Python fallback.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TASK = "01bdf9b8d2db"
ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators" / TASK
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
sys.path.insert(0, str(ROOT / "src"))

BANDS = ("easy", "medium", "hard")
LESSON_STRIDE = 11


def _sha_json(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_generator(path: Path | None = None):
    source = Path(path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_01bdf9b8d2db", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def canonical_row() -> dict:
    ledger = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise ValueError(f"canonical task {TASK} is absent")


def _norm_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    test = row.get("test") or []
    if isinstance(test, dict):
        test = [test]
    return [
        {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
        for pair in [*(row.get("train") or []), *test]
    ]


def regions(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    answer = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                cr, cc = todo.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] != 5 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            answer.append(cells)
    return answer


def independent_output(grid):
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for cells in regions(grid):
        markers = [grid[r][c] for r, c in cells if grid[r][c] not in (0, 5)]
        if len(markers) != 1:
            raise ValueError(f"region has {len(markers)} markers, expected one")
        for r, c in cells:
            out[r][c] = markers[0]
    return out


def pinned_lesson_seed(band: str, lesson_index: int) -> int:
    # Mirrors shared/tools/canonical_profile_gate.py::_pinned_seed and
    # generator_semantic_gate.py::_lesson_plan.
    text = f"profile-floor:v1:{TASK}:lesson:{band}:{lesson_index}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:12], 16)


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-lesson-probe-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = stage / "probe-request.json"
        request.write_text(json.dumps({"program": program, "grids": grids}))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("probe-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs, separators=(",", ":")))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=1200)
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(
                f"Racket batch failed exit={result['exit_code']} timed_out={result['timed_out']}: "
                f"{result['stderr'][-2000:]} {result['stdout'][-2000:]}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError(f"Racket returned {len(outputs)} outputs for {len(grids)} inputs")
        return outputs


def audit(module, lessons_per_band: int) -> tuple[dict, list]:
    pairs = canonical_pairs()
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(module, "SEMANTIC_WITNESSES", {}))

    canonical = {
        "pairs": len(pairs),
        "self_check_failures": [],
        "independent_oracle_mismatches": [],
        "shortcut_mismatches": {name: [] for name in shortcuts},
    }
    for index, pair in enumerate(pairs):
        reasons = module.self_check(deepcopy(pair["input"]))
        if reasons:
            canonical["self_check_failures"].append({"pair": index, "reasons": reasons})
        if independent_output(pair["input"]) != pair["output"]:
            canonical["independent_oracle_mismatches"].append(index)
        for name, rival in shortcuts.items():
            if rival(deepcopy(pair["input"])) != pair["output"]:
                canonical["shortcut_mismatches"][name].append(index)

    all_grids: dict[str, list[list[int]]] = {}
    by_band = {}
    counterexamples = {}
    for band in BANDS:
        counts = Counter()
        unique = set()
        schedule_counts = Counter()
        witness_counts = Counter()
        competitor_counts = {
            name: Counter() for name in competitors
        }
        hook_disagreements = []
        for lesson_index in range(lessons_per_band):
            seed = pinned_lesson_seed(band, lesson_index)
            start = lesson_index * LESSON_STRIDE
            grids = [
                module.generate(seed, start + offset, difficulty=band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            outputs = [independent_output(grid) for grid in grids]
            demos = [
                {"input": deepcopy(grid), "output": deepcopy(output)}
                for grid, output in zip(grids[:-1], outputs[:-1])
            ]
            query = {"input": deepcopy(grids[-1]), "output": deepcopy(outputs[-1])}
            reasons = module.lesson_identifiable(deepcopy(demos), deepcopy(query))
            counts["lessons"] += 1
            counts["hook_identifiable"] += not reasons
            counts["hook_unidentifiable"] += bool(reasons)
            lesson_survivors = []
            for offset, grid in enumerate(grids):
                digest = _sha_json(grid)
                unique.add(digest)
                all_grids.setdefault(digest, grid)
                counts["generated_inputs"] += 1
                counts["self_check_failures"] += bool(module.self_check(deepcopy(grid)))
                counts["nondeterministic"] += (
                    grid != module.generate(seed, start + offset, difficulty=band)
                )
                schedule_counts[module.schedule_profile(seed, start + offset, band)] += 1
                for witness_name, witness in witnesses.items():
                    witness_counts[witness_name] += bool(witness(deepcopy(grid)))
                for name, rival in competitors.items():
                    rival_output = rival(deepcopy(grid))
                    disagree = rival_output != outputs[offset]
                    competitor_counts[name]["input_disagreements"] += disagree
                    competitor_counts[name]["input_agreements"] += not disagree
                    if disagree and name not in counterexamples:
                        counterexamples[name] = {
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start + offset,
                            "input": grid,
                            "intended_python": outputs[offset],
                            "rival_output": rival_output,
                        }
            for name, rival in competitors.items():
                fits_demos = all(
                    rival(deepcopy(pair["input"])) == pair["output"]
                    for pair in demos
                )
                agrees_query = rival(deepcopy(query["input"])) == query["output"]
                competitor_counts[name]["survived_demos"] += fits_demos
                competitor_counts[name]["refuted_by_demos"] += not fits_demos
                competitor_counts[name]["survived_all"] += fits_demos and agrees_query
                competitor_counts[name]["query_discriminates"] += fits_demos and not agrees_query
                if fits_demos:
                    lesson_survivors.append(name)
            expected_identifiable = not lesson_survivors
            if bool(not reasons) != expected_identifiable and len(hook_disagreements) < 10:
                hook_disagreements.append({
                    "lesson_index": lesson_index,
                    "seed": seed,
                    "sample_index": start,
                    "hook_reasons": reasons,
                    "survivors": lesson_survivors,
                })
        counts["unique_inputs"] = len(unique)
        by_band[band] = {
            "counts": dict(counts),
            "schedule_profiles": dict(schedule_counts),
            "witness_hits": dict(witness_counts),
            "competitors": {name: dict(stats) for name, stats in competitor_counts.items()},
            "hook_vs_competitor_disagreements": hook_disagreements,
        }

    report = {
        "schema": "01bdf9b8d2db-source-bound-lesson-probe-v1",
        "task_id": TASK,
        "lessons_per_band": lessons_per_band,
        "examples_per_lesson": module.EXAMPLES_NEEDED,
        "query_examples_per_lesson": 1,
        "generated_inputs_per_band": lessons_per_band * (module.EXAMPLES_NEEDED + 1),
        "sampler": {
            "bands": list(BANDS),
            "seed_formula": "int(sha256('profile-floor:v1:TASK:lesson:BAND:k')[:12], 16)",
            "lesson_start_sample_index": "k * 11",
            "within_lesson_sample_indexes": f"start..start+{module.EXAMPLES_NEEDED}",
            "overrides": {},
            "difficulty": "band passed to every draw",
            "overlap": "none; stride 11 exceeds the 4-input lesson block",
        },
        "domain_limits": {
            "axes": module.AXES,
            "schedule_profiles": list(module.SCHEDULE_PROFILES),
            "strict_scope": "self_check lawful manifold only; no universal induction claim",
            "declared_shortcuts": sorted(shortcuts),
            "declared_competitors": sorted(competitors),
            "declared_witnesses": sorted(witnesses),
        },
        "canonical": canonical,
        "by_band": by_band,
        "pooled_unique_inputs": len(all_grids),
        "counterexamples": counterexamples,
        "racket": {"status": "not_requested", "checked": 0, "mismatches": []},
    }
    return report, list(all_grids.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--counterexample-out", type=Path)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.lessons_per_band < 100:
        parser.error("--lessons-per-band must be at least 100 for the review duty")

    module, source = load_generator(args.generator)
    report, generated = audit(module, args.lessons_per_band)
    row = canonical_row()
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["canonical_ledger_sha256"] = hashlib.sha256(
        (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").read_bytes()
    ).hexdigest()
    report["rule_hash"] = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]

    exit_code = 0
    if report["canonical"]["self_check_failures"]:
        exit_code = 1
    if report["canonical"]["independent_oracle_mismatches"]:
        exit_code = 1
    if any(report["canonical"]["shortcut_mismatches"].values()):
        exit_code = 1
    for band in BANDS:
        row_stats = report["by_band"][band]
        if row_stats["counts"].get("self_check_failures"):
            exit_code = 1
        if row_stats["counts"].get("nondeterministic"):
            exit_code = 1
        if row_stats["counts"].get("hook_unidentifiable"):
            exit_code = 1
        if row_stats["hook_vs_competitor_disagreements"]:
            exit_code = 1

    if args.racket:
        try:
            grids = [pair["input"] for pair in canonical_pairs()] + generated
            outputs = racket_outputs(grids)
            expected = [independent_output(grid) for grid in grids]
            mismatches = [
                index for index, (actual, wanted) in enumerate(zip(outputs, expected))
                if actual != wanted
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "canonical_checked": len(canonical_pairs()),
                "generated_checked": len(generated),
                "mismatches": mismatches[:100],
            }
            if mismatches:
                exit_code = 1
            generated_outputs = outputs[len(canonical_pairs()):]
            by_digest = {
                _sha_json(grid): output
                for grid, output in zip(generated, generated_outputs)
            }
            for counterexample in report["counterexamples"].values():
                digest = _sha_json(counterexample["input"])
                counterexample["intended_racket"] = by_digest[digest]
                counterexample["intended_racket_verified_in_batch"] = (
                    by_digest[digest] == counterexample["intended_python"]
                )
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed", "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    if args.counterexample_out:
        args.counterexample_out.parent.mkdir(parents=True, exist_ok=True)
        args.counterexample_out.write_text(json.dumps({
            "schema": "01bdf9b8d2db-shortcut-counterexample-v1",
            "task_id": TASK,
            "generator_sha256": report["generator_sha256"],
            "rule_hash": report["rule_hash"],
            "probe_sha256": report["probe_sha256"],
            "counterexamples": report["counterexamples"],
            "racket": report["racket"],
        }, indent=2) + "\n")
    print(json.dumps({
        "generator_sha256": report["generator_sha256"],
        "probe_sha256": report["probe_sha256"],
        "canonical": report["canonical"],
        "by_band": report["by_band"],
        "pooled_unique_inputs": report["pooled_unique_inputs"],
        "racket": report["racket"],
    }, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

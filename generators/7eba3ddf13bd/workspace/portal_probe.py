"""Source-bound portal audit against the selected canonical Racket program.

Run from the packet with run_with_racket.py (or configure a system Racket):
  python3 run_with_racket.py python3 generators/7eba3ddf13bd/workspace/portal_probe.py \
      --seeds 200 --out ../checks/portal-probe
Use --generator PATH to compare a frozen baseline using exactly the same inputs
protocol and the revised diagnostic analyzer. No source file is changed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import traceback

TASK_ID = "7eba3ddf13bd"
REPO = Path(__file__).resolve().parents[3]


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed(band: str, index: int) -> int:
    raw = f"portal-review-probe-v1:{band}:{index}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:12], 16)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=_positive, default=40, help="independent seeds per difficulty band")
    parser.add_argument("--generator", type=Path, help="optional frozen/alternative generator.py to compare")
    parser.add_argument("--cases", type=Path, help="additional JSON list of {name,input,expected?} fixtures")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; never overwritten")
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if out.exists():
        parser.error(f"output already exists: {out}")
    source = (args.generator or REPO / f"generators/{TASK_ID}/generator.py").resolve()
    if not source.is_file() or source.is_symlink():
        parser.error(f"generator is not a regular source file: {source}")
    if args.cases is not None and not args.cases.is_file():
        parser.error(f"cases file does not exist: {args.cases}")
    out.mkdir(parents=True)
    summary = {"schema": "arcpuzzles-portal-review-probe-v1", "task_id": TASK_ID,
               "source": {"generator_sha256": _sha(source)}, "seeds_per_band": args.seeds,
               "seed_protocol": "sha256(portal-review-probe-v1:band:index)[:12]; sample_index=11*index+7",
               "failures": [], "counts": {}, "rivals": {}, "witnesses": {}}
    counts = Counter()
    stats = Counter()
    unique_inputs = set()
    times = []
    bridge = None
    started = time.perf_counter()
    try:
        sys.path.insert(0, str(REPO / "src"))
        from arcpuzzles import Catalog
        from arcpuzzles.runtime import prepare_runtime
        with tempfile.TemporaryDirectory(prefix="portal-review-probe-") as temporary:
            runtime = Path(temporary)
            prepare_runtime(Catalog(REPO), runtime, TASK_ID)
            sys.path.insert(0, str(runtime))
            from arc_repl.racket_bridge import RacketBridge
            from puzzle_generators.rule_wrap import wrap_rule
            from scripts.coder_synth_verify import _as_pairs, _norm_grid
            analyzer_path = runtime / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py"
            analyzer = _load(analyzer_path, "portal_review_analyzer")
            target_path = runtime / "probe_target.py"
            target_path.write_bytes(source.read_bytes())
            target = _load(target_path, "portal_review_target")
            if getattr(target, "TASK_ID", None) != TASK_ID:
                raise ValueError("the probe is scoped to the selected portal task")
            canonical = [json.loads(line) for line in (runtime / "data/canonical/puzzles.jsonl").read_text().splitlines()
                         if line.strip() and json.loads(line).get("task_id") == TASK_ID]
            if len(canonical) != 1:
                raise ValueError("expected exactly one canonical authority row")
            row = canonical[0]
            code = row["program_solution"]
            summary["source"].update({
                "generator_version": getattr(target, "VERSION", None),
                "analyzer_sha256": _sha(analyzer_path),
                "canonical_rule_hash": hashlib.sha256(" ".join(code.split()).encode()).hexdigest()[:12],
                "canonical_program_sha256": hashlib.sha256(code.encode()).hexdigest(),
                "prelude_sha256": _sha(runtime / "arc_repl/racket_prelude/arc-prelude.rkt"),
            })
            pairs = [{"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
                     for split in ("train", "test") for pair in _as_pairs(row.get(split))]
            summary["rivals"] = {name: {"canonical_matches": 0, "generated_disagreements": 0}
                                 for name in analyzer.SEMANTIC_RIVALS}
            bridge = RacketBridge()
            bridge.eval_text(f"(define __portal_review_rule {wrap_rule(code)})")
            with (out / "cases.jsonl").open("w", encoding="utf-8") as records:
                def inspect_case(origin, grid, *, expected=None, **meta):
                    before = copy.deepcopy(grid)
                    bridge.define_grid("__portal_review_input", grid)
                    tick = time.perf_counter()
                    truth = bridge.eval_text("(__portal_review_rule __portal_review_input)")
                    times.append(time.perf_counter() - tick)
                    predicted = analyzer.rule_mirror(grid)
                    diagnostics = analyzer.route_diagnostics(grid)
                    counts[origin] += 1
                    counts["racket_calls"] += 1
                    counts["oracle_agreements"] += predicted == truth
                    failures = []
                    if predicted != truth:
                        failures.append("python_racket_mismatch")
                    if expected is not None and truth != expected:
                        failures.append("expected_racket_mismatch")
                    if grid != before:
                        failures.append("input_mutation")
                    if origin == "generated":
                        findings = target.self_check(grid)
                        if findings:
                            failures.append("generator_self_check_rejected")
                        if truth == grid:
                            failures.append("identity_output")
                        stats[f"profile:{meta['profile']}"] += 1
                        stats[f"jumps:{len(diagnostics['used_portal_colors'])}"] += 1
                        stats[f"route_count:{diagnostics['shortest_route_count']}"] += 1
                        shape = (len(grid), len(grid[0]), len({v for line in grid for v in line}))
                        stats["canonical_profile"] += shape in {(7, 10, 5), (7, 11, 5)}
                        unique_inputs.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
                    rivals = {name: rival(grid) for name, rival in analyzer.SEMANTIC_RIVALS.items()}
                    for name, rival_output in rivals.items():
                        if origin == "canonical":
                            summary["rivals"][name]["canonical_matches"] += rival_output == truth
                        if origin == "generated" and rival_output != truth:
                            summary["rivals"][name]["generated_disagreements"] += 1
                            if name not in summary["witnesses"]:
                                summary["witnesses"][name] = {**meta, "input": grid, "output": truth,
                                                              "rival_output": rival_output}
                    record = {"origin": origin, **meta, "input": grid, "output": truth,
                              "oracle_match": predicted == truth, "failures": failures,
                              "diagnostics": {key: diagnostics[key] for key in
                                              ("distance", "plain_distance", "shortest_route_count",
                                               "used_portal_colors", "painted_cells", "portal_pair_count")}}
                    records.write(json.dumps(record, separators=(",", ":")) + "\n")
                    if failures:
                        summary["failures"].append({"origin": origin, **meta, "failures": failures})

                for i, pair in enumerate(pairs):
                    inspect_case("canonical", pair["input"], expected=pair["output"], index=i)
                # A paired intervention that preserves geometry and changes ONLY
                # portal color. This falsifies the strongest canonical shortcut.
                renamed = [[5 if v == 4 else v for v in line] for line in pairs[0]["input"]]
                expected = [[5 if v == 4 else v for v in line] for line in pairs[0]["output"]]
                inspect_case("intervention", renamed, expected=expected, name="canonical_portal_4_to_5")
                if args.cases:
                    summary["source"]["extra_cases_sha256"] = _sha(args.cases)
                    extras = json.loads(args.cases.read_text())
                    if not isinstance(extras, list):
                        raise ValueError("extra cases must be a JSON list")
                    for i, case in enumerate(extras):
                        inspect_case("fixture", case["input"], expected=case.get("expected"), name=case.get("name", str(i)))
                for band in ("easy", "medium", "hard"):
                    for i in range(args.seeds):
                        seed, sample_index = _seed(band, i), 11 * i + 7
                        try:
                            grid = target.generate(seed, sample_index, difficulty=band)
                            if target.generate(seed, sample_index, difficulty=band) != grid:
                                summary["failures"].append({"band": band, "seed": seed, "sample_index": sample_index,
                                                            "failures": ["nondeterministic_generation"]})
                            profile_fn = getattr(target, "schedule_profile", None)
                            profile = profile_fn(seed, sample_index, band) if profile_fn else "undeclared"
                            inspect_case("generated", grid, band=band, seed=seed, sample_index=sample_index, profile=profile)
                        except Exception as exc:
                            counts["generation_or_execution_errors"] += 1
                            summary["failures"].append({"band": band, "seed": seed, "sample_index": sample_index,
                                                        "failures": [repr(exc)]})
            bridge.close()
            bridge = None
    except Exception:
        summary["fatal_error"] = traceback.format_exc()
    finally:
        if bridge is not None:
            bridge.close()
        summary["counts"] = dict(counts)
        summary["generated_statistics"] = {**dict(stats), "unique_inputs": len(unique_inputs)}
        summary["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        if times:
            ordered = sorted(times)
            summary["racket_latency_ms"] = {"median": round(1000 * ordered[len(ordered) // 2], 3),
                                            "p95": round(1000 * ordered[min(len(ordered) - 1, int(len(ordered) * .95))], 3)}
        summary["passed"] = not summary["failures"] and "fatal_error" not in summary
        _write(out / "report.json", summary)
        _write(out / "witnesses.json", summary["witnesses"])
    print(json.dumps({key: summary[key] for key in ("passed", "counts", "generated_statistics")}, indent=2))
    if summary.get("fatal_error"):
        print(summary["fatal_error"], file=sys.stderr)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

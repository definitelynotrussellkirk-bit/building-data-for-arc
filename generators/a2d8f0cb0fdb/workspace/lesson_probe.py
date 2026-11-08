#!/usr/bin/env python3
"""Source-bound 100-lessons-per-band rival census for a2d8f0cb0fdb.

The parent stages the selected task with ``arcpuzzles.runtime.prepare_runtime``.
The worker materializes the production 3-demo/1-query lesson shape through
``runner.run_one`` and labels every grid with the selected canonical Racket
authority. Rival and witness declarations are read from the staged generator.

This is a finite deterministic census, not a proof of universal induction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

TASK_ID = "a2d8f0cb0fdb"
BANDS = ("easy", "medium", "hard")
SCHEMA = "a2d8f0cb0fdb-source-bound-lesson-census-v1"
SAMPLE_STRIDE = 11
SCHEDULE_LENGTH = 5


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _grid_hash(grid: Any) -> str:
    return _hash_bytes(json.dumps(grid, separators=(",", ":")).encode())


def _seed(band: str, ordinal: int) -> int:
    payload = f"{TASK_ID}|{SCHEMA}|{band}|{ordinal}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _plan(per_band: int, n_demos: int) -> list[dict[str, Any]]:
    return [
        {
            "band": band,
            "ordinal": ordinal,
            "seed": _seed(band, ordinal),
            "sample_index": ordinal * SAMPLE_STRIDE,
            "n_demos": n_demos,
            "n_queries": 1,
        }
        for band in BANDS
        for ordinal in range(per_band)
    ]


def _canonical_pairs(path: Path) -> list[dict]:
    with path.open() as stream:
        for line in stream:
            if TASK_ID not in line:
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            def decode(grid):
                if grid and isinstance(grid[0], str):
                    return [[int(ch) for ch in line] for line in grid]
                return grid
            return [
                {"input": decode(pair["input"]), "output": decode(pair["output"])}
                for pair in list(row["train"]) + test
            ]
    raise ValueError(f"canonical row {TASK_ID} not found")


def _worker(request_path: Path, result_path: Path) -> int:
    request = json.loads(request_path.read_text())
    plan = request["plan"]

    from puzzle_generators import runner

    bundle = runner._load_bundle(TASK_ID)
    module = bundle.generator_module
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}) or {})
    witnesses = dict(getattr(module, "SEMANTIC_WITNESSES", {}) or {})
    hook = getattr(module, "lesson_identifiable", None)
    observe = getattr(module, "observe_overrides", None)

    report: dict[str, Any] = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": _hash_bytes(Path(module.__file__).read_bytes()),
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "racket_rule": {
            "source": bundle.rule_file,
            "source_sha256": _hash_bytes(bundle.rule_source.encode()),
            "normalized_sha12": _hash_bytes(" ".join(bundle.rule_source.split()).encode())[:12],
        },
        "sampler": {
            "bands": list(BANDS),
            "lesson_assembly": "runner.run_one: 3 sequential demos plus 1 sequential query",
            "labels": "selected canonical Racket authority through one persistent bridge",
            "seed_formula": f"uint64(sha256('{TASK_ID}|{SCHEMA}|<band>|<ordinal>')[:8])",
            "sample_index_formula": f"ordinal * {SAMPLE_STRIDE}",
            "sample_stride": SAMPLE_STRIDE,
            "schedule_length": SCHEDULE_LENGTH,
            "cyclic_start_policy": "sample_index = ordinal*11; gcd(11,5)=1, so 100 lessons cover each of the five starts exactly 20 times per band",
            "plan": plan,
        },
        "domain_limits": {
            "advertised_exact_axes": getattr(module, "AXES", {}),
            "generated_grammar": {
                "grid_h": "4..9",
                "grid_w": "5..12",
                "legend_target": "first nonzero row-0 color, always 2..9",
                "body_signal": "3..12 cells of value 1",
                "body_distractors": "0 or 2 non-{0,1} cells according to scene_profile",
                "scene_profiles": list(getattr(module, "SCENE_PROFILES", ())),
            },
            "claim_scope": "finite deterministic census only; no universal induction claim",
        },
        "declared": {
            "competitors": sorted(competitors),
            "canonical_shortcuts": sorted(shortcuts),
            "witnesses": sorted(witnesses),
        },
        "canonical_shortcut_fit": {},
        "bands": {},
        "totals": {},
        "failures": [],
        "limitations": [
            "The runner may advance sample_index after a rejected or duplicate pair; replay uses the recorded lesson start plus source hashes.",
            "The declared five-position schedule is audited through every cyclic start, but the census cannot exclude undeclared rival programs.",
            "Rival disagreement on this sample does not prove the demos uniquely determine the intended rule among all programs.",
        ],
    }

    canonical = _canonical_pairs(runner.CANONICAL_PUZZLES)
    for name, rival in shortcuts.items():
        fit = 0
        errors = []
        for index, pair in enumerate(canonical):
            try:
                fit += rival(pair["input"]) == pair["output"]
            except Exception as exc:
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        report["canonical_shortcut_fit"][name] = {
            "fits": fit,
            "total": len(canonical),
            "errors": errors,
        }
        if fit != len(canonical) or errors:
            report["failures"].append({"kind": "canonical_shortcut_fit", "name": name, "fit": fit, "errors": errors})

    per_band_hashes = {band: set() for band in BANDS}
    global_hashes = set()
    per_band = {
        band: {
            "lessons_requested": 0,
            "lessons_materialized": 0,
            "inputs": 0,
            "unique_inputs": 0,
            "duplicate_inputs": 0,
            "self_check_errors": 0,
            "observe_errors": 0,
            "unidentifiable_lessons": 0,
            "hook_errors": 0,
            "run_errors": 0,
            "axis_values": {axis: Counter() for axis in getattr(module, "AXES", {})},
            "witness_input_hits": Counter(),
            "witness_lesson_demo_hits": Counter(),
            "competitor_input_disagreements": Counter(),
            "competitor_input_agreements": Counter(),
            "competitor_lessons_refuted_by_demos": Counter(),
            "competitor_lessons_survived_demos": Counter(),
            "competitor_query_disagreements_after_survival": Counter(),
            "start_modulo_schedule": Counter(),
        }
        for band in BANDS
    }

    try:
        for lesson_index, spec in enumerate(plan):
            band = spec["band"]
            stats = per_band[band]
            stats["lessons_requested"] += 1
            stats["start_modulo_schedule"][str(spec["sample_index"] % SCHEDULE_LENGTH)] += 1
            try:
                instance = runner.run_one(
                    TASK_ID,
                    seed=spec["seed"],
                    sample_index=spec["sample_index"],
                    n_train=spec["n_demos"],
                    n_test=spec["n_queries"],
                    difficulty=band,
                    bundle=bundle,
                    bridge=bridge,
                    fn_name=fn_name,
                )
            except Exception as exc:
                stats["run_errors"] += 1
                if len(report["failures"]) < 24:
                    report["failures"].append({
                        "kind": "run_error",
                        "lesson": lesson_index,
                        "replay": spec,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                continue

            stats["lessons_materialized"] += 1
            demos = instance["train"]
            query = instance["test"][0]
            pairs = [("demo", pair) for pair in demos] + [("query", query)]
            demo_witness_hits = Counter()
            competitor_demo_fits = {name: True for name in competitors}
            competitor_query_agrees = {name: True for name in competitors}

            for split, pair in pairs:
                grid, authority = pair["input"], pair["output"]
                digest = _grid_hash(grid)
                global_hashes.add(digest)
                per_band_hashes[band].add(digest)
                stats["inputs"] += 1

                findings = list(module.self_check(grid) or [])
                if findings:
                    stats["self_check_errors"] += 1
                    if len(report["failures"]) < 24:
                        report["failures"].append({
                            "kind": "self_check",
                            "replay": spec,
                            "split": split,
                            "input_sha256": digest,
                            "findings": findings,
                        })

                if callable(observe):
                    try:
                        values = observe(grid)
                        for axis, value in values.items():
                            if axis in stats["axis_values"]:
                                stats["axis_values"][axis][str(value)] += 1
                    except Exception as exc:
                        stats["observe_errors"] += 1
                        if len(report["failures"]) < 24:
                            report["failures"].append({
                                "kind": "observe_error",
                                "replay": spec,
                                "split": split,
                                "error": f"{type(exc).__name__}: {exc}",
                            })

                for name, witness in witnesses.items():
                    try:
                        fired = bool(witness(grid))
                    except Exception as exc:
                        fired = False
                        if len(report["failures"]) < 24:
                            report["failures"].append({
                                "kind": "witness_error",
                                "name": name,
                                "replay": spec,
                                "error": f"{type(exc).__name__}: {exc}",
                            })
                    if fired:
                        stats["witness_input_hits"][name] += 1
                        if split == "demo":
                            demo_witness_hits[name] += 1

                for name, rival in competitors.items():
                    try:
                        agrees = rival(grid) == authority
                    except Exception as exc:
                        agrees = False
                        competitor_demo_fits[name] = False
                        competitor_query_agrees[name] = False
                        if len(report["failures"]) < 24:
                            report["failures"].append({
                                "kind": "competitor_error",
                                "name": name,
                                "replay": spec,
                                "split": split,
                                "error": f"{type(exc).__name__}: {exc}",
                            })
                    stats["competitor_input_agreements" if agrees else "competitor_input_disagreements"][name] += 1
                    if split == "demo":
                        competitor_demo_fits[name] &= agrees
                    else:
                        competitor_query_agrees[name] = agrees

            for name in witnesses:
                if demo_witness_hits[name]:
                    stats["witness_lesson_demo_hits"][name] += 1

            for name in competitors:
                if competitor_demo_fits[name]:
                    stats["competitor_lessons_survived_demos"][name] += 1
                    if not competitor_query_agrees[name]:
                        stats["competitor_query_disagreements_after_survival"][name] += 1
                else:
                    stats["competitor_lessons_refuted_by_demos"][name] += 1

            if callable(hook):
                try:
                    reasons = list(hook(demos, query) or [])
                except Exception as exc:
                    reasons = []
                    stats["hook_errors"] += 1
                    if len(report["failures"]) < 24:
                        report["failures"].append({
                            "kind": "hook_error",
                            "replay": spec,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                if reasons:
                    stats["unidentifiable_lessons"] += 1
                    if len(report["failures"]) < 24:
                        report["failures"].append({
                            "kind": "unidentifiable",
                            "replay": spec,
                            "reasons": reasons,
                            "survivors": [name for name, survived in competitor_demo_fits.items() if survived],
                        })
    finally:
        bridge.shutdown()

    total_counter = Counter()
    for band in BANDS:
        stats = per_band[band]
        stats["unique_inputs"] = len(per_band_hashes[band])
        stats["duplicate_inputs"] = stats["inputs"] - stats["unique_inputs"]
        for key, value in list(stats.items()):
            if isinstance(value, Counter):
                stats[key] = {str(k): int(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
            elif isinstance(value, dict) and key == "axis_values":
                stats[key] = {
                    axis: {str(k): int(v) for k, v in sorted(counter.items(), key=lambda kv: str(kv[0]))}
                    for axis, counter in value.items()
                }
            elif isinstance(value, int):
                total_counter[key] += value
        report["bands"][band] = stats

    report["totals"] = {str(k): int(v) for k, v in sorted(total_counter.items())}
    report["totals"]["unique_inputs_across_bands"] = len(global_hashes)
    report["totals"]["canonical_pairs_checked"] = len(canonical)

    # Every named competitor should be refuted by every complete lesson.
    for band in BANDS:
        for name in competitors:
            survived = report["bands"][band]["competitor_lessons_survived_demos"].get(name, 0)
            if survived:
                report["failures"].append({
                    "kind": "competitor_survived_lessons",
                    "band": band,
                    "name": name,
                    "count": survived,
                })

    result_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 1 if report["failures"] else 0


def _parent(args) -> int:
    root = _repo_root()
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    plan = _plan(args.per_band, args.demos)
    if SAMPLE_STRIDE % SCHEDULE_LENGTH == 0:
        raise RuntimeError("sample stride must rotate through cyclic schedule starts")
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-lesson-probe-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(root), stage, TASK_ID)
        shutil.copy2(Path(__file__), stage / "lesson_probe.py")
        (stage / "request.json").write_text(json.dumps({"plan": plan}, indent=2) + "\n")
        result = run_process(
            [sys.executable, "-B", "lesson_probe.py", "--worker", "request.json", "result.json"],
            stage,
            timeout=args.timeout,
        )
        if not (stage / "result.json").exists():
            raise RuntimeError(f"worker produced no report: stdout={result['stdout']} stderr={result['stderr']}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / "result.json", args.out)
        report = json.loads(args.out.read_text())
        print(json.dumps({
            "out": str(args.out),
            "generator_sha256": report["generator_sha256"],
            "totals": report["totals"],
            "failures": len(report["failures"]),
            "worker_exit": result["exit_code"],
            "worker_timed_out": result["timed_out"],
        }, indent=2))
        return max(int(result["exit_code"] != 0 or result["timed_out"]), int(bool(report["failures"])))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--worker", nargs=2, metavar=("REQUEST", "RESULT"))
    args = parser.parse_args()
    if args.worker:
        return _worker(Path(args.worker[0]), Path(args.worker[1]))
    if args.per_band < 100:
        parser.error("--per-band must be at least 100 for the required census")
    if args.demos != 3:
        parser.error("this task declares EXAMPLES_NEEDED=3; use --demos 3")
    if args.out is None:
        parser.error("--out is required")
    return _parent(args)


if __name__ == "__main__":
    raise SystemExit(main())

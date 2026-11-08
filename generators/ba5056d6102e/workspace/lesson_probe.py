#!/usr/bin/env python3
"""Source-bound, Racket-backed lesson census for ba5056d6102e.

The probe stages the final task through the public runtime copier, then builds
actual 3-demo/1-query lessons with ``puzzle_generators.runner.run_one``.  Rival
sets are read from the staged generator's declarations rather than copied here.
It is deliberately finite: it tests the named competitors over a pinned lesson
sample and does not claim universal rule identifiability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "ba5056d6102e"
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from arcpuzzles.catalog import Catalog  # noqa: E402
from arcpuzzles.runtime import prepare_runtime, run_process  # noqa: E402


CHILD = r'''
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path

from puzzle_generators import runner
from scripts.canonical_profile_gate import canonical_pairs
from scripts.coder_synth_verify import _grids_equal

TASK_ID = "ba5056d6102e"
BANDS = ("easy", "medium", "hard")
N_DEMOS = 3
N_QUERIES = 1
STRIDE = 11


def pinned_seed(task_id: str, band_key: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{task_id}:{band_key}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def grid_hash(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()


def main() -> int:
    request = json.loads(Path("lesson-probe-request.json").read_text())
    per_band = int(request["lessons_per_band"])
    gen = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}) or {})
    for name, fn in shortcuts.items():
        competitors.setdefault(name, fn)
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}) or {})

    canonical = canonical_pairs(TASK_ID)
    shortcut_canonical = {}
    for name, fn in sorted(shortcuts.items()):
        errors = []
        fits = 0
        for index, pair in enumerate(canonical):
            try:
                same = _grids_equal(fn(deepcopy(pair["input"])), pair["output"])
            except Exception as exc:
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
                continue
            fits += int(same)
        shortcut_canonical[name] = {
            "pairs": len(canonical),
            "fits": fits,
            "fits_all": fits == len(canonical) and not errors,
            "errors": errors,
        }

    bundle = runner._load_bundle(TASK_ID)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    rows = {}
    all_input_hashes = set()
    all_pair_hashes = set()
    failures = []
    try:
        for band in BANDS:
            input_hashes = set()
            pair_hashes = set()
            starts = Counter()
            pair_profiles = Counter()
            witness_hits = Counter()
            competitor_counts = {
                name: Counter(
                    refuted=0,
                    survived_demos=0,
                    survived_all=0,
                    query_discriminates=0,
                    errors=0,
                )
                for name in sorted(competitors)
            }
            identifiable = 0
            strict_pairs = 0
            materialized = 0
            for lesson_index in range(per_band):
                seed = pinned_seed(TASK_ID, f"lesson:{band}", lesson_index)
                sample_index = lesson_index * STRIDE
                starts[sample_index % len(gen.SCHEDULE_PROFILES)] += 1
                try:
                    instance = runner.run_one(
                        TASK_ID,
                        seed=seed,
                        sample_index=sample_index,
                        n_train=N_DEMOS,
                        n_test=N_QUERIES,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                        difficulty=band,
                    )
                except Exception as exc:
                    failures.append({
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    continue
                materialized += 1
                demos = instance["train"]
                query = instance["test"][0]
                reasons = gen.lesson_identifiable(demos, query)
                identifiable += int(reasons == [])
                if reasons:
                    failures.append({
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": sample_index,
                        "identifiability_reasons": list(reasons),
                    })

                pairs = demos + [query]
                for offset, pair in enumerate(pairs):
                    inp_hash = grid_hash(pair["input"])
                    pair_hash = hashlib.sha256(
                        (inp_hash + grid_hash(pair["output"])).encode()
                    ).hexdigest()
                    input_hashes.add(inp_hash)
                    pair_hashes.add(pair_hash)
                    all_input_hashes.add(inp_hash)
                    all_pair_hashes.add(pair_hash)
                    profile = gen.schedule_profile(
                        seed, sample_index + offset, difficulty=band
                    )
                    pair_profiles[str(profile)] += 1
                    strict_pairs += int(gen.strict_canonical_like(pair["input"]) == [])
                    for name, witness in witnesses.items():
                        try:
                            witness_hits[name] += int(bool(witness(pair["input"])))
                        except Exception as exc:
                            failures.append({
                                "band": band,
                                "lesson_index": lesson_index,
                                "witness": name,
                                "error": f"{type(exc).__name__}: {exc}",
                            })

                for name, rival in competitors.items():
                    counts = competitor_counts[name]
                    try:
                        fits_demos = all(
                            _grids_equal(
                                rival(deepcopy(pair["input"])), pair["output"]
                            )
                            for pair in demos
                        )
                        agrees_query = _grids_equal(
                            rival(deepcopy(query["input"])), query["output"]
                        )
                    except Exception as exc:
                        counts["errors"] += 1
                        failures.append({
                            "band": band,
                            "lesson_index": lesson_index,
                            "competitor": name,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                        continue
                    if fits_demos:
                        counts["survived_demos"] += 1
                        if agrees_query:
                            counts["survived_all"] += 1
                        else:
                            counts["query_discriminates"] += 1
                    else:
                        counts["refuted"] += 1

            rows[band] = {
                "requested_lessons": per_band,
                "materialized_lessons": materialized,
                "identifiable_lessons": identifiable,
                "unidentifiable_lessons": materialized - identifiable,
                "generated_pairs": materialized * (N_DEMOS + N_QUERIES),
                "unique_inputs": len(input_hashes),
                "unique_input_fraction": (
                    len(input_hashes) / (materialized * (N_DEMOS + N_QUERIES))
                    if materialized else 0.0
                ),
                "unique_pairs": len(pair_hashes),
                "strict_canonical_like_pairs": strict_pairs,
                "start_residues_mod_schedule": dict(sorted(starts.items())),
                "pair_schedule_profiles": dict(sorted(pair_profiles.items())),
                "witness_hits": dict(sorted(witness_hits.items())),
                "competitors": {
                    name: dict(counter) for name, counter in competitor_counts.items()
                },
            }
    finally:
        bridge.shutdown()

    generator_path = Path(gen.__file__)
    normalized_rule_hash = hashlib.sha256(
        " ".join(bundle.rule_source.split()).encode()
    ).hexdigest()[:12]
    report = {
        "schema": "ba5056d6102e-racket-lesson-census-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "normalized_selected_rule_hash": normalized_rule_hash,
        "rule_source": bundle.rule_file,
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": per_band,
            "n_demos": N_DEMOS,
            "n_queries": N_QUERIES,
            "seed_rule": "sha256('profile-floor:v1:' + task_id + ':lesson:' + band + ':' + k)[:12] as int",
            "sample_index_rule": "k * 11",
            "pair_indices": "sample_index through sample_index+3, as consumed by runner.run_one",
            "difficulty": "passed to every pair through runner.run_one",
            "outputs": "canonical selected Racket rule via one persistent RacketBridge",
            "competitors": "dynamic union of final generator LESSON_COMPETITORS and CANONICAL_SHORTCUTS",
        },
        "declared_axes": gen.AXES,
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "competitors": sorted(competitors),
        "witnesses": sorted(witnesses),
        "canonical_shortcut_check": shortcut_canonical,
        "per_band": rows,
        "totals": {
            "requested_lessons": per_band * len(BANDS),
            "materialized_lessons": sum(row["materialized_lessons"] for row in rows.values()),
            "identifiable_lessons": sum(row["identifiable_lessons"] for row in rows.values()),
            "unidentifiable_lessons": sum(row["unidentifiable_lessons"] for row in rows.values()),
            "generated_pairs": sum(row["generated_pairs"] for row in rows.values()),
            "unique_inputs": len(all_input_hashes),
            "unique_pairs": len(all_pair_hashes),
        },
        "failures": failures,
        "passed": not failures,
        "domain_limits": [
            "Finite census over declared competitors; it is not a proof against every possible shortcut.",
            "Lessons overlap in neither sample-index block nor seed, but generated examples are not statistical IID draws.",
            "Input uniqueness is exact-byte uniqueness, not symmetry- or recoloring-equivalence.",
            "The sampler measures 3-demo/1-query lessons only; other episode lengths require a separate census.",
        ],
    }
    Path("lesson-probe-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "totals": report["totals"],
        "generator_sha256": report["generator_sha256"],
        "rule_hash": normalized_rule_hash,
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=1800)
    args = parser.parse_args()
    if args.lessons_per_band < 1:
        parser.error("--lessons-per-band must be positive")

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-lesson-probe-") as directory:
        stage = Path(directory)
        manifest = prepare_runtime(Catalog(REPO), stage, TASK_ID)
        (stage / "lesson-probe-request.json").write_text(
            json.dumps({"lessons_per_band": args.lessons_per_band}) + "\n"
        )
        (stage / "lesson_probe_child.py").write_text(CHILD)
        result = run_process(
            [sys.executable, "-B", "lesson_probe_child.py"],
            stage,
            timeout=args.timeout,
        )
        report_path = stage / "lesson-probe-report.json"
        if not report_path.exists():
            raise RuntimeError(
                "lesson probe produced no report: "
                f"exit={result['exit_code']} timeout={result['timed_out']} "
                f"stdout={result['stdout'][-1000:]} stderr={result['stderr'][-1000:]}"
            )
        report = json.loads(report_path.read_text())
        report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report["runtime_manifest_sha256"] = hashlib.sha256(
            (stage / "RUNTIME_MANIFEST.json").read_bytes()
        ).hexdigest()
        report["runtime_file_count"] = len(manifest["files"])
        report["execution"] = {
            "exit_code": result["exit_code"],
            "timed_out": result["timed_out"],
            "stdout_tail": result["stdout"][-2000:],
            "stderr_tail": result["stderr"][-2000:],
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")

    print(json.dumps({
        "passed": report["passed"],
        "totals": report["totals"],
        "out": str(args.out),
    }, indent=2))
    return 0 if report["passed"] and result["exit_code"] == 0 and not result["timed_out"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

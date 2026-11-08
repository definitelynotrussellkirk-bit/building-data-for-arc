#!/usr/bin/env python3
"""Source-bound lesson census for ARC task 92f4d4eb0dbb.

The probe prepares the task's portable runtime, materializes real three-demo /
one-query lessons through the selected Racket authority, and checks every
currently declared competitor and witness.  Its finite census is curriculum
evidence, not a proof against unenumerated shortcuts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "92f4d4eb0dbb"
BANDS = ("easy", "medium", "hard")
N_DEMOS = 3
N_QUERIES = 1
STRIDE = 11
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from arcpuzzles import Catalog  # noqa: E402
from arcpuzzles.runtime import prepare_runtime, run_process  # noqa: E402


def pinned_seed(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:lesson:{band}:{lesson_index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def canonical_pairs() -> list[dict]:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                test = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return row["train"] + test
    raise FileNotFoundError(f"canonical task {TASK_ID} not found")


CHILD = r'''
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path

from puzzle_generators import runner

TASK_ID = "92f4d4eb0dbb"
BANDS = ("easy", "medium", "hard")
N_DEMOS = 3
N_QUERIES = 1
STRIDE = 11


def pinned_seed(band, lesson_index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:lesson:{band}:{lesson_index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def grid_hash(grid):
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()


def intended_output(grid):
    rows = [r for r, row in enumerate(grid) for value in row if value == 1]
    if not rows:
        return deepcopy(grid)
    threshold = min(rows) + max(rows)
    return [
        [2 if value == 1 and 2 * r > threshold else value for value in row]
        for r, row in enumerate(grid)
    ]


def same(left, right):
    return left == right


def first_difference(left, right):
    if len(left) != len(right):
        return ["height", len(left), len(right)]
    for r, (left_row, right_row) in enumerate(zip(left, right)):
        if len(left_row) != len(right_row):
            return ["width", r, len(left_row), len(right_row)]
        for c, (a, b) in enumerate(zip(left_row, right_row)):
            if a != b:
                return [r, c, a, b]
    return None


def main():
    request = json.loads(Path("lesson-probe-request.json").read_text())
    per_band = int(request["lessons_per_band"])
    canonical = request["canonical_pairs"]
    gen = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
    if gen.EXAMPLES_NEEDED != N_DEMOS:
        raise AssertionError(
            f"probe expects {N_DEMOS} demos, generator declares {gen.EXAMPLES_NEEDED}"
        )

    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}) or {})
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}) or {})
    for name, fn in shortcuts.items():
        competitors.setdefault(name, fn)
    if not competitors:
        raise AssertionError("generator declares no lesson competitors")

    canonical_shortcuts = {}
    failures = []
    for name, fn in sorted(shortcuts.items()):
        fits = 0
        errors = []
        for index, pair in enumerate(canonical):
            try:
                fits += int(same(fn(deepcopy(pair["input"])), pair["output"]))
            except Exception as exc:
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
        canonical_shortcuts[name] = {
            "pairs": len(canonical),
            "fits": fits,
            "fits_all": fits == len(canonical) and not errors,
            "errors": errors,
        }
        if not canonical_shortcuts[name]["fits_all"]:
            failures.append({
                "kind": "declared_shortcut_does_not_fit_canonical",
                "competitor": name,
                "detail": canonical_shortcuts[name],
            })

    bundle = runner._load_bundle(TASK_ID)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    rows = {}
    all_input_hashes = set()
    all_pair_hashes = set()
    first_disagreements = {}
    try:
        for band in BANDS:
            input_hashes = set()
            pair_hashes = set()
            starts = Counter()
            profiles = Counter()
            witness_hits = Counter()
            axis_values = {name: Counter() for name in gen.AXES}
            competitor_counts = {
                name: Counter(
                    demo_pair_disagreements=0,
                    query_disagreements=0,
                    refuted_by_demos=0,
                    survived_demos=0,
                    survived_all=0,
                    query_discriminates=0,
                    errors=0,
                )
                for name in sorted(competitors)
            }
            materialized = 0
            identifiable = 0
            oracle_mismatches = 0
            strict_pairs = 0
            for lesson_index in range(per_band):
                seed = pinned_seed(band, lesson_index)
                start = lesson_index * STRIDE
                starts[start % len(gen.SCHEDULE_PROFILES)] += 1
                try:
                    instance = runner.run_one(
                        TASK_ID,
                        seed=seed,
                        sample_index=start,
                        n_train=N_DEMOS,
                        n_test=N_QUERIES,
                        bundle=bundle,
                        bridge=bridge,
                        fn_name=fn_name,
                        difficulty=band,
                    )
                except Exception as exc:
                    failures.append({
                        "kind": "materialization_error",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    continue
                materialized += 1
                demos = instance["train"]
                query = instance["test"][0]
                reasons = list(gen.lesson_identifiable(demos, query) or [])
                identifiable += int(not reasons)
                if reasons:
                    failures.append({
                        "kind": "lesson_identifiability",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                        "reasons": reasons,
                    })

                pairs = [*demos, query]
                for offset, pair in enumerate(pairs):
                    sample_index = start + offset
                    inp_hash = grid_hash(pair["input"])
                    out_hash = grid_hash(pair["output"])
                    pair_hash = hashlib.sha256((inp_hash + out_hash).encode()).hexdigest()
                    input_hashes.add(inp_hash)
                    pair_hashes.add(pair_hash)
                    all_input_hashes.add(inp_hash)
                    all_pair_hashes.add(pair_hash)
                    profiles[str(gen.schedule_profile(seed, sample_index, band))] += 1
                    observed = gen.observe_overrides(pair["input"])
                    for axis in gen.AXES:
                        axis_values[axis][str(observed[axis])] += 1
                    strict_pairs += int(gen.strict_canonical_like(pair["input"]) == [])
                    for name, witness in witnesses.items():
                        try:
                            witness_hits[name] += int(bool(witness(pair["input"])))
                        except Exception as exc:
                            failures.append({
                                "kind": "witness_error",
                                "band": band,
                                "lesson_index": lesson_index,
                                "witness": name,
                                "error": f"{type(exc).__name__}: {exc}",
                            })
                    expected = intended_output(pair["input"])
                    if not same(expected, pair["output"]):
                        oracle_mismatches += 1
                        failures.append({
                            "kind": "oracle_racket_mismatch",
                            "band": band,
                            "lesson_index": lesson_index,
                            "sample_index": sample_index,
                            "input_sha256": inp_hash,
                            "first_difference": first_difference(expected, pair["output"]),
                        })

                for name, rival in competitors.items():
                    counts = competitor_counts[name]
                    try:
                        demo_outputs = [
                            rival(deepcopy(pair["input"])) for pair in demos
                        ]
                        query_output = rival(deepcopy(query["input"]))
                    except Exception as exc:
                        counts["errors"] += 1
                        failures.append({
                            "kind": "competitor_error",
                            "band": band,
                            "lesson_index": lesson_index,
                            "competitor": name,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                        continue
                    demo_misses = [
                        i for i, (candidate, pair) in enumerate(zip(demo_outputs, demos))
                        if not same(candidate, pair["output"])
                    ]
                    query_miss = not same(query_output, query["output"])
                    counts["demo_pair_disagreements"] += len(demo_misses)
                    counts["query_disagreements"] += int(query_miss)
                    if demo_misses:
                        counts["refuted_by_demos"] += 1
                    else:
                        counts["survived_demos"] += 1
                        counts["query_discriminates"] += int(query_miss)
                        counts["survived_all"] += int(not query_miss)
                        failures.append({
                            "kind": "competitor_survived_demos",
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start,
                            "competitor": name,
                            "query_disagrees": query_miss,
                        })

                    if name not in first_disagreements and (demo_misses or query_miss):
                        if demo_misses:
                            index = demo_misses[0]
                            pair = demos[index]
                            rival_output = demo_outputs[index]
                            pair_kind = f"demo_{index}"
                            pair_sample_index = start + index
                        else:
                            pair = query
                            rival_output = query_output
                            pair_kind = "query"
                            pair_sample_index = start + N_DEMOS
                        first_disagreements[name] = {
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "lesson_start_sample_index": start,
                            "pair_sample_index": pair_sample_index,
                            "pair_kind": pair_kind,
                            "input_sha256": grid_hash(pair["input"]),
                            "input": pair["input"],
                            "racket_output": pair["output"],
                            "rival_output": rival_output,
                            "first_difference": first_difference(
                                pair["output"], rival_output
                            ),
                        }

            generated_pairs = materialized * (N_DEMOS + N_QUERIES)
            rows[band] = {
                "requested_lessons": per_band,
                "materialized_lessons": materialized,
                "identifiable_lessons": identifiable,
                "unidentifiable_lessons": materialized - identifiable,
                "generated_pairs": generated_pairs,
                "unique_inputs": len(input_hashes),
                "unique_input_fraction": (
                    len(input_hashes) / generated_pairs if generated_pairs else 0.0
                ),
                "unique_pairs": len(pair_hashes),
                "strict_canonical_like_pairs": strict_pairs,
                "oracle_racket_mismatches": oracle_mismatches,
                "start_residues_mod_schedule": dict(sorted(starts.items())),
                "pair_schedule_profiles": dict(sorted(profiles.items())),
                "axis_values": {
                    name: dict(sorted(values.items()))
                    for name, values in axis_values.items()
                },
                "witness_hits": dict(sorted(witness_hits.items())),
                "competitors": {
                    name: dict(counter)
                    for name, counter in competitor_counts.items()
                },
            }
    finally:
        bridge.shutdown()

    generator_path = Path(gen.__file__)
    normalized_rule_hash = hashlib.sha256(
        " ".join(bundle.rule_source.split()).encode()
    ).hexdigest()[:12]
    if normalized_rule_hash != gen.RULE_HASH:
        failures.append({
            "kind": "rule_hash_mismatch",
            "declared": gen.RULE_HASH,
            "selected": normalized_rule_hash,
        })

    report = {
        "schema": "92f4d4eb0dbb-racket-lesson-census-v1",
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
            "lesson_start_sample_index_rule": f"k * {STRIDE}",
            "pair_indices": "lesson start through start+3, consumed by runner.run_one",
            "difficulty": "passed to every pair through runner.run_one",
            "outputs": "selected canonical Racket rule through one persistent Racket bridge",
            "competitors": "dynamic union of LESSON_COMPETITORS and CANONICAL_SHORTCUTS",
            "witnesses": "dynamic SEMANTIC_WITNESSES declaration",
        },
        "declared_axes": gen.AXES,
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "competitors": sorted(competitors),
        "witnesses": sorted(witnesses),
        "canonical_shortcut_check": canonical_shortcuts,
        "per_band": rows,
        "first_disagreements": first_disagreements,
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
            "This finite census tests declared competitors only; it is not universal induction over all possible rules.",
            "Exact-byte uniqueness does not quotient by translations, reflections, or morphology equivalence.",
            "The census measures three-demo/one-query episodes; other episode lengths need a separate run.",
            "The generator domain deliberately fixes input colors to 0/1 and generated morphology width to five columns, matching the selected rule's evidenced color semantics while varying dimensions, height parity, shape, reflection, and placement.",
        ],
    }
    Path("lesson-probe-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "totals": report["totals"],
        "failure_count": len(failures),
        "generator_sha256": report["generator_sha256"],
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
            json.dumps({
                "lessons_per_band": args.lessons_per_band,
                "canonical_pairs": canonical_pairs(),
            }) + "\n"
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
    return 0 if (
        report["passed"]
        and result["exit_code"] == 0
        and not result["timed_out"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())

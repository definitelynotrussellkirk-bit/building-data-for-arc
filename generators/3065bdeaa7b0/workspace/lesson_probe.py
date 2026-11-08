#!/usr/bin/env python3
"""Source-bound, Racket-backed lesson census for ARC task 3065bdeaa7b0.

The probe stages the selected task through the repository's public runtime copier
and constructs actual 3-demo/1-query lessons with ``runner.run_one``.  It reads
rivals and witnesses from the staged generator instead of keeping a second rival
list.  The finite census measures the named alternatives over a pinned sample;
it is evidence about this curriculum, not a proof of universal identifiability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "3065bdeaa7b0"
BANDS = ("easy", "medium", "hard")
N_DEMOS = 3
N_QUERIES = 1
# 11 is coprime to the four-position curriculum, so 100 lessons exercise every
# cyclic start exactly 25 times while keeping non-overlapping index blocks.
STRIDE = 11
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from arcpuzzles.catalog import Catalog  # noqa: E402
from arcpuzzles.runtime import prepare_runtime, run_process  # noqa: E402


def pinned_seed(band: str, index: int) -> int:
    """Stable seed used by both the executable probe and its regression test."""
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:lesson:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


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

TASK_ID = "3065bdeaa7b0"
BANDS = ("easy", "medium", "hard")
N_DEMOS = 3
N_QUERIES = 1
STRIDE = 11


def pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:lesson:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def grid_hash(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()


def color_positions(grid):
    positions = {}
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            if color:
                positions.setdefault(color, []).append((row_index, col_index))
    return positions


def between(a, b):
    step = 1 if a <= b else -1
    return range(a, b + step, step)


def independent_oracle(grid):
    """Independent Python transcription used only as a parity cross-check."""
    out = deepcopy(grid)
    records = []
    for color, points in color_positions(grid).items():
        if len(points) != 2:
            continue
        first, second = sorted(points)
        records.append((first, color, second))
    records.sort(key=lambda record: record[0])
    for first, color, second in records:
        for col in between(first[1], second[1]):
            out[first[0]][col] = color
        for row in between(first[0], second[0]):
            out[row][second[1]] = color
    return out


def first_difference(a, b):
    for row_index, (left_row, right_row) in enumerate(zip(a, b)):
        for col_index, (left, right) in enumerate(zip(left_row, right_row)):
            if left != right:
                return [row_index, col_index, left, right]
    return None


def main() -> int:
    request = json.loads(Path("lesson-probe-request.json").read_text())
    per_band = int(request["lessons_per_band"])
    gen = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
    if int(gen.EXAMPLES_NEEDED) != N_DEMOS:
        raise AssertionError(
            f"probe expects {N_DEMOS} demos, generator declares {gen.EXAMPLES_NEEDED}"
        )

    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}) or {})
    for name, fn in shortcuts.items():
        competitors.setdefault(name, fn)
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}) or {})
    if not competitors:
        raise AssertionError("generator declares no lesson competitors")

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
    first_disagreements = {}
    oracle_mismatches = []
    try:
        for band in BANDS:
            input_hashes = set()
            pair_hashes = set()
            starts = Counter()
            pair_profiles = Counter()
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
            identifiable = 0
            strict_pairs = 0
            materialized = 0
            for lesson_index in range(per_band):
                seed = pinned_seed(band, lesson_index)
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
                        "kind": "materialization_error",
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
                reasons = list(gen.lesson_identifiable(demos, query) or [])
                identifiable += int(not reasons)
                if reasons:
                    failures.append({
                        "kind": "lesson_identifiability",
                        "band": band,
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": sample_index,
                        "reasons": reasons,
                    })

                pairs = [*demos, query]
                for offset, pair in enumerate(pairs):
                    pair_sample_index = sample_index + offset
                    inp_hash = grid_hash(pair["input"])
                    out_hash = grid_hash(pair["output"])
                    pair_hash = hashlib.sha256((inp_hash + out_hash).encode()).hexdigest()
                    input_hashes.add(inp_hash)
                    pair_hashes.add(pair_hash)
                    all_input_hashes.add(inp_hash)
                    all_pair_hashes.add(pair_hash)
                    profile = gen.schedule_profile(
                        seed, pair_sample_index, difficulty=band
                    )
                    pair_profiles[str(profile)] += 1
                    strict_pairs += int(gen.strict_canonical_like(pair["input"]) == [])
                    observed = gen.observe_overrides(pair["input"])
                    for axis_name in gen.AXES:
                        axis_values[axis_name][str(observed[axis_name])] += 1
                    expected = independent_oracle(pair["input"])
                    if not _grids_equal(expected, pair["output"]):
                        mismatch = {
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": pair_sample_index,
                            "input_sha256": inp_hash,
                            "first_difference": first_difference(expected, pair["output"]),
                        }
                        oracle_mismatches.append(mismatch)
                        failures.append({"kind": "oracle_racket_mismatch", **mismatch})
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

                for name, rival in competitors.items():
                    counts = competitor_counts[name]
                    try:
                        rival_demo_outputs = [
                            rival(deepcopy(pair["input"])) for pair in demos
                        ]
                        rival_query_output = rival(deepcopy(query["input"]))
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
                    demo_mismatches = [
                        index for index, (candidate, pair) in enumerate(
                            zip(rival_demo_outputs, demos)
                        )
                        if not _grids_equal(candidate, pair["output"])
                    ]
                    query_miss = not _grids_equal(
                        rival_query_output, query["output"]
                    )
                    counts["demo_pair_disagreements"] += len(demo_mismatches)
                    counts["query_disagreements"] += int(query_miss)
                    fits_demos = not demo_mismatches
                    if fits_demos:
                        counts["survived_demos"] += 1
                        failures.append({
                            "kind": "competitor_survived_demos",
                            "band": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": sample_index,
                            "competitor": name,
                            "query_disagrees": query_miss,
                        })
                        if query_miss:
                            counts["query_discriminates"] += 1
                        else:
                            counts["survived_all"] += 1
                    else:
                        counts["refuted_by_demos"] += 1

                    if name not in first_disagreements:
                        if demo_mismatches:
                            pair_index = demo_mismatches[0]
                            pair = demos[pair_index]
                            rival_output = rival_demo_outputs[pair_index]
                            pair_kind = f"demo_{pair_index}"
                            pair_sample_index = sample_index + pair_index
                        elif query_miss:
                            pair = query
                            rival_output = rival_query_output
                            pair_kind = "query"
                            pair_sample_index = sample_index + N_DEMOS
                        else:
                            pair = None
                        if pair is not None:
                            first_disagreements[name] = {
                                "band": band,
                                "lesson_index": lesson_index,
                                "seed": seed,
                                "lesson_start_sample_index": sample_index,
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
                "axis_values": {
                    name: dict(sorted(values.items(), key=lambda item: int(item[0])))
                    for name, values in axis_values.items()
                },
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
    shortcut_failures = [
        name for name, result in shortcut_canonical.items()
        if not result["fits_all"]
    ]
    if shortcut_failures:
        failures.append({
            "kind": "declared_shortcut_does_not_fit_canonical",
            "shortcuts": shortcut_failures,
        })
    if normalized_rule_hash != gen.RULE_HASH:
        failures.append({
            "kind": "rule_hash_mismatch",
            "declared": gen.RULE_HASH,
            "selected": normalized_rule_hash,
        })

    report = {
        "schema": "3065bdeaa7b0-racket-lesson-census-v1",
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
            "sample_index_rule": f"k * {STRIDE}",
            "pair_indices": "lesson start through start+3, consumed by runner.run_one",
            "cyclic_start_policy": "stride 11 modulo four schedule states; 100 lessons gives 25 starts at each residue",
            "difficulty": "passed to every pair through runner.run_one",
            "outputs": "canonical selected Racket rule through one persistent RacketBridge",
            "competitors": "dynamic union of final generator LESSON_COMPETITORS and CANONICAL_SHORTCUTS",
            "witnesses": "dynamic final generator SEMANTIC_WITNESSES",
        },
        "declared_axes": gen.AXES,
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "competitors": sorted(competitors),
        "witnesses": sorted(witnesses),
        "canonical_shortcut_check": shortcut_canonical,
        "per_band": rows,
        "first_disagreements": first_disagreements,
        "oracle_racket_mismatches": oracle_mismatches,
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
            "This is a finite census over declared competitors, not a proof against every possible shortcut.",
            "Exact-byte uniqueness does not quotient by geometric symmetry or color permutation.",
            "The sampler measures three-demo/one-query episodes; other episode lengths need a separate census.",
            "Seeds and sample indices are deterministic and broad, but generated examples are not claimed to be IID.",
        ],
    }
    Path("lesson-probe-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "totals": report["totals"],
        "generator_sha256": report["generator_sha256"],
        "rule_hash": normalized_rule_hash,
        "failure_count": len(failures),
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

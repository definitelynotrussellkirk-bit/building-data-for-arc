#!/usr/bin/env python3
"""Source-bound finite lesson census; reference labels use public arcpuzzles apply.

Default: 4 seeds x 25 sliding starts x 3 bands = 300 four-demo/one-query
lessons.  Only 29 draws per seed/band are needed: 348 draw uses before input
deduplication.  Overlapping lessons are explicitly not independent observations.
No private runner, solve artifact, Python oracle, or approval mutation is used.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import subprocess
import sys

TASK_ID = "aba5e4aeb835"
REPO = Path(__file__).resolve().parents[3]
BANDS = ("easy", "medium", "hard")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open("x") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")


def callable_identity(fn):
    try:
        source = inspect.getsource(fn)
        source_hash = hashlib.sha256(source.encode()).hexdigest()
    except (OSError, TypeError):
        source_hash = None
    return {"module": fn.__module__, "qualname": fn.__qualname__, "source_sha256": source_hash}


def load_generator(path):
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location("laser_probe_selected_generator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def registry(gen, name):
    value = getattr(gen, name, {})
    if not isinstance(value, dict) or any(not callable(fn) for fn in value.values()):
        raise TypeError(f"{name} must be a dict[str, callable]")
    return value


def canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                # Only public examples enter the probe; written/program solutions
                # are neither inspected nor retained.
                pairs = [p for kind in ("train", "test") for p in record[kind]
                         if isinstance(p.get("input"), list) and isinstance(p.get("output"), list)]
                if len(pairs) != 4:
                    raise ValueError(f"Expected ALL 4 usable canonical pairs, got {len(pairs)}")
                return [{"input": p["input"], "output": p["output"]} for p in pairs]
    raise ValueError("Canonical task not found")


def compare(fn, grid, expected):
    try:
        output = fn(deepcopy(grid))
        return {"agrees": output == expected, "prediction_sha256": digest(output)}
    except Exception as exc:
        return {"agrees": False, "error": f"{type(exc).__name__}: {exc}"}


def check_valid(value):
    """Generators may expose either a boolean or a violation-list check."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple)):
        return not value
    raise TypeError(f"Expected boolean or violation list, got {type(value).__name__}")


def observe(gen, grid):
    fn = getattr(gen, "observe_overrides", None)
    if fn is None:
        return {}
    value = fn(deepcopy(grid))
    return value if isinstance(value, dict) else {"observation": value}


def validate_bands(raw):
    bands = [value.strip() for value in raw.split(",")]
    if any(not value for value in bands):
        raise ValueError("--bands must contain nonempty band names")
    if len(set(bands)) != len(bands):
        raise ValueError("--bands must contain distinct band names")
    unknown = sorted(set(bands) - set(BANDS))
    if unknown:
        raise ValueError(f"unknown --bands values: {', '.join(unknown)}; choose easy,medium,hard")
    return bands


def evaluate_check(fn, grid, **kwargs):
    """Retain declared check results while normalizing boolean/list validity."""
    try:
        result = fn(deepcopy(grid), **kwargs)
        valid = check_valid(result)
        errors = [] if valid else list(result) if isinstance(result, (list, tuple)) else ["check returned False"]
        return result, valid, errors
    except Exception as exc:
        errors = [f"{type(exc).__name__}: {exc}"]
        return errors, False, errors


def verify_witness_claims(row, claims):
    """A fired witness must actually distinguish every named rival from Racket."""
    failures = []
    verified = {}
    for witness, names in claims.items():
        if not row["witnesses"][witness]:
            verified[witness] = None
            continue
        verified[witness] = True
        for name in names:
            result = row["competitors"][name]
            if result["agrees"] or "error" in result:
                verified[witness] = False
                failures.append({"kind": "false_witness_claim", "draw_id": row["id"],
                                 "witness": witness, "rival": name,
                                 "input_sha256": row["input_sha256"],
                                 "racket_output_sha256": row["output_sha256"], "comparison": result})
    row["witness_claims_verified"] = verified
    return failures


def apply_batches(grids, out, wrapper, timeout):
    """Execute only the supported CLI, with <=64 inputs per invocation."""
    labels = {}
    receipts = []
    items = list(grids.items())
    for start in range(0, len(items), 64):
        number = start // 64
        batch = items[start:start + 64]
        input_path = out / f"apply-{number:03d}-inputs.json"
        result_path = out / f"apply-{number:03d}-results.json"
        write(input_path, {"inputs": [grid for _, grid in batch]})
        command = [sys.executable, str(wrapper), sys.executable, "-m", "arcpuzzles",
                   "apply", TASK_ID, "--input", str(input_path), "--reference", "canonical",
                   "--timeout", str(timeout), "--out", str(result_path)]
        run = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 90)
        receipt = {"batch": number, "inputs": len(batch), "command": command,
                   "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
        receipts.append(receipt)
        write(out / f"apply-{number:03d}-command.json", receipt)
        if run.returncode:
            raise RuntimeError(f"Public apply batch {number} failed; retained command receipt")
        result = json.loads(result_path.read_text())
        if len(result["results"]) != len(batch):
            raise RuntimeError("Public apply returned wrong result count")
        for (key, grid), row in zip(batch, result["results"], strict=True):
            if row.get("input") != grid or row.get("input_sha256") != digest(grid):
                raise RuntimeError("Public apply input/hash mismatch")
            if row.get("output") is None:
                raise RuntimeError(f"Public apply has no output for {key}: {row}")
            if row.get("output_sha256") != digest(row["output"]):
                raise RuntimeError("Public apply output/hash mismatch")
            labels[key] = row["output"]
        receipts[-1].update({key: result.get(key) for key in
                            ("executed_rule_hash", "catalog_rule_hash", "rule_text_sha256",
                             "generator_sha256", "rule_hash_matches_catalog", "reference")})
        print(f"public apply batch {number}: {len(batch)} inputs", flush=True)
    return labels, receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory; refuses overwrite")
    parser.add_argument("--generator", type=Path, default=REPO / "generators" / TASK_ID / "generator.py")
    parser.add_argument("--seeds", default="104729,130363,155921,196613", help="comma-separated integer seeds")
    parser.add_argument("--starts", type=int, default=25, help="consecutive lesson starts per seed/band")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--stride", type=int, default=1, help="lesson-start stride; all drawn indices retained")
    parser.add_argument("--bands", default=",".join(BANDS))
    parser.add_argument("--wrapper", type=Path, default=REPO.parent / "run_with_racket.py")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--generate-only", action="store_true", help="inputs/observations only; no labeled claims")
    args = parser.parse_args()
    try:
        seeds = [int(s) for s in args.seeds.split(",")]
        bands = validate_bands(args.bands)
    except ValueError as exc:
        parser.error(str(exc))
    if args.starts < 1 or args.stride < 1 or args.start_index < 0 or len(set(seeds)) != len(seeds):
        parser.error("positive starts/stride, nonnegative start index, and distinct seeds required")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    gen = load_generator(args.generator.resolve())
    demos_count = int(getattr(gen, "EXAMPLES_NEEDED", 4))
    if demos_count != 4:
        raise ValueError(f"Expected four demonstrations, generator declares {demos_count}")
    registries = {name: registry(gen, name) for name in
                  ("SEMANTIC_WITNESSES", "SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")}
    # Union the ACTUAL declared callables so neither a missing lesson alias nor
    # a later new semantic rival silently escapes measurement.
    competitors = {}
    for registry_name in ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        for name, fn in registries[registry_name].items():
            if name in competitors and competitors[name] is not fn:
                raise ValueError(f"Conflicting declared competitor {name}")
            competitors[name] = fn
    witnesses = registries["SEMANTIC_WITNESSES"]
    witness_rivals = getattr(gen, "WITNESS_RIVALS", {})
    if not isinstance(witness_rivals, dict):
        raise TypeError("WITNESS_RIVALS must be a dict[str, list[str]]")
    for name, rivals in witness_rivals.items():
        if name not in witnesses or not isinstance(rivals, (list, tuple)) or not rivals:
            raise ValueError(f"Invalid WITNESS_RIVALS declaration for {name}")
        if any(rival not in competitors for rival in rivals):
            raise ValueError(f"WITNESS_RIVALS {name} refers to an undeclared rival")
    min_strict_frac = float(getattr(gen, "MIN_STRICT_FRAC", 1.0))
    canonical = canonical_pairs()
    grids = {digest(p["input"]): p["input"] for p in canonical}
    draws = {}
    failures = []
    starts = [args.start_index + n * args.stride for n in range(args.starts)]
    indices = sorted({i for start in starts for i in range(start, start + demos_count + 1)})
    period = len(getattr(gen, "SCHEDULE_PROFILES", ())) or 4
    for band in bands:
        for seed in seeds:
            for index in indices:
                key = f"{band}:{seed}:{index}"
                grid = gen.generate(seed, index, difficulty=band)
                input_hash = digest(grid)
                grids[input_hash] = grid
                row = {"id": key, "band": band, "seed": seed, "sample_index": index,
                       "input_sha256": input_hash, "observation": observe(gen, grid)}
                result, valid, errors = evaluate_check(gen.self_check, grid, difficulty=band)
                row["self_check_result"] = result
                row["self_check_valid"] = valid
                row["self_check_errors"] = errors
                if errors:
                    failures.append({"kind": "self_check", "draw_id": key, "errors": errors})
                fn = getattr(gen, "strict_canonical_like", None)
                result, valid, errors = evaluate_check(fn, grid) if fn else (None, False, ["strict_canonical_like is missing"])
                row["strict_canonical_like_result"] = result
                row["strict_canonical_like"] = valid
                if not valid and min_strict_frac == 1.0:
                    failures.append({"kind": "strict_canonical_like_violation", "draw_id": key, "errors": errors})
                row["witnesses"] = {}
                for name, fn in witnesses.items():
                    try:
                        row["witnesses"][name] = bool(fn(deepcopy(grid)))
                    except Exception as exc:
                        row["witnesses"][name] = False
                        failures.append({"kind": "witness_error", "draw_id": key, "name": name,
                                         "error": f"{type(exc).__name__}: {exc}"})
                draws[key] = row
    manifest = {"schema": "laser-distribution-probe-v1", "task_id": TASK_ID,
                "generator": str(args.generator.resolve()), "generator_sha256": file_hash(args.generator),
                "generator_version": getattr(gen, "VERSION", None),
                "probe_sha256": file_hash(__file__), "wrapper_sha256": file_hash(args.wrapper),
                "api_callables": {name: callable_identity(getattr(gen, name)) for name in
                                  ("generate", "self_check", "strict_canonical_like", "observe_overrides",
                                   "schedule_profile", "lesson_identifiable") if callable(getattr(gen, name, None))},
                "canonical_pairs_sha256": digest(canonical),
                "registries": {name: {key: callable_identity(fn) for key, fn in value.items()}
                               for name, value in registries.items()},
                "seeds": seeds, "bands": bands, "starts": starts, "sample_indices": indices,
                "sample_index_range": [min(indices), max(indices)], "demo_count": demos_count,
                "query_count": 1, "schedule_period": period,
                "schedule_profiles": getattr(gen, "SCHEDULE_PROFILES", None),
                "min_strict_frac": min_strict_frac, "witness_rivals": witness_rivals,
                "sampling_policy": "Sliding/strided lessons reuse deterministic generated draws; labels are deduplicated by exact input SHA256. Lessons overlap and are not independent trials.",
                "canonical_pairs": 4, "draw_uses": len(draws), "unique_generated_inputs": len({r["input_sha256"] for r in draws.values()}),
                "unique_apply_inputs_including_canonical": len(grids),
                "lesson_count": len(bands) * len(seeds) * len(starts),
                "lesson_pair_uses": len(bands) * len(seeds) * len(starts) * (demos_count + 1),
                "generate_only": args.generate_only}
    write(out / "manifest.json", manifest)
    if args.generate_only:
        write(out / "inputs.json", grids)
        write(out / "draws.json", list(draws.values()))
        write(out / "failures.json", failures)
        print(json.dumps({"out": str(out), "generate_only": True, "draws": len(draws)}))
        return int(bool(failures))
    labels, receipts = apply_batches(grids, out, args.wrapper.resolve(), args.timeout)
    if file_hash(args.generator) != manifest["generator_sha256"]:
        failures.append({"kind": "selected_generator_changed_during_probe"})
    rule_identities = {(r.get("executed_rule_hash"), r.get("rule_text_sha256")) for r in receipts}
    if len(rule_identities) != 1:
        failures.append({"kind": "reference_rule_changed_between_apply_batches"})
    if any(not r.get("rule_hash_matches_catalog") for r in receipts):
        failures.append({"kind": "reference_rule_hash_does_not_match_catalog"})
    shortcut_canonical = {}
    for name, fn in registries["CANONICAL_SHORTCUTS"].items():
        results = [compare(fn, pair["input"], pair["output"]) for pair in canonical]
        shortcut_canonical[name] = {"denominator": 4, "fits": sum(r["agrees"] for r in results),
                                    "fits_all_four": all(r["agrees"] for r in results), "pairs": results}
        if not all(r["agrees"] for r in results):
            failures.append({"kind": "canonical_shortcut_does_not_fit_all_four", "name": name, "pairs": results})
    for i, pair in enumerate(canonical):
        if labels[digest(pair["input"])] != pair["output"]:
            failures.append({"kind": "canonical_racket_pair_mismatch", "canonical_pair": i})
    for row in draws.values():
        grid = grids[row["input_sha256"]]
        expected = labels[row["input_sha256"]]
        row["output_sha256"] = digest(expected)
        row["non_identity"] = grid != expected
        row["competitors"] = {name: compare(fn, grid, expected) for name, fn in competitors.items()}
        if not row["non_identity"]:
            failures.append({"kind": "identity", "draw_id": row["id"]})
        for name, result in row["competitors"].items():
            if "error" in result:
                failures.append({"kind": "competitor_error", "draw_id": row["id"], "name": name, **result})
        failures.extend(verify_witness_claims(row, witness_rivals))
    lessons = []
    summaries = {}
    for band in bands:
        band_draws = [r for r in draws.values() if r["band"] == band]
        stats = {name: Counter() for name in competitors}
        phase_counts = Counter()
        for seed in seeds:
            for start in starts:
                ids = [f"{band}:{seed}:{i}" for i in range(start, start + demos_count + 1)]
                rows = [draws[key] for key in ids]
                status = {}
                for name in competitors:
                    refuted = [i for i, r in enumerate(rows[:demos_count]) if not r["competitors"][name]["agrees"]]
                    query_disagrees = not rows[-1]["competitors"][name]["agrees"]
                    status[name] = {"demo_refutations": refuted, "survives_demos": not refuted,
                                    "query_disagrees": query_disagrees,
                                    "query_discriminates": not refuted and query_disagrees}
                    stats[name].update({"refuted_by_demos": bool(refuted), "survives_demos": not refuted,
                                        "survives_all": not refuted and not query_disagrees,
                                        "query_disagrees": query_disagrees,
                                        "query_discriminates": not refuted and query_disagrees,
                                        "demo_pair_disagreements": len(refuted)})
                identifiable = not any(s["query_discriminates"] for s in status.values())
                all_refuted = all(not s["survives_demos"] for s in status.values())
                lesson = {"band": band, "seed": seed, "start": start, "phase": start % period,
                          "draw_ids": ids, "competitors": status,
                          "demo_witnesses": {name: any(r["witnesses"][name] for r in rows[:-1]) for name in witnesses},
                          "query_witnesses": rows[-1]["witnesses"],
                          "query_identifiable_against_declared_competitors": identifiable,
                          "all_competitors_refuted_by_demos": all_refuted}
                fn = getattr(gen, "lesson_identifiable", None)
                if fn:
                    pairs = [{"input": deepcopy(grids[r["input_sha256"]]),
                              "output": deepcopy(labels[r["input_sha256"]])} for r in rows]
                    try:
                        lesson["declared_lesson_identifiable"] = fn(pairs[:-1], pairs[-1])
                        if not check_valid(lesson["declared_lesson_identifiable"]):
                            failures.append({"kind": "declared_lesson_not_identifiable", "band": band,
                                             "seed": seed, "start": start, "draw_ids": ids})
                    except Exception as exc:
                        failures.append({"kind": "lesson_identifiable_error", "band": band, "seed": seed,
                                         "start": start, "error": f"{type(exc).__name__}: {exc}"})
                if not identifiable:
                    failures.append({"kind": "query_not_identifiable", **lesson})
                if not all_refuted:
                    failures.append({"kind": "competitor_survives_demos", **lesson})
                phase_counts[start % period] += 1
                lessons.append(lesson)
        unique = {r["input_sha256"] for r in band_draws}
        denominator = len(seeds) * len(starts)
        strict_count = sum(r["strict_canonical_like"] is True for r in band_draws)
        if strict_count / len(band_draws) < min_strict_frac:
            failures.append({"kind": "strict_fraction_below_minimum", "band": band, "passing": strict_count,
                             "denominator": len(band_draws), "minimum_fraction": min_strict_frac})
        summaries[band] = {"lesson_denominator": denominator, "demo_pair_denominator": denominator * demos_count,
                           "query_pair_denominator": denominator, "draw_use_denominator": len(band_draws),
                           "unique_input_denominator": len(unique), "overlapping_lesson_pair_uses": denominator * (demos_count + 1),
                           "meets_100_lesson_floor": denominator >= 100, "cyclic_start_counts": dict(phase_counts),
                           "all_cyclic_starts_exercised": len(phase_counts) == period,
                           "self_check_failures": sum(bool(r["self_check_errors"]) for r in band_draws),
                           "strict_canonical_like": sum(r["strict_canonical_like"] is True for r in band_draws),
                           "verified_witness_draw_uses": {name: sum(r["witness_claims_verified"].get(name) is True for r in band_draws) for name in witness_rivals},
                           "non_identity": sum(r["non_identity"] for r in band_draws),
                           "witness_draw_uses": {name: sum(r["witnesses"][name] for r in band_draws) for name in witnesses},
                           "witness_unique_inputs": {name: len({r["input_sha256"] for r in band_draws if r["witnesses"][name]}) for name in witnesses},
                           "witness_demo_lessons": {name: sum(r["demo_witnesses"][name] for r in lessons if r["band"] == band) for name in witnesses},
                           "witness_query_lessons": {name: sum(r["query_witnesses"][name] for r in lessons if r["band"] == band) for name in witnesses},
                           "competitors": {name: dict(counter) for name, counter in stats.items()},
                           "observed_axes": {axis: dict(Counter(json.dumps(r["observation"].get(axis), sort_keys=True)
                                                               for r in band_draws))
                                             for axis in sorted({a for r in band_draws for a in r["observation"]})}}
    if not competitors or not registries["CANONICAL_SHORTCUTS"] or not witnesses:
        failures.append({"kind": "missing_declared_registry", "registry_sizes": {k: len(v) for k, v in registries.items()}})
    report = {"manifest": manifest, "bands": summaries, "canonical_shortcuts": shortcut_canonical,
              "racket_receipts": receipts, "failures": failures,
              "failure_count": len(failures), "passed": not failures,
              "meets_full_distribution_scope": all(r["meets_100_lesson_floor"] and r["all_cyclic_starts_exercised"] for r in summaries.values()) and set(bands) == set(BANDS),
              "claim_limit": "Finite census of the actual declared rivals; overlapping lesson counts are not independent draws or proof against undeclared hypotheses."}
    write(out / "draws.json", list(draws.values()))
    write(out / "lessons.json", lessons)
    write(out / "failures.json", failures)
    write(out / "report.json", report)
    print(json.dumps({"out": str(out), "passed": report["passed"], "failures": len(failures),
                      "lessons": len(lessons), "unique_inputs": manifest["unique_generated_inputs"]}))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

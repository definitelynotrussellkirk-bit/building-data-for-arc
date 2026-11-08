#!/usr/bin/env python3
"""Source-bound lesson/rival and mutation-observability probe for 84def340ce03.

Run from the packet root after the selected generator is frozen::

    python3 run_with_racket.py python3 generators/84def340ce03/workspace/lesson_probe.py \
        --out ../checks/lesson-probe \
        --baseline-generator ../checks/semantic-review/baseline_generator.py

The generator supplies inputs and rival declarations. Every reference answer,
including mutation answers, comes from the public Catalog.apply API in batches
of at most 64. No private runner or copied Python reference transform is used.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[3]
TASK_ID = "84def340ce03"
BANDS = ("easy", "medium", "hard")
BASELINE_SHA256 = "50354457757c1a2fc9688b02a03e66ded0d8dd2795b895531dde8844585a3b0f"
sys.dont_write_bytecode = True
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]

from arcpuzzles import Catalog


def packed(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def grid_sha(grid):
    return sha(packed(grid))


def load_generator(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if getattr(module, "TASK_ID", None) != TASK_ID:
        raise ValueError(f"Wrong task in generator {path}")
    return module


def tiles(grid):
    return [tuple(grid[r + dr][c + dc] for dr in range(2) for dc in range(2))
            for r in range(0, len(grid), 2) for c in range(0, len(grid[0]), 2)]


def uniformize_top_left(grid):
    """Erase three source values per tile, preserving its top-left value."""
    return [[grid[2 * (r // 2)][2 * (c // 2)] for c in range(len(grid[0]))]
            for r in range(len(grid))]


def grid_features(grid):
    ts = tiles(grid)
    uniform_count = sum(len(set(t)) == 1 for t in ts)
    return {
        "shape": [len(grid), len(grid[0])],
        "palette_size": len({v for row in grid for v in row}),
        "has_zero": any(0 in row for row in grid),
        "mixed_tiles": len(ts) - uniform_count,
        "uniform_tiles": uniform_count,
        "has_repeated_tile": len(set(ts)) < len(ts),
        "has_adjacent_repeated_tile": any(a == b for a, b in zip(ts, ts[1:])),
        "has_uniform_and_mixed_tiles": 0 < uniform_count < len(ts),
        "smaller_side_not_four": min(len(grid), len(grid[0])) != 4,
    }


def lawful_grid(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return False
    h, w = len(grid), len(grid[0])
    return (h % 2 == 0 and w % 2 == 0 and h <= 30 and w <= 30 and h * w // 2 <= 30
            and all(isinstance(row, list) and len(row) == w
                    and all(type(v) is int and 0 <= v <= 9 for v in row) for row in grid))


def read_canonical():
    rows = []
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.open():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    if not rows:
        raise ValueError("Target has no canonical records")
    rules = {row["program_solution"] for row in rows}
    if len(rules) != 1:
        raise ValueError("Target canonical rule is ambiguous")
    rule = next(iter(rules))
    pairs = []
    for row_index, row in enumerate(rows):
        for split in ("train", "test"):
            for pair_index, pair in enumerate(row.get(split, [])):
                pairs.append({"record_index": row_index, "source": row["source"],
                              "split": split, "pair_index": pair_index, **pair})
    return rows, pairs, rule


def declarations(module):
    shortcuts = getattr(module, "CANONICAL_SHORTCUTS", None)
    competitors = getattr(module, "LESSON_COMPETITORS", None)
    for name, value in (("CANONICAL_SHORTCUTS", shortcuts), ("LESSON_COMPETITORS", competitors)):
        if not isinstance(value, dict) or not value or not all(isinstance(k, str) and callable(v) for k, v in value.items()):
            raise ValueError(f"{name} must be a nonempty dictionary of named callables")
    for name in shortcuts.keys() & competitors.keys():
        if shortcuts[name] is not competitors[name]:
            raise ValueError(f"The two rival declarations assign different callables to {name!r}")
    merged = dict(shortcuts)
    merged.update(competitors)
    return shortcuts, competitors, merged


def run(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source_path = REPO / "generators" / TASK_ID / "generator.py"
    source_hash = sha(source_path.read_bytes())
    if args.expected_generator_sha256 and args.expected_generator_sha256 != source_hash:
        raise ValueError("Selected generator does not match the requested frozen hash")
    baseline_path = args.baseline_generator.resolve()
    if sha(baseline_path.read_bytes()) != BASELINE_SHA256:
        raise ValueError("Baseline snapshot differs from the original measured source")
    module = load_generator(source_path, "lesson_probe_final")
    baseline = load_generator(baseline_path, "lesson_probe_baseline")
    shortcuts, competitors, rivals = declarations(module)
    canonical_rows, canonical_pairs, rule = read_canonical()
    canonical_hash = sha(packed(canonical_rows))
    rule_hash = sha(" ".join(rule.split()).encode())[:12]
    rule_text_hash = sha(rule.encode())
    if getattr(module, "RULE_HASH", None) != rule_hash:
        raise ValueError("Generator RULE_HASH differs from its selected canonical rule")
    if getattr(module, "EXAMPLES_NEEDED", 3) != 3:
        raise ValueError("This explicit probe audits three demonstrations; EXAMPLES_NEEDED must match")

    inputs = {}
    slot_records = []
    slots = {}

    def add_grid(grid):
        if not lawful_grid(grid):
            raise ValueError("Probe input falls outside the declared even rectangular ARC domain")
        key = grid_sha(grid)
        inputs.setdefault(key, copy.deepcopy(grid))
        return key

    for pair in canonical_pairs:
        pair["input_sha256"] = add_grid(pair["input"])
        pair["mutation_input_sha256"] = add_grid(uniformize_top_left(pair["input"]))
    for phase, sampler in (("baseline", baseline), ("final", module)):
        for band in BANDS:
            for seed in range(args.seeds):
                for sample_index in range(6):
                    grid = sampler.generate(seed, sample_index, difficulty=band)
                    errors = sampler.self_check(copy.deepcopy(grid), difficulty=band)
                    if errors:
                        raise ValueError(f"{phase} validator failed {band=} {seed=} {sample_index=}: {errors}")
                    key = add_grid(grid)
                    mutation_key = add_grid(uniformize_top_left(grid))
                    record = {"phase": phase, "generation_source_sha256": BASELINE_SHA256 if phase == "baseline" else source_hash,
                              "band": band, "seed": seed, "sample_index": sample_index,
                              "overrides": {}, "input_sha256": key, "mutation_input_sha256": mutation_key,
                              "features": grid_features(grid)}
                    if callable(getattr(sampler, "schedule_profile", None)):
                        record["schedule_profile"] = sampler.schedule_profile(seed, sample_index, difficulty=band)
                    slots[phase, band, seed, sample_index] = record
                    slot_records.append(record)

    identity = {
        "schema": "84def340ce03-lesson-probe-v1", "task_id": TASK_ID,
        "generator_sha256": source_hash, "baseline_generator_sha256": BASELINE_SHA256,
        "probe_sha256": sha(SCRIPT.read_bytes()), "canonical_target_records_sha256": canonical_hash,
        "canonical_rule_hash": rule_hash, "canonical_rule_text_sha256": rule_text_hash,
        "canonical_record_count": len(canonical_rows), "canonical_pair_count": len(canonical_pairs),
        "unique_canonical_pair_count": len({sha(packed([p["input"], p["output"]])) for p in canonical_pairs}),
        "canonical_shortcuts": sorted(shortcuts), "lesson_competitors": sorted(competitors),
        "scored_rivals": sorted(rivals),
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "sampler": {"method": "Direct calls to each source's generate(seed, sample_index, difficulty=band), then public Catalog.apply labels.",
                    "seed_range_inclusive": [0, args.seeds - 1], "sample_indices": [0, 1, 2, 3, 4, 5],
                    "difficulty_bands": list(BANDS), "overrides": {}, "n_demos": 3, "n_queries": 1,
                    "cyclic_starts": [0, 1, 2], "lessons_per_band": args.seeds * 3,
                    "generated_input_slots_per_band": args.seeds * 6,
                    "demo_occurrences_per_band": args.seeds * 9, "query_occurrences_per_band": args.seeds * 3,
                    "overlap": "For each seed, windows [0,1,2]->3, [1,2,3]->4, [2,3,4]->5 share generated inputs.",
                    "conditioning": "None: no retries, selection, rejection or replacement; oracle requests deduplicate identical grids only."},
        "domain": "Default distribution only, all bands, no overrides. Every sampled grid is a rectangular even 0..9 integer grid with h*w/2 <= 30. Three cyclic starts test the declared 3-cycle schedule; this is finite rival evidence, not universal induction.",
        "oracle": {"method": "Public arcpuzzles.Catalog.apply(TASK_ID, grids, reference='canonical', timeout=120)",
                   "batch_size": 64, "unique_requested_inputs_including_mutations": len(inputs),
                   "execution_generator_sha256": source_hash,
                   "public_callable_text_sha256": None,
                   "hash_semantics": "canonical_rule_text_sha256 hashes the exact stored canonical source. Public apply rule_text_sha256 hashes the runtime callable text, so it is captured on the first source-bound call and must remain identical thereafter. executed_rule_hash binds whitespace-normalized canonical source.",
                   "baseline_origin_note": "Baseline inputs come from the preserved original generator; labels execute the unchanged selected canonical rule through the current selected generator's public apply provenance."},
    }
    (out / "plan.json").write_text(json.dumps(identity, indent=2) + "\n")
    (out / "input_slots.jsonl").write_bytes(b"".join(packed(r) + b"\n" for r in slot_records))

    def assert_frozen():
        if sha(source_path.read_bytes()) != source_hash:
            raise RuntimeError("Selected generator changed during the probe")
        rows_now, _, _ = read_canonical()
        if sha(packed(rows_now)) != canonical_hash:
            raise RuntimeError("Target canonical records changed during the probe")

    catalog = Catalog(REPO)
    answers = {}
    compressed_path = out / "oracle_batches.jsonl.gz"
    uncompressed_digest = hashlib.sha256()
    uncompressed_size = 0
    keys = list(inputs)
    batch_count = (len(keys) + 63) // 64
    callable_text_hash = None
    with compressed_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            for batch_index, start in enumerate(range(0, len(keys), 64)):
                assert_frozen()
                batch_keys = keys[start:start + 64]
                applied = catalog.apply(TASK_ID, [inputs[key] for key in batch_keys], reference="canonical", timeout=120)
                line = packed({"batch_index": batch_index, "request_input_sha256": batch_keys, "public_apply_result": applied}) + b"\n"
                uncompressed_digest.update(line)
                uncompressed_size += len(line)
                compressed.write(line)
                if callable_text_hash is None:
                    callable_text_hash = applied["rule_text_sha256"]
                    identity["oracle"]["public_callable_text_sha256"] = callable_text_hash
                if (applied["generator_sha256"] != source_hash or applied["executed_rule_hash"] != rule_hash
                        or applied["rule_text_sha256"] != callable_text_hash or not applied["rule_hash_matches_catalog"]):
                    raise RuntimeError("Public apply source/rule provenance differs from the frozen plan")
                for key, result in zip(batch_keys, applied["results"], strict=True):
                    if result["input_sha256"] != key or result["output"] is None:
                        raise RuntimeError(f"Invalid public apply result: {result}")
                    if grid_sha(result["output"]) != result["output_sha256"]:
                        raise RuntimeError("Public apply output digest does not match the returned grid")
                    answers[key] = result["output"]
                print(f"Oracle batch {batch_index + 1}/{batch_count}: {len(answers)}/{len(inputs)} unique input labels", flush=True)
    assert_frozen()

    errors = []
    rival_cache = {}

    def rival_output(name, key):
        cache_key = name, key
        if cache_key not in rival_cache:
            try:
                rival_cache[cache_key] = (rivals[name](copy.deepcopy(inputs[key])), None)
            except Exception as exc:
                rival_cache[cache_key] = (None, f"{type(exc).__name__}: {exc}")
        return rival_cache[cache_key]

    canonical_fit = {}
    for name in rivals:
        pair_records = []
        for pair in canonical_pairs:
            key = pair["input_sha256"]
            if answers[key] != pair["output"]:
                errors.append(f"Actual Racket does not match canonical pair {pair['record_index']}/{pair['split']}/{pair['pair_index']}")
            candidate, error = rival_output(name, key)
            pair_records.append({k: pair[k] for k in ("record_index", "source", "split", "pair_index", "input_sha256")}
                                | {"matches": candidate == pair["output"] and error is None, "error": error})
        canonical_fit[name] = {"declared_canonical_shortcut": name in shortcuts,
                               "matches": sum(p["matches"] for p in pair_records),
                               "total": len(pair_records), "pairs": pair_records}
        if name in shortcuts and not all(p["matches"] for p in pair_records):
            errors.append(f"Declared canonical shortcut {name!r} does not fit every canonical pair")

    canonical_profiles = {(len(p["input"]), len(p["input"][0]), len({v for row in p["input"] for v in row})) for p in canonical_pairs}
    lesson_records = []
    band_reports = {}
    mutation_examples = []
    for phase in ("baseline", "final"):
        band_reports[phase] = {}
        for band in BANDS:
            selected = [r for r in slot_records if r["phase"] == phase and r["band"] == band]
            stats = {name: Counter() for name in rivals}
            for seed in range(args.seeds):
                for window_start in range(3):
                    demo_keys = [slots[phase, band, seed, i]["input_sha256"] for i in range(window_start, window_start + 3)]
                    query_key = slots[phase, band, seed, window_start + 3]["input_sha256"]
                    statuses = {}
                    for name in rivals:
                        demo_results = [rival_output(name, key) for key in demo_keys]
                        query_result, query_error = rival_output(name, query_key)
                        if any(error is not None for _, error in demo_results) or query_error is not None:
                            status = "rival_error"
                        elif any(value != answers[key] for key, (value, _) in zip(demo_keys, demo_results, strict=True)):
                            status = "demo_eliminated"
                        elif query_result != answers[query_key]:
                            status = "survived_demos_query_changes"
                        else:
                            status = "survived_demos_query_agrees"
                        stats[name][status] += 1
                        statuses[name] = status
                    lesson_records.append({"phase": phase, "band": band, "seed": seed,
                                           "window_start": window_start, "demo_input_sha256": demo_keys,
                                           "query_input_sha256": query_key, "rivals": statuses})
            mutation = Counter()
            for record in selected:
                key, changed_key = record["input_sha256"], record["mutation_input_sha256"]
                input_changes = key != changed_key
                output_changes = answers[key] != answers[changed_key]
                mutation["input_changed" if input_changes else "input_unchanged"] += 1
                mutation["output_changed" if output_changes else "output_unchanged"] += 1
                mutation["input_and_output_changed"] += input_changes and output_changes
                mutation["changed_input_but_unchanged_output"] += input_changes and not output_changes
                if not any(x["phase"] == phase and x["band"] == band for x in mutation_examples):
                    mutation_examples.append({**record, "input": inputs[key], "mutated_input": inputs[changed_key],
                                              "actual_racket_output": answers[key], "mutated_actual_racket_output": answers[changed_key]})
            features = Counter()
            for record in selected:
                feature = record["features"]
                for name in ("has_zero", "has_repeated_tile", "has_adjacent_repeated_tile", "has_uniform_and_mixed_tiles", "smaller_side_not_four"):
                    features[name] += bool(feature[name])
                features["heterogeneous_tile_input"] += feature["mixed_tiles"] > 0
                features["all_uniform_tile_input"] += feature["mixed_tiles"] == 0
                features["canonical_dimension_palette_profile"] += (*feature["shape"], feature["palette_size"]) in canonical_profiles
            per_rival = {}
            for name, counts in stats.items():
                per_rival[name] = {key: counts[key] for key in ("demo_eliminated", "survived_demos_query_changes", "survived_demos_query_agrees", "rival_error")}
                per_rival[name]["survived_demos_total"] = counts["survived_demos_query_changes"] + counts["survived_demos_query_agrees"]
                if phase == "final" and counts["demo_eliminated"] != args.seeds * 3:
                    errors.append(f"Final {band}: {name} eliminated in {counts['demo_eliminated']}/{args.seeds * 3} lessons")
            band_reports[phase][band] = {"lessons": args.seeds * 3, "generated_input_slots": len(selected),
                                         "unique_inputs": len({r["input_sha256"] for r in selected}),
                                         "unique_mutated_inputs": len({r["mutation_input_sha256"] for r in selected}),
                                         "features": dict(features), "rivals": per_rival,
                                         "uniformize_top_left_mutation": dict(mutation)}
            if phase == "baseline" and mutation["output_changed"]:
                errors.append(f"Frozen baseline {band} unexpectedly has mutation-observable output")
            if phase == "final" and mutation["changed_input_but_unchanged_output"]:
                errors.append(f"Final {band} contains an unobservable nontrivial tile-uniformization mutation")
    (out / "lesson_records.jsonl").write_bytes(b"".join(packed(r) + b"\n" for r in lesson_records))
    (out / "mutation_examples.json").write_text(json.dumps(mutation_examples, indent=2) + "\n")

    unique_canonical = {p["input_sha256"]: p for p in canonical_pairs}
    canonical_mutation = {"unique_inputs": len(unique_canonical),
                          "input_changed": sum(p["input_sha256"] != p["mutation_input_sha256"] for p in unique_canonical.values()),
                          "output_changed": sum(answers[p["input_sha256"]] != answers[p["mutation_input_sha256"]] for p in unique_canonical.values())}
    if canonical_mutation["input_changed"] != canonical_mutation["output_changed"]:
        errors.append("Canonical nontrivial tile-uniformization mutation is not output-observable")
    compression = {"compressed_path": "oracle_batches.jsonl.gz", "compressed_size_bytes": compressed_path.stat().st_size,
                   "compressed_sha256": sha(compressed_path.read_bytes()), "original_path": "oracle_batches.jsonl",
                   "original_size_bytes": uncompressed_size, "original_sha256": uncompressed_digest.hexdigest(),
                   "restore_command": "gzip -dc oracle_batches.jsonl.gz > oracle_batches.jsonl",
                   "contents": "One JSON line per public Catalog.apply call, preserving full input/output grids, rule/generator hashes, API result and requested input hashes."}
    report = {**identity, "status": "pass" if not errors else "fail", "errors": errors,
              "canonical_rival_fit": canonical_fit, "canonical_uniformize_top_left_mutation": canonical_mutation,
              "bands": band_reports, "oracle_batches": batch_count, "compression": compression,
              "interpretation": "Every output was obtained from actual Racket through public Catalog.apply. The baseline/final comparison isolates whether tile quadrant information is observable. Finite, overlapping lesson windows bound the induction claim; unsupported overrides are not audited here."}
    assert_frozen()
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "RESTORE.md").write_text("# Oracle evidence\n\nThe complete public API results are losslessly compressed in `oracle_batches.jsonl.gz`.\n\nRun `gzip -dc oracle_batches.jsonl.gz > oracle_batches.jsonl` from this directory.\nVerify the resulting SHA-256 and byte count against `report.json` → `compression`.\n\n`input_slots.jsonl` maps generator source, seeds, bands and sample indices to oracle input hashes.\n`lesson_records.jsonl` maps each overlapping lesson to its demo/query hashes and rival outcomes.\nNo private runner APIs or Python-generated reference labels were used.\n")
    manifest = {p.name: {"size_bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
                for p in out.iterdir() if p.is_file()}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "generator_sha256": source_hash,
                      "canonical_pair_count": len(canonical_pairs), "unique_canonical_pair_count": len(unique_canonical),
                      "bands": band_reports, "errors": errors}, indent=2), flush=True)
    return 0 if not errors else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory, outside any runtime tree")
    parser.add_argument("--baseline-generator", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=100, help="At least 100 independent seeds per band")
    parser.add_argument("--expected-generator-sha256")
    args = parser.parse_args()
    if args.seeds < 100:
        parser.error("At least 100 seeds per band are required for this probe")
    try:
        return run(args)
    except Exception as exc:
        failure = {"status": "error", "task_id": TASK_ID, "error": f"{type(exc).__name__}: {exc}",
                   "traceback": traceback.format_exc(), "cwd": os.getcwd(), "argv": sys.argv}
        if not isinstance(exc, FileExistsError) and args.out.is_dir() and not (args.out / "report.json").exists():
            (args.out / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
        print(json.dumps(failure, indent=2), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

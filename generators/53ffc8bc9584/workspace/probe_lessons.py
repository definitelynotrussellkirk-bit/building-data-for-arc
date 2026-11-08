#!/usr/bin/env python3
"""Source-bound lesson census, retained failures, and public sampler parity.

From packet_root (the wrapper changes cwd to repo):
  python3 run_with_racket.py python3 generators/53ffc8bc9584/workspace/probe_lessons.py \
      --phase final --out ../checks/lesson-final

--per-band counts independent seed groups. Each group tests all four cyclic
four-demo starts, so its default 100 gives 400 complete lessons per band.
Overlapping windows are intentional and are reported separately from unique
inputs. The cheap census independently implements the selected local rule;
public generate_in_runtime verifies sampler parity and Racket outputs on a
smaller recorded subset. Supported CLI `arcpuzzles apply` verifies decisive
inputs. No private runner functions, solve files, or hidden labels are read.

An optional --runtime uses a previously prepared portable snapshot, checking
every mapped file against RUNTIME_MANIFEST.json before importing its generator.
This permits honest before/after measurements even after selected source edits.
Output directories must be new: earlier failures are never overwritten.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
from collections import Counter
from contextlib import nullcontext
from typing import Any

TASK_ID = "53ffc8bc9584"
BANDS = ("easy", "medium", "hard")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_row(handle, value: Any) -> None:
    handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    handle.flush()


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    """Test each black cell against four original-grid diagonal triples."""
    h, w = len(grid), len(grid[0])
    out = copy.deepcopy(grid)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            for dr in (-1, 1):
                for dc in (-1, 1):
                    if (0 <= r + dr < h and 0 <= c + dc < w
                            and grid[r + dr][c] == 4
                            and grid[r][c + dc] == 4
                            and grid[r + dr][c + dc] == 4):
                        out[r][c] = 9
    return out


def perpendicular_diagnostic(grid: list[list[int]]) -> list[list[int]]:
    """Additional hypothesis, kept distinct from the generator declarations."""
    h, w = len(grid), len(grid[0])
    out = copy.deepcopy(grid)
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 and any(
                0 <= r + dr < h and 0 <= c + dc < w
                and grid[r + dr][c] == 4 and grid[r][c + dc] == 4
                for dr in (-1, 1) for dc in (-1, 1)
            ):
                out[r][c] = 9
    return out


def shape_signature(cells) -> str:
    if not cells:
        return "none"
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return json.dumps(sorted((r - top, c - left) for r, c in cells), separators=(",", ":"))


def component_shapes(grid) -> dict[str, list[str]]:
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4}
    singletons, linked = set(), []
    while unseen:
        stack = [unseen.pop()]
        comp = set(stack)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    comp.add(p)
                    stack.append(p)
        if len(comp) == 1:
            singletons.update(comp)
        if len(comp) == 5:
            linked.append(shape_signature(comp))
    return {"linked_shapes": linked,
            "singleton_shapes": [shape_signature(singletons)] if singletons else []}


def import_snapshot(runtime: Path, relative: str):
    """Compile the exact hashed bytes; do not accept stale bytecode caches."""
    sys.path.insert(0, str(runtime))
    module_name = relative.removesuffix(".py").replace("/", ".")
    package = module_name.rsplit(".", 1)[0]
    importlib.import_module(package)
    path = runtime / relative
    source = path.read_bytes()
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    module.__package__ = package
    sys.modules[module_name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module, source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--library", type=Path, default=Path.cwd())
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", choices=("before", "intermediate", "final"), required=True)
    parser.add_argument("--per-band", type=int, default=100, help="seed groups per band; four starts per group")
    parser.add_argument("--seed", type=int, default=53000)
    parser.add_argument("--public-per-start", type=int, default=1,
                        help="Racket public episodes per band/start (0 explicitly skips parity)")
    parser.add_argument("--skip-apply", action="store_true", help="explicitly skip decisive CLI authority checks")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if args.per_band < 1 or args.public_per_start < 0 or args.timeout <= 0:
        parser.error("per-band and timeout must be positive; public-per-start must be nonnegative")
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import generate_in_runtime, prepare_runtime

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    catalog = Catalog(args.library.resolve())
    catalog_row = catalog.describe(TASK_ID)
    context = nullcontext(str(args.runtime.resolve())) if args.runtime else tempfile.TemporaryDirectory(prefix="lesson-probe-")
    started = time.monotonic()
    with context as directory:
        runtime = Path(directory)
        if not args.runtime:
            prepare_runtime(catalog, runtime, TASK_ID)
        manifest = json.loads((runtime / "RUNTIME_MANIFEST.json").read_text())
        mismatches = [item["runtime_path"] for item in manifest["files"]
                      if not (runtime / item["runtime_path"]).is_file()
                      or file_hash(runtime / item["runtime_path"]) != item["sha256"]]
        if mismatches:
            dump(out / "manifest-failure.json", {"runtime": str(runtime), "mismatches": mismatches})
            raise RuntimeError(f"Runtime mapped sources differ from manifest: {mismatches}")
        module, source = import_snapshot(runtime, catalog_row["runtime_generator"])
        (out / "generator_sampled.py").write_bytes(source)
        (out / "probe_sampled.py").write_bytes(Path(__file__).read_bytes())
        from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
        from puzzle_generators.helpers.grid import is_well_formed

        rule_source = canonical_rule_source(getattr(module, "RULE_TASK_ID", TASK_ID))
        source_identity = {
            "generator_sha256": hashlib.sha256(source).hexdigest(),
            "generator_version": getattr(module, "VERSION", None),
            "declared_rule_hash": getattr(module, "RULE_HASH", None),
            "selected_rule_hash": normalized_rule_hash(rule_source),
            "selected_rule_source_sha256": hashlib.sha256(rule_source.encode()).hexdigest(),
            "runtime_manifest_sha256": file_hash(runtime / "RUNTIME_MANIFEST.json"),
            "worker_sha256": file_hash(runtime / "arcpuzzles_worker.py"),
            "runner_sha256": file_hash(runtime / "puzzle_generators/runner.py"),
            "grid_helpers_sha256": file_hash(runtime / "puzzle_generators/helpers/grid.py"),
            "probe_sha256": file_hash(Path(__file__)),
        }
        dump(out / "runtime-source-manifest.json", manifest)
        report = {
            "schema": "53ffc8bc9584-source-bound-lessons-v1", "task_id": TASK_ID,
            "phase": args.phase, "source": source_identity,
            "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
            "runtime_cwd": str(runtime), "runtime_prepared_by_probe": not bool(args.runtime),
            "sampler": {
                "policy": "public arcpuzzles worker: fixed seed, consecutive candidate sample_index, up to 25 candidates; first 4 accepted demos and next 1 query",
                "validation": "public is_well_formed; self_check with difficulty; reject checker mutation, malformed output, disallowed identity, duplicate 12-hex input/output pair digest",
                "census_output_authority": "independent Python selected-rule interpretation; not itself a Racket label",
                "seed_groups_per_band": args.per_band, "seed_rule": "seed + group_index",
                "seed_range_inclusive": [args.seed, args.seed + args.per_band - 1],
                "start_rule": "4 * group_index + cyclic_start", "cyclic_starts": [0, 1, 2, 3],
                "candidate_index_range_if_no_rejections": [0, 4 * (args.per_band - 1) + 7],
                "overrides": {}, "n_train": 4, "n_test": 1,
                "warning": "Window overlap is measured; 400 lesson windows are not 400 independent draws.",
            },
            "limitations": [
                "Finite generated-domain census, not universal induction or exhaustive ARC-grid verification.",
                "Default overrides only; override boundary tests belong to the focused test suite.",
                "The cheaper census uses an independent Python rule; only recorded public parity and apply inputs have Racket outputs.",
                "Canonical exact profiles mean height/width/palette cardinality; exact palette values are also reported separately.",
                "Diagnostic perpendicular hypothesis is additional to, and reported separately from, dynamically loaded declarations.",
            ],
        }
        failure_handle = (out / "failures.jsonl").open("w")
        inputs_handle = (out / "inputs.jsonl").open("w")
        lesson_handle = (out / "lessons.jsonl").open("w")
        failures = Counter()

        def fail(kind, detail):
            failures[kind] += 1
            write_row(failure_handle, {"kind": kind, "source": source_identity, **detail})

        if source_identity["declared_rule_hash"] != source_identity["selected_rule_hash"]:
            fail("rule_hash_mismatch", {})

        registries = {name: dict(getattr(module, name, {}))
                      for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")}
        rivals = {f"{registry}:{name}": function for registry, values in registries.items()
                  for name, function in values.items()}
        rivals["DIAGNOSTIC:perpendicular_without_diagonal"] = perpendicular_diagnostic
        report["rival_declarations"] = {name: list(values) for name, values in registries.items()}
        for registry, values in registries.items():
            if not values:
                fail("empty_rival_declaration", {"registry": registry})
        pairs = canonical_pairs(TASK_ID)
        usable = [pair for pair in pairs if is_well_formed(pair.get("input")) and is_well_formed(pair.get("output"))]
        profiles = {(len(p["input"]), len(p["input"][0]), len({v for row in p["input"] for v in row})) for p in usable}
        palettes = {(len(p["input"]), len(p["input"][0]), tuple(sorted({v for row in p["input"] for v in row}))) for p in usable}
        canonical_result = {"read_pairs": len(pairs), "usable_pairs": len(usable),
                            "skipped_unusable_pairs": len(pairs) - len(usable),
                            "profiles": sorted(profiles), "exact_palette_profiles": sorted(palettes),
                            "rival_fit_counts": {}, "strict_count": 0, "accepted_count": 0}
        for index, pair in enumerate(usable):
            canonical_result["strict_count"] += not bool(module.strict_canonical_like(copy.deepcopy(pair["input"])))
            canonical_result["accepted_count"] += not bool(module.self_check(copy.deepcopy(pair["input"])))
            if independent_rule(pair["input"]) != pair["output"]:
                fail("canonical_rule_mismatch", {"canonical_index": index, "pair": pair})
        for name, rival in rivals.items():
            fits = 0
            for index, pair in enumerate(usable):
                actual = rival(copy.deepcopy(pair["input"]))
                fits += actual == pair["output"]
                if actual != pair["output"]:
                    fail("canonical_rival_does_not_fit", {"rival": name, "canonical_index": index,
                                                         "pair": pair, "rival_output": actual})
            canonical_result["rival_fit_counts"][name] = fits
        report["canonical"] = canonical_result
        if not usable:
            fail("no_usable_canonical_pairs", {})

        cache, unique, decisive = {}, {}, {}

        def get_input(band, seed, index):
            key = (band, seed, index)
            if key in cache:
                return cache[key]
            replay = {"band": band, "seed": seed, "sample_index": index, "overrides": {}}
            grid = None
            try:
                generated = module.generate(seed=seed, sample_index=index, difficulty=band)
                grid = generated.get("input") if isinstance(generated, dict) else generated
                if not is_well_formed(grid):
                    raise ValueError("malformed generated input")
                checked = copy.deepcopy(grid)
                sig = inspect.signature(module.self_check)
                supports_band = "difficulty" in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                findings = module.self_check(checked, **({"difficulty": band} if supports_band else {}))
                if findings or checked != grid:
                    raise ValueError(f"self_check findings or mutation: {findings}")
                expected = independent_rule(grid)
                if not is_well_formed(expected):
                    raise ValueError("validate.output_not_well_formed")
                if grid == expected and not getattr(module, "ALLOW_IDENTITY_OUTPUT", False):
                    raise ValueError("validate.output_equals_input")
                identifier = digest(grid)
                if identifier not in unique:
                    strict_reasons = module.strict_canonical_like(copy.deepcopy(grid))
                    observed = module.observe_overrides(copy.deepcopy(grid))
                    colors = tuple(sorted({v for row in grid for v in row}))
                    record = {"input_sha256": identifier, "first_replay": replay, "input": grid,
                              "independent_output": expected, "output_sha256": digest(expected),
                              "strict_reasons": strict_reasons, "observed": observed,
                              "exact_profile": (len(grid), len(grid[0]), len(colors)) in profiles,
                              "exact_palette_profile": (len(grid), len(grid[0]), colors) in palettes,
                              "rival_disagreements": {}, **component_shapes(grid)}
                    for name, rival in rivals.items():
                        rival_output = rival(copy.deepcopy(grid))
                        if rival_output != expected:
                            record["rival_disagreements"][name] = rival_output
                            decisive.setdefault(("refutation", band, name), identifier)
                    if module.rule_mirror(copy.deepcopy(grid)) != expected:
                        fail("generator_mirror_mismatch", {**replay, "input": grid, "independent_output": expected,
                                                           "generator_mirror_output": module.rule_mirror(copy.deepcopy(grid))})
                    unique[identifier] = record
                    write_row(inputs_handle, record)
                decisive.setdefault(("scene", band, unique[identifier]["observed"]["scene_family"]), identifier)
                value = {"input_sha256": identifier, "pair": {"input": grid, "output": expected},
                         "pair_digest": digest([grid, expected])[:12], "sample_index": index}
            except Exception as exc:
                value = {"rejection": {**replay, "error": type(exc).__name__, "reason": str(exc), "input": grid}}
                fail("candidate_rejection", value["rejection"])
            cache[key] = value
            return value

        def lesson(band, seed, start):
            accepted, rejected, seen = [], [], set()
            for index in range(start, start + 25):
                value = get_input(band, seed, index)
                if "rejection" in value:
                    rejected.append(value["rejection"])
                elif value["pair_digest"] in seen:
                    rejected.append({"band": band, "seed": seed, "sample_index": index,
                                     "overrides": {}, "error": "ValueError", "reason": "duplicate pair"})
                else:
                    seen.add(value["pair_digest"])
                    accepted.append(value)
                if len(accepted) == 5:
                    break
            return accepted, rejected

        report["bands"] = {}
        global_occurrences = Counter()
        for band in BANDS:
            stats = {"requested_lessons": args.per_band * 4, "complete_lessons": 0,
                     "contract_failures": 0, "candidate_rejection_occurrences": 0,
                     "surviving_rival_lessons": Counter(), "cyclic_starts": Counter()}
            occurrences, demo_occurrences, query_occurrences = Counter(), Counter(), Counter()
            for group in range(args.per_band):
                for cyclic in range(4):
                    seed, start = args.seed + group, 4 * group + cyclic
                    accepted, rejected = lesson(band, seed, start)
                    entry = {"band": band, "group_index": group, "cyclic_start": cyclic,
                             "seed": seed, "sample_index": start, "overrides": {},
                             "accepted_indices": [x["sample_index"] for x in accepted],
                             "input_sha256s": [x["input_sha256"] for x in accepted], "rejections": rejected}
                    stats["candidate_rejection_occurrences"] += len(rejected)
                    if len(accepted) != 5:
                        fail("incomplete_lesson", entry)
                        write_row(lesson_handle, entry)
                        continue
                    stats["complete_lessons"] += 1
                    stats["cyclic_starts"][cyclic] += 1
                    demos = [x["pair"] for x in accepted[:4]]
                    query = accepted[4]["pair"]
                    reasons = module.lesson_identifiable(copy.deepcopy(demos), copy.deepcopy(query))
                    survivors = [name for name in rivals if all(name not in unique[x["input_sha256"]]["rival_disagreements"] for x in accepted[:4])]
                    entry.update({"lesson_identifiable_reasons": reasons, "surviving_rivals": survivors})
                    if reasons:
                        stats["contract_failures"] += 1
                        fail("lesson_contract_failure", entry)
                    if survivors:
                        fail("rival_survives_complete_lesson", entry)
                    stats["surviving_rival_lessons"].update(survivors)
                    for pos, item in enumerate(accepted):
                        identifier = item["input_sha256"]
                        occurrences[identifier] += 1
                        (demo_occurrences if pos < 4 else query_occurrences)[identifier] += 1
                    write_row(lesson_handle, entry)
                if group % 25 == 24 or group == args.per_band - 1:
                    print(f"{band}: {group + 1}/{args.per_band} seed groups, {stats['complete_lessons']} complete lessons", flush=True)
            stats.update({"demo_input_occurrences": sum(demo_occurrences.values()),
                          "query_input_occurrences": sum(query_occurrences.values()),
                          "all_input_occurrences": sum(occurrences.values()),
                          "unique_demo_inputs": len(demo_occurrences), "unique_query_inputs": len(query_occurrences),
                          "unique_inputs": len(occurrences),
                          "unique_inputs_used_as_both_demo_and_query": len(set(demo_occurrences) & set(query_occurrences)),
                          "unique_sample_requests": sum(k[0] == band for k in cache)})
            for metric, test in (("strict", lambda r: not r["strict_reasons"]),
                                 ("canonical_exact_profile", lambda r: r["exact_profile"]),
                                 ("canonical_exact_palette_profile", lambda r: r["exact_palette_profile"])):
                hits = sum(n for h, n in occurrences.items() if test(unique[h]))
                unique_hits = sum(test(unique[h]) for h in occurrences)
                stats[metric] = {"occurrence_hits": hits, "occurrence_denominator": sum(occurrences.values()),
                                 "occurrence_fraction": hits / sum(occurrences.values()) if occurrences else None,
                                 "unique_input_hits": unique_hits, "unique_input_denominator": len(occurrences),
                                 "unique_input_fraction": unique_hits / len(occurrences) if occurrences else None}
            stats["scene_family_unique_inputs"] = Counter(unique[h]["observed"]["scene_family"] for h in occurrences)
            stats["linked_shapes_unique_inputs"] = Counter(s for h in occurrences for s in unique[h]["linked_shapes"])
            stats["singleton_shapes_unique_inputs"] = Counter(s for h in occurrences for s in unique[h]["singleton_shapes"])
            stats["rival_refuted_unique_inputs"] = Counter(name for h in occurrences for name in unique[h]["rival_disagreements"])
            report["bands"][band] = stats
            global_occurrences.update(occurrences)
        report["census_totals"] = {"complete_lessons": sum(s["complete_lessons"] for s in report["bands"].values()),
                                   "unique_inputs": len(global_occurrences),
                                   "input_occurrences": sum(global_occurrences.values()),
                                   "unique_sample_requests": len(cache)}

        # Public batch defaults keep sample_index=0 and increment the seed.
        # Four-start coverage alone cannot reveal a query-family alias here.
        default_report = {"policy": "Catalog.generate(count=per_band, seed=seed, sample_index=0, n_train=4, n_test=1, difficulty=band)",
                          "outputs": "independent Python rule; smaller public parity subset below uses Racket",
                          "seed_range_inclusive": [args.seed, args.seed + args.per_band - 1],
                          "query_family_gate": {"enabled": args.per_band >= 4,
                                                "skip_reason": None if args.per_band >= 4 else "Fewer than four seeds do not cover a full declared family cycle."},
                          "bands": {}}
        default_global = Counter()
        with (out / "default-lessons.jsonl").open("w") as default_handle:
            for band in BANDS:
                stats = {"requested_lessons": args.per_band, "complete_lessons": 0,
                         "query_scene_families": Counter(), "demo_scene_families": Counter(),
                         "surviving_rival_lessons": Counter(), "contract_failures": 0,
                         "candidate_rejection_occurrences": 0}
                occurrences, queries, demos = Counter(), Counter(), Counter()
                for group in range(args.per_band):
                    seed = args.seed + group
                    accepted, rejected = lesson(band, seed, 0)
                    entry = {"policy": "public_default", "band": band, "seed": seed,
                             "sample_index": 0, "overrides": {},
                             "accepted_indices": [x["sample_index"] for x in accepted],
                             "input_sha256s": [x["input_sha256"] for x in accepted], "rejections": rejected}
                    stats["candidate_rejection_occurrences"] += len(rejected)
                    if len(accepted) != 5:
                        fail("incomplete_default_lesson", entry)
                    else:
                        stats["complete_lessons"] += 1
                        reasons = module.lesson_identifiable([copy.deepcopy(x["pair"]) for x in accepted[:4]],
                                                             copy.deepcopy(accepted[4]["pair"]))
                        survivors = [name for name in rivals if all(name not in unique[x["input_sha256"]]["rival_disagreements"] for x in accepted[:4])]
                        entry.update({"lesson_identifiable_reasons": reasons, "surviving_rivals": survivors})
                        if reasons:
                            stats["contract_failures"] += 1
                            fail("default_lesson_contract_failure", entry)
                        if survivors:
                            fail("rival_survives_default_lesson", entry)
                        stats["surviving_rival_lessons"].update(survivors)
                        for pos, item in enumerate(accepted):
                            identifier = item["input_sha256"]
                            occurrences[identifier] += 1
                            (demos if pos < 4 else queries)[identifier] += 1
                            stats["demo_scene_families" if pos < 4 else "query_scene_families"][unique[identifier]["observed"]["scene_family"]] += 1
                    write_row(default_handle, entry)
                stats.update({"input_occurrences": sum(occurrences.values()), "unique_inputs": len(occurrences),
                              "demo_occurrences": sum(demos.values()), "unique_demo_inputs": len(demos),
                              "query_occurrences": sum(queries.values()), "unique_query_inputs": len(queries),
                              "strict_occurrence_hits": sum(n for h, n in occurrences.items() if not unique[h]["strict_reasons"]),
                              "canonical_exact_profile_occurrence_hits": sum(n for h, n in occurrences.items() if unique[h]["exact_profile"]),
                              "query_families_not_observed": sorted(set(getattr(module, "SCENE_FAMILIES", ())) - set(stats["query_scene_families"]))})
                if args.per_band >= 4 and stats["query_families_not_observed"]:
                    fail("default_query_family_missing", {"band": band, "seed_range_inclusive": [args.seed, args.seed + args.per_band - 1],
                                                           "sample_index": 0, "overrides": {},
                                                           "missing_families": stats["query_families_not_observed"],
                                                           "query_scene_families": stats["query_scene_families"],
                                                           "fixtures": "default-lessons.jsonl and inputs.jsonl"})
                default_report["bands"][band] = stats
                default_global.update(occurrences)
        default_report["totals"] = {"complete_lessons": sum(s["complete_lessons"] for s in default_report["bands"].values()),
                                    "input_occurrences": sum(default_global.values()), "unique_inputs": len(default_global)}
        report["public_default_census"] = default_report

        # This supported public API is the same worker reached by Catalog.generate.
        # A passed old runtime intentionally uses its own source hash and explicit
        # unapproved research metadata, never stale catalog admission metadata.
        parity = {"public_api": "arcpuzzles.runtime.generate_in_runtime", "episodes_checked": 0,
                  "mismatches": 0, "requested_per_band_per_start": args.public_per_start,
                  "seed_rule": "seed + episode_index", "sample_index_rule": "cyclic_start (0..3)",
                  "runtime_cwd": str(runtime), "research_approved": False}
        row = {**catalog_row, "generator_sha256": source_identity["generator_sha256"], "approved": False}
        with (out / "public-parity.jsonl").open("w") as parity_handle:
            for band in BANDS:
                for cyclic in range(4):
                    if not args.public_per_start:
                        continue
                    print(f"Public Racket sampler parity: {band}, start {cyclic}", flush=True)
                    try:
                        episodes = generate_in_runtime(runtime, row, count=args.public_per_start,
                                                       seed=args.seed, difficulty=band, n_train=4, n_test=1,
                                                       sample_index=cyclic, overrides={}, timeout=args.timeout)
                        for episode in episodes:
                            expected, rejected = lesson(band, episode["seed"], cyclic)
                            mismatch = (episode["train"] + episode["test"] != [v["pair"] for v in expected]
                                        or episode["sample_indices"] != [v["sample_index"] for v in expected]
                                        or len(episode["rejections"]) != len(rejected)
                                        or episode["provenance"]["generator_sha256"] != source_identity["generator_sha256"]
                                        or episode["executed_rule_hash"] != source_identity["selected_rule_hash"])
                            record = {"band": band, "cyclic_start": cyclic, "matches_cheap_sampler": not mismatch,
                                      "episode": {k: v for k, v in episode.items() if k != "program"}}
                            write_row(parity_handle, record)
                            parity["episodes_checked"] += 1
                            if mismatch:
                                parity["mismatches"] += 1
                                fail("public_sampler_mismatch", {**record, "cheap_inputs": [v["input_sha256"] for v in expected],
                                                                  "cheap_rejections": rejected})
                    except Exception as exc:
                        parity["mismatches"] += 1
                        fail("public_sampler_error", {"band": band, "cyclic_start": cyclic, "seed": args.seed,
                                                      "error": f"{type(exc).__name__}: {exc}"})
        report["public_sampler_parity"] = parity

        # Deduplicate scene/refutation witnesses, plus every usable canonical input.
        authority_inputs = {digest(p["input"]): p["input"] for p in usable}
        authority_inputs.update({h: unique[h]["input"] for h in decisive.values()})
        report["decisive_inputs"] = [{"reason": list(k), "input_sha256": h} for k, h in decisive.items()]
        authority = {"skipped": args.skip_apply, "inputs_checked": 0, "disagreements": 0, "commands": []}
        if not args.skip_apply:
            grids = list(authority_inputs.values())
            for start in range(0, len(grids), 64):
                batch = grids[start:start + 64]
                input_path = out / f"authority-inputs-{start // 64}.json"
                result_path = out / f"authority-results-{start // 64}.json"
                dump(input_path, {"inputs": batch})
                command = [sys.executable, "-m", "arcpuzzles", "--library", str(catalog.root), "apply", TASK_ID,
                           "--input", str(input_path), "--out", str(result_path), "--timeout", str(args.timeout)]
                run = subprocess.run(command, cwd=catalog.root, capture_output=True, text=True,
                                     timeout=args.timeout + 15)
                authority["commands"].append({"argv": command, "cwd": str(catalog.root), "exit_code": run.returncode,
                                              "stdout": run.stdout, "stderr": run.stderr,
                                              "input_file": input_path.name, "result_file": result_path.name})
                if run.returncode or not result_path.is_file():
                    fail("authority_command_error", authority["commands"][-1])
                    continue
                result = json.loads(result_path.read_text())
                # apply selects current rule source. Its generator hash is
                # recorded separately: an old --runtime may be intentionally different.
                authority["catalog_generator_sha256"] = result["generator_sha256"]
                if result["executed_rule_hash"] != source_identity["selected_rule_hash"]:
                    fail("authority_rule_changed", {"authority": result["executed_rule_hash"],
                                                    "sampled_rule": source_identity["selected_rule_hash"]})
                for applied in result["results"]:
                    authority["inputs_checked"] += 1
                    if applied["error"] or applied["output"] != independent_rule(applied["input"]):
                        authority["disagreements"] += 1
                        fail("authority_output_mismatch", applied)
        report["authority"] = authority
        if file_hash(runtime / catalog_row["runtime_generator"]) != source_identity["generator_sha256"]:
            fail("sampled_source_changed_during_run", {})
        report["failure_counts"] = dict(failures)
        report["status"] = "pass" if not failures else "fail"
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["evidence_note"] = "failures.jsonl references lossless input/independent-output/rival-output fixtures in inputs.jsonl; each lesson records exact seed, indices and overrides. generator_sampled.py preserves exact sampled bytes."
        report["stored_unique_inputs_including_default_and_public_parity"] = len(unique)
        report["unique_sample_requests_including_default_and_public_parity"] = len(cache)
        for handle in (failure_handle, inputs_handle, lesson_handle):
            handle.close()
        report["artifacts"] = {p.name: {"sha256": file_hash(p), "bytes": p.stat().st_size}
                               for p in sorted(out.iterdir()) if p.is_file()}
        dump(out / "report.json", report)
        print(json.dumps({"status": report["status"], "report": str(out / "report.json"),
                          "source": source_identity, "census_totals": report["census_totals"],
                          "failure_counts": dict(failures)}), flush=True)
        return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

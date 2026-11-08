"""Reproduce task-local distribution and finite-rival lesson measurements.

From the review packet root, after freezing the selected generator::

    python3 run_with_racket.py python3 \
        generators/b985d561c63b/workspace/probe_distribution.py \
        --library . --out ../checks/final_probe --lessons 100 \
        --short-lesson-probe

The wrapper sets the bundled Racket runtime and changes the child cwd to repo.
In a standalone repository with Racket installed, call this file directly and
pass --library and --out explicitly; all paths may be relocated.

Catalog.generate supplies every generated output through the selected canonical
Racket rule. Three batched starts (0, 1, 2 by default) cover cyclic starts without
claiming their overlapping windows are independent lessons. The first start
provides 100 nonoverlapping lessons per band, each with three demos and two
queries. A separate input-derived Python oracle is checked against every actual
Racket output. Rival functions are loaded from the selected generator itself.

Only this task is inspected. No reference, generator, catalog, or approval files
are modified. Optional --runtime imports the generator from a previously prepared
runtime and requires its bytes to equal the selected library generator.
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
import time
from typing import Any

TASK_ID = "b985d561c63b"
BANDS = ("easy", "medium", "hard")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid, include):
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or not include(grid[r][c]):
                continue
            seen.add((r, c))
            stack, cells = [(r, c)], []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and include(grid[nr][nc])):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def bbox(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return (r0, c0, max(r for r, _ in cells) - r0 + 1,
            max(c for _, c in cells) - c0 + 1)


def inspect_input(grid):
    """Independent input parser: no generator helpers or generation metadata."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("empty or malformed grid")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30 or any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("ragged or oversized grid")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("noninteger or invalid ARC color")
    source = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)]
    if not source:
        raise ValueError("missing template")
    sr, sc, th, tw = bbox(source)
    template = [row[sc:sc + tw] for row in grid[sr:sr + th]]
    if any(v == 5 for row in template for v in row):
        raise ValueError("gray cells inside the source bounding box")
    colors = {v for row in template for v in row if v not in (0, 5)}
    if len(colors) < 2:
        raise ValueError("template does not expose two colors")
    source_components = components(grid, lambda v: v not in (0, 5))
    regions = components(grid, lambda v: v == 5)
    if not regions:
        raise ValueError("no gray targets")
    region_boxes = [bbox(region) for region in regions]
    for cells, (rr, cc, rh, rw) in zip(regions, region_boxes, strict=True):
        if len(cells) != rh * rw:
            raise ValueError("nonrectangular gray target")
        if rh < th or rw < tw:
            raise ValueError("target smaller than source template")
        # Bounding boxes, including template holes, require a zero-cell margin.
        row_separate = rr >= sr + th + 1 or sr >= rr + rh + 1
        col_separate = cc >= sc + tw + 1 or sc >= cc + rw + 1
        if not (row_separate or col_separate):
            raise ValueError("target is not separated from the whole source box")
    for i, (ar, ac, ah, aw) in enumerate(region_boxes):
        for br, bc, bh, bw in region_boxes[i + 1:]:
            if not (br >= ar + ah + 1 or ar >= br + bh + 1
                    or bc >= ac + aw + 1 or ac >= bc + bw + 1):
                raise ValueError("targets lack a zero-cell margin")
    dense = all(v != 0 for row in template for v in row)
    congruent = all((rh, rw) == (th, tw) for _, _, rh, rw in region_boxes)
    features = {
        "grid_shape": [h, w], "grid_palette_size": len({v for row in grid for v in row}),
        "template_bbox": [sr, sc, th, tw], "template_palette": sorted(colors),
        "source_components": len(source_components), "template_holes": sum(v == 0 for row in template for v in row),
        "target_count": len(regions), "target_boxes": [list(b) for b in region_boxes],
        "target_surplus_cells": sum(rh * rw - th * tw for _, _, rh, rw in region_boxes),
        "dense_congruent": dense and congruent,
        "canonical_exact_profile": (h, w, len({v for row in grid for v in row})) == (10, 10, 4),
        "source_not_leftmost": any((cc, rr) < (sc, sr) for rr, cc, _, _ in region_boxes),
    }
    return template, region_boxes, features


def independent_oracle(grid):
    """Copy the entire source bounding box at each target's top-left corner."""
    template, targets, _ = inspect_input(grid)
    out = [row[:] for row in grid]
    for rr, cc, _, _ in targets:
        for dr, row in enumerate(template):
            out[rr + dr][cc:cc + len(row)] = row
    return out


def hook_reasons(hook, *args, **kwargs):
    supplied = deepcopy(args)
    result = hook(*supplied, **kwargs)
    if supplied != args:
        raise ValueError(f"{hook.__name__} mutated its inputs")
    if isinstance(result, bool):
        return [] if result else ["predicate returned False"]
    if isinstance(result, list) and all(isinstance(item, str) for item in result):
        return result
    raise TypeError(f"{hook.__name__} returned {type(result).__name__}, expected bool or list[str]")


def call_rule(fn, grid):
    given = deepcopy(grid)
    output = fn(given)
    if given != grid:
        raise ValueError(f"{fn.__name__} mutated its input")
    if not isinstance(output, list) or len(output) != len(grid):
        raise ValueError(f"{fn.__name__} returned the wrong grid height")
    if any(not isinstance(row, list) or len(row) != len(grid[0])
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in output):
        raise ValueError(f"{fn.__name__} returned a malformed output grid")
    return output


def declaration(module, name):
    value = getattr(module, name, None)
    if not isinstance(value, dict) or not value or any(not isinstance(k, str) or not callable(v) for k, v in value.items()):
        raise ValueError(f"{name} must declare nonempty named callables")
    return value


def choose_library(explicit):
    if explicit is not None:
        return explicit.resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "catalog/puzzles.jsonl").is_file():
            return parent
    raise ValueError("Pass --library /path/to/repo")


def load_generator(library, runtime):
    selected = library / f"generators/{TASK_ID}/generator.py"
    source = selected if runtime is None else runtime.resolve() / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py"
    if file_hash(source) != file_hash(selected):
        raise ValueError("The supplied runtime generator differs from the selected library source")
    sys.path.insert(0, str(library / "shared/runtime" if runtime is None else runtime.resolve()))
    spec = importlib.util.spec_from_file_location("b985d561c63b_probe_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source


def canonical_pairs(catalog):
    task = catalog.get(TASK_ID)
    result, rules = [], []
    for variant in task["variants"]:
        if variant.get("task_id") != TASK_ID:
            raise ValueError("Catalog returned a different task variant")
        if variant.get("program_solution"):
            rules.append(variant["program_solution"])
        for split in ("train", "test"):
            pairs = variant.get(split, [])
            if not isinstance(pairs, list):
                raise ValueError("Unexpected canonical encoding for this task")
            for pair in pairs:
                result.append({"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])})
    if not result or not rules or len({" ".join(rule.split()) for rule in rules}) != 1:
        raise ValueError("Missing canonical examples or ambiguous selected rule")
    return result, rules[0]


def run(args, report):
    library = choose_library(args.library)
    sys.path.insert(0, str(library / "src"))
    from arcpuzzles import Catalog

    catalog = Catalog(library)
    module, imported_source = load_generator(library, args.runtime)
    selected = library / f"generators/{TASK_ID}/generator.py"
    generator_hash = file_hash(selected)
    pairs, rule_source = canonical_pairs(catalog)
    rule_hash = hashlib.sha256(" ".join(rule_source.split()).encode()).hexdigest()[:12]
    report["sources"] = {
        "task_id": TASK_ID, "generator_sha256": generator_hash,
        "generator_version": getattr(module, "VERSION", None),
        "selected_generator": str(selected), "imported_generator": str(imported_source),
        "rule_hash": rule_hash, "rule_source_sha256": hashlib.sha256(rule_source.encode()).hexdigest(),
        "probe_sha256": file_hash(Path(__file__)),
    }
    shortcuts = declaration(module, "CANONICAL_SHORTCUTS")
    competitors = declaration(module, "LESSON_COMPETITORS")
    rivals = declaration(module, "SEMANTIC_RIVALS")
    witnesses = declaration(module, "SEMANTIC_WITNESSES")
    witness_rivals = getattr(module, "WITNESS_RIVALS", {})
    report["declarations"] = {
        name: sorted(value) for name, value in (("CANONICAL_SHORTCUTS", shortcuts),
            ("LESSON_COMPETITORS", competitors), ("SEMANTIC_RIVALS", rivals), ("SEMANTIC_WITNESSES", witnesses))
    }
    report["declarations"]["WITNESS_RIVALS"] = witness_rivals
    report["declarations"]["SCHEDULE_PROFILES"] = [repr(p) for p in getattr(module, "SCHEDULE_PROFILES", [])]
    lesson_hook = getattr(module, "lesson_identifiable", None)
    if lesson_hook is not None and not callable(lesson_hook):
        raise ValueError("lesson_identifiable must be callable when declared")
    report["declarations"]["lesson_identifiable"] = lesson_hook is not None
    if not callable(getattr(module, "strict_canonical_like", None)):
        raise ValueError("strict_canonical_like is missing")

    applied = catalog.apply(TASK_ID, [p["input"] for p in pairs], timeout=args.timeout)
    (args.out / "canonical_apply.json").write_text(json.dumps(applied, indent=2) + "\n")
    if applied["executed_rule_hash"] != rule_hash or applied["generator_sha256"] != generator_hash:
        raise ValueError("Canonical application source identity differs")
    canonical = {"stored_pairs": len(pairs), "unique_pairs": len({digest(p) for p in pairs}),
                 "racket_matches": 0, "independent_oracle_matches": 0,
                 "shortcut_matches": dict.fromkeys(shortcuts, 0),
                 "competitor_matches": dict.fromkeys(competitors, 0), "features": []}
    for pair, executed in zip(pairs, applied["results"], strict=True):
        if executed.get("error") or executed.get("output") != pair["output"]:
            raise ValueError(f"Canonical Racket mismatch: {executed.get('error')}")
        canonical["racket_matches"] += 1
        if independent_oracle(pair["input"]) != pair["output"]:
            raise ValueError("Independent oracle failed a canonical pair")
        canonical["independent_oracle_matches"] += 1
        for name, functions, field in (("shortcut", shortcuts, "shortcut_matches"),
                                       ("competitor", competitors, "competitor_matches")):
            for rival_name, fn in functions.items():
                if call_rule(fn, pair["input"]) == pair["output"]:
                    canonical[field][rival_name] += 1
        for hook_name in ("self_check", "strict_canonical_like"):
            reasons = hook_reasons(getattr(module, hook_name), pair["input"])
            if reasons:
                raise ValueError(f"{hook_name} rejects canonical: {reasons}")
        canonical["features"].append(inspect_input(pair["input"])[2])
    for field in ("shortcut_matches", "competitor_matches"):
        if any(value != len(pairs) for value in canonical[field].values()):
            raise ValueError(f"A declared {field} rule does not fit all stored canonical pairs")
    report["canonical"] = canonical
    if args.short_lesson_probe:
        # This is a measured public-API limitation, not a failure of the promised
        # three-demo curriculum. Pick a core start from visible input features.
        short_start = next(si for si in range(args.sample_start, args.sample_start + 3)
                           if inspect_input(module.generate(args.seed, si, difficulty="medium"))[2]["dense_congruent"])
        short_episode = catalog.generate(TASK_ID, count=1, seed=args.seed,
            difficulty="medium", n_train=1, n_test=1, sample_index=short_start,
            allow_unapproved=True, reference="canonical", timeout=args.timeout)[0]
        if (short_episode["provenance"]["generator_sha256"] != generator_hash
                or short_episode["executed_rule_hash"] != rule_hash):
            raise ValueError("Short-lesson probe source identity differs")
        short_demos, short_query = short_episode["train"], short_episode["test"][0]
        short_survivors = []
        short_discriminates = []
        for name, fn in competitors.items():
            if all(call_rule(fn, pair["input"]) == pair["output"] for pair in short_demos):
                short_survivors.append(name)
                if call_rule(fn, short_query["input"]) != short_query["output"]:
                    short_discriminates.append(name)
        for pair in short_demos + [short_query]:
            if independent_oracle(pair["input"]) != pair["output"]:
                raise ValueError("Short lesson independent oracle disagrees with Racket")
        report["short_lesson_probe"] = {
            "scope": "Known limitation: public generation accepts a one-demo lesson even when finite rivals leave its query ambiguous. This is outside the generator's three-demo schedule guarantee.",
            "band": "medium", "seed": args.seed, "sample_start": short_start,
            "sample_indices": short_episode["sample_indices"], "public_generation_accepted": True,
            "rejections": short_episode.get("rejections", []),
            "surviving_competitors": short_survivors, "query_discriminates": short_discriminates,
            "lesson_hook_reasons": hook_reasons(lesson_hook, short_demos, short_query) if lesson_hook is not None else None,
            "racket_pair_occurrences": 2,
        }
        (args.out / "short_lesson.json").write_text(json.dumps(short_episode, indent=2) + "\n")
    starts = tuple(args.sample_start + offset for offset in range(3))
    report["plan"] = {
        "bands": list(BANDS), "seed_base": args.seed, "seed_last": args.seed + args.lessons - 1,
        "lessons_per_band_per_start": args.lessons, "starts": list(starts),
        "train_pairs": 3, "query_pairs": 2, "nonoverlapping_base_lessons": args.lessons * len(BANDS),
        "additional_overlapping_cyclic_windows": args.lessons * len(BANDS) * 2,
        "overlap_definition": "Base lessons use distinct (band, seed) values; additional starts reuse those seeds and overlap sample indices. Counts are observations, not independent random trials.",
        "output_authority": "Every generated pair is returned by public Catalog.generate using canonical Racket; no Python-generated labels.",
        "identifiability_scope": "Measured only against the actual declared finite competitor set; no claim of unique inference among every possible rule.",
    }
    seen_draws, seen_inputs, first_counterexamples = {}, {}, {}
    feature_counts = {band: Counter() for band in BANDS}
    witness_counts = {band: Counter() for band in BANDS}
    source_profiles = {band: Counter() for band in BANDS}
    competitor_counts = {band: {start: {name: Counter() for name in competitors} for start in starts} for band in BANDS}
    report["batches"] = []
    report["failures"] = []
    total_occurrences = 0
    total_rejections = 0
    with (args.out / "instances.jsonl").open("w") as instances_file, (args.out / "lessons.jsonl").open("w") as lessons_file:
        for band in BANDS:
            for start in starts:
                print(f"{TASK_ID}: {band} start={start}, {args.lessons} actual Racket lessons", file=sys.stderr, flush=True)
                if file_hash(selected) != generator_hash or file_hash(imported_source) != generator_hash:
                    raise ValueError("Generator changed during probe")
                episodes = catalog.generate(TASK_ID, count=args.lessons, seed=args.seed,
                    difficulty=band, n_train=3, n_test=2, sample_index=start,
                    allow_unapproved=True, reference="canonical", timeout=args.timeout)
                batch = {"band": band, "sample_start": start, "episodes": len(episodes),
                         "pair_occurrences": 0, "unique_draws_added": 0,
                         "rejections": 0, "lesson_query_checks": 0, "identifiable_queries": 0}
                for episode in episodes:
                    provenance = episode["provenance"]
                    if provenance["generator_sha256"] != generator_hash or episode["executed_rule_hash"] != rule_hash:
                        raise ValueError("Episode source identity differs from imported declarations")
                    if hashlib.sha256(episode["program"].encode()).hexdigest() != report["sources"]["rule_source_sha256"]:
                        raise ValueError("Episode executed different canonical source bytes")
                    indices = episode["sample_indices"]
                    ep_pairs = episode["train"] + episode["test"]
                    if len(episode["train"]) != 3 or len(episode["test"]) != 2 or len(indices) != 5:
                        raise ValueError("Lesson does not contain the requested 3 demos and 2 queries")
                    batch["rejections"] += len(episode.get("rejections", []))
                    total_rejections += len(episode.get("rejections", []))
                    if indices != list(range(start, start + 5)) or episode.get("rejections"):
                        report["failures"].append({"reason": "generation skipped draws", "band": band,
                            "seed": episode["seed"], "start": start, "indices": indices,
                            "rejections": episode.get("rejections")})
                    for si, pair in zip(indices, ep_pairs, strict=True):
                        batch["pair_occurrences"] += 1
                        total_occurrences += 1
                        key = (band, episode["seed"], si)
                        inp, output = pair["input"], pair["output"]
                        input_hash, output_hash = digest(inp), digest(output)
                        if independent_oracle(inp) != output:
                            raise ValueError(f"Independent oracle disagrees with Racket at {key}")
                        if key in seen_draws:
                            if seen_draws[key] != (input_hash, output_hash):
                                raise ValueError(f"Repeated draw was nondeterministic at {key}")
                            continue
                        replayed = module.generate(seed=episode["seed"], sample_index=si, difficulty=band)
                        if isinstance(replayed, dict):
                            replayed = replayed.get("input")
                        if replayed != inp:
                            raise ValueError(f"Imported generator replay differs from public generation at {key}")
                        seen_draws[key] = input_hash, output_hash
                        if input_hash in seen_inputs and seen_inputs[input_hash] != output_hash:
                            raise ValueError("Same input received different Racket outputs")
                        seen_inputs[input_hash] = output_hash
                        batch["unique_draws_added"] += 1
                        features = inspect_input(inp)[2]
                        if features["source_components"] != 1:
                            report["failures"].append({"reason": "disconnected source template", "draw": key})
                        counts = feature_counts[band]
                        counts["unique_draws"] += 1
                        for feature in ("dense_congruent", "canonical_exact_profile", "source_not_leftmost"):
                            counts[feature] += int(features[feature])
                        counts["template_has_holes"] += int(features["template_holes"] > 0)
                        counts["target_has_surplus"] += int(features["target_surplus_cells"] > 0)
                        counts["racket_retains_gray"] += int(any(v == 5 for row in output for v in row))
                        counts["strict_hook_accepts"] += int(not hook_reasons(module.strict_canonical_like, inp))
                        counts[f"grid_shape:{features['grid_shape']}"] += 1
                        counts[f"target_count:{features['target_count']}"] += 1
                        counts[f"template_palette_size:{len(features['template_palette'])}"] += 1
                        schedule = getattr(module, "schedule_profile", None)
                        if callable(schedule):
                            source_profiles[band][repr(schedule(episode["seed"], si, difficulty=band))] += 1
                        rule_outputs = {name: call_rule(fn, inp) for name, fn in rivals.items()}
                        for name, rival_out in rule_outputs.items():
                            if rival_out != output:
                                counts[f"refutes:{name}"] += 1
                                first_counterexamples.setdefault(name, {
                                    "band": band, "seed": episode["seed"], "sample_index": si,
                                    "generator_sha256": generator_hash, "rule_hash": rule_hash,
                                    "input": inp, "racket_output": output, "rival_output": rival_out,
                                    "rival_name": name, "function": getattr(rivals[name], "__name__", None),
                                    "input_sha256": input_hash, "output_sha256": output_hash,
                                    "features": features})
                        for name, predicate in witnesses.items():
                            copied = deepcopy(inp)
                            fired = predicate(copied)
                            if copied != inp or type(fired) is not bool:
                                raise ValueError(f"Witness {name} mutates input or does not return bool")
                            if fired:
                                witness_counts[band][name] += 1
                                claims = witness_rivals.get(name, [])
                                if claims and not any(rule_outputs[rival_name] != output for rival_name in claims):
                                    report["failures"].append({"reason": "false rival witness", "witness": name, "draw": key})
                        instances_file.write(json.dumps({"band": band, "seed": episode["seed"],
                            "sample_index": si, "input_sha256": input_hash, "output_sha256": output_hash,
                            "input": inp, "output": output}, separators=(",", ":")) + "\n")
                    scores = []
                    for query_index, query in enumerate(episode["test"]):
                        reasons = hook_reasons(lesson_hook, episode["train"], query) if lesson_hook is not None else None
                        batch["lesson_query_checks"] += 1
                        survivors, query_discriminates = [], []
                        for name, fn in competitors.items():
                            fits = all(call_rule(fn, pair["input"]) == pair["output"] for pair in episode["train"])
                            agrees = call_rule(fn, query["input"]) == query["output"]
                            status = "refuted_by_demos" if not fits else "survived_all" if agrees else "query_discriminates"
                            competitor_counts[band][start][name][status] += 1
                            if fits:
                                survivors.append(name)
                            if status == "query_discriminates":
                                query_discriminates.append(name)
                        batch["identifiable_queries"] += int(not reasons and not query_discriminates)
                        if reasons or query_discriminates:
                            report["failures"].append({"reason": "unidentified query under declared competitors",
                                "band": band, "seed": episode["seed"], "start": start,
                                "query_index": query_index, "hook_reasons": reasons,
                                "survivors": survivors, "query_discriminates": query_discriminates})
                        scores.append({"query_index": query_index, "hook_reasons": reasons,
                                       "survivors": survivors, "query_discriminates": query_discriminates})
                    lessons_file.write(json.dumps({"band": band, "seed": episode["seed"],
                        "sample_start": start, "base_nonoverlapping_lesson": start == starts[0],
                        "sample_indices": indices, "input_sha256": [digest(p["input"]) for p in ep_pairs],
                        "output_sha256": [digest(p["output"]) for p in ep_pairs], "queries": scores}, separators=(",", ":")) + "\n")
                report["batches"].append(batch)
                instances_file.flush()
                lessons_file.flush()
    report["census"] = {band: dict(sorted(counts.items())) for band, counts in feature_counts.items()}
    report["witness_counts"] = {band: dict(sorted(counts.items())) for band, counts in witness_counts.items()}
    report["schedule_profiles"] = {band: dict(sorted(counts.items())) for band, counts in source_profiles.items()}
    report["competitor_counts"] = {
        band: {str(start): {name: dict(counts) for name, counts in by_name.items()}
               for start, by_name in by_start.items()} for band, by_start in competitor_counts.items()}
    report["totals"] = {"pair_occurrences_racket_checked": total_occurrences,
        "unique_draw_tuples": len(seen_draws), "unique_input_grids": len(seen_inputs),
        "repeated_window_draw_occurrences": total_occurrences - len(seen_draws),
        "generation_rejections": total_rejections,
        "base_lesson_windows": args.lessons * len(BANDS),
        "additional_overlapping_windows": args.lessons * len(BANDS) * 2,
        "query_checks": sum(batch["lesson_query_checks"] for batch in report["batches"]),
        "independent_oracle_mismatches": 0,
        "first_counterexample_rivals": sorted(first_counterexamples)}
    missing = sorted(set(shortcuts) - set(first_counterexamples))
    if missing:
        report["failures"].append({"reason": "canonical shortcuts lack a generated counterexample", "rivals": missing})
    if file_hash(selected) != generator_hash or file_hash(imported_source) != generator_hash:
        raise ValueError("Source changed before final probe receipt")
    (args.out / "first_counterexamples.json").write_text(json.dumps(first_counterexamples, indent=2) + "\n")
    report["artifacts"] = {name: {"sha256": file_hash(args.out / name), "bytes": (args.out / name).stat().st_size}
                           for name in ("canonical_apply.json", "instances.jsonl", "lessons.jsonl", "first_counterexamples.json")}
    if args.short_lesson_probe:
        report["artifacts"]["short_lesson.json"] = {"sha256": file_hash(args.out / "short_lesson.json"),
                                                    "bytes": (args.out / "short_lesson.json").stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--runtime", type=Path, help="optional prepared runtime whose generator hash must match the selected source")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--lessons", type=int, default=100, help="nonoverlapping base lessons per band; two extra cyclic starts are also measured")
    parser.add_argument("--seed", type=int, default=140000)
    parser.add_argument("--sample-start", type=int, default=0)
    parser.add_argument("--short-lesson-probe", action="store_true", help="also retain a one-demo public lesson and measure any query ambiguity")
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    if args.lessons < 1 or args.sample_start < 0:
        parser.error("lessons must be positive and sample-start nonnegative")
    args.out = args.out.resolve()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("output directory must be new or empty")
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    report = {"schema": "b985d561c63b-distribution-probe-v1", "task_id": TASK_ID,
              "command": sys.argv, "working_directory": str(Path.cwd()), "status": "running"}
    try:
        run(args, report)
        report["status"] = "pass" if not report.get("failures") else "fail"
    except Exception as exc:
        report["status"] = "fail"
        report.setdefault("failures", []).append({"reason": "probe exception", "exception": f"{type(exc).__name__}: {exc}"})
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "sources", "totals", "failures", "elapsed_seconds") if key in report}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

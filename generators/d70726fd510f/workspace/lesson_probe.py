#!/usr/bin/env python3
"""Source-bound finite-rival diagnostics; Python outputs are never Racket labels.

Example (checkout): python generators/d70726fd510f/workspace/lesson_probe.py
  --lessons-per-band 100 --seed 0 --out /tmp/lessons.json
For a baseline lacking declarations, explicitly supply --competitor-file generator.py.
The optional --racket-parity route uses only the public Catalog.apply API.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

TASK_ID = "d70726fd510f"
BANDS = ("easy", "medium", "hard")
XOR_TABLE = 6  # bit index = 2 * left_nonzero + right_nonzero: 00,01,10,11


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid) -> str:
    return sha256(json.dumps(grid, separators=(",", ":")).encode())


def bootstrap(generator_file: Path, runtime_root: Path | None = None):
    """Find the checkout or a prepare_runtime portable tree without private APIs."""
    starts = [generator_file.resolve().parent, Path(__file__).resolve().parent]
    if runtime_root:
        starts.insert(0, runtime_root.resolve())
    tried = []
    for start in starts:
        for ancestor in (start, *start.parents):
            for candidate in (ancestor, ancestor / "shared/runtime", ancestor / "runtime"):
                if candidate in tried:
                    continue
                tried.append(candidate)
                if (candidate / "puzzle_generators/base.py").is_file():
                    sys.path.insert(0, str(candidate))
                    for library in (ancestor, *ancestor.parents):
                        if (library / "src/arcpuzzles/catalog.py").is_file():
                            sys.path.insert(0, str(library / "src"))
                            return candidate, library
                    return candidate, None
    raise FileNotFoundError("Cannot locate puzzle_generators runtime; pass --runtime-root")


def load_generator(path: Path, runtime_root: Path | None = None) -> ModuleType:
    bootstrap(path, runtime_root)
    source = path.read_bytes()
    name = "lesson_probe_generator_" + sha256(source)[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    module.__lesson_probe_source_sha256__ = sha256(source)
    return module


def validate_grid(grid):
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) or not row for row in grid):
        raise ValueError("expected nonempty list of rows")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if width < 3 or width % 2 != 1:
        raise ValueError("expected equal panels with a middle separator")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("expected integer colors 0..9")
    middle = width // 2
    if any(row[middle] != 4 for row in grid):
        raise ValueError("missing middle color-4 separator")
    if any(cell == 4 for row in grid for c, cell in enumerate(row) if c != middle):
        raise ValueError("separator color appears in a panel")
    return len(grid), middle


def occupancy_states(grid):
    _, width = validate_grid(grid)
    return [2 * int(row[c] != 0) + int(row[width + 1 + c] != 0)
            for row in grid for c in range(width)]


def boolean_output(grid, table: int):
    """Independently evaluate all16 occupancy truth tables, including XOR6."""
    if type(table) is not int or not 0 <= table < 16:
        raise ValueError("table must be an integer0..15")
    _, width = validate_grid(grid)
    return [[2 * ((table >> (2 * int(row[c] != 0) + int(row[width + 1 + c] != 0))) & 1)
             for c in range(width)] for row in grid]


def declarations(module, attribute):
    value = getattr(module, attribute, None)
    if not isinstance(value, dict) or any(not isinstance(k, str) or not callable(v) for k, v in value.items()):
        raise ValueError(f"{attribute} must be the generator's dict[str, callable]")
    return value


def evaluate(function, grid):
    try:
        # A rival must not be able to mutate the shared input used by other rivals.
        return function([row[:] for row in grid]), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def authority(canonical_file: Path):
    rows = []
    for line in canonical_file.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    if not rows:
        raise ValueError(f"No canonical record for {TASK_ID}")
    fingerprints = {sha256(json.dumps({key: row.get(key) for key in ("train", "test", "program_solution")},
                                     sort_keys=True, separators=(",", ":")).encode()) for row in rows}
    if len(fingerprints) != 1:
        raise ValueError("Conflicting canonical records require explicit resolution")
    row = rows[0]
    pairs = [{"split": split, "index": i, **pair}
             for split in ("train", "test") for i, pair in enumerate(row.get(split, []))]
    rule = row["program_solution"]
    return pairs, {"canonical_file_sha256": sha256(canonical_file.read_bytes()),
                   "canonical_record_sha256": next(iter(fingerprints)),
                   "rule_text_sha256": sha256(rule.encode()),
                   "rule_normalized_sha256": sha256(" ".join(rule.split()).encode()),
                   "pair_count": len(pairs)}


def canonical_checks(shortcuts, pairs):
    result = {}
    for name, function in shortcuts.items():
        rows = []
        for pair in pairs:
            predicted, error = evaluate(function, pair["input"])
            rows.append({"split": pair["split"], "index": pair["index"],
                         "fits": error is None and predicted == pair["output"], "error": error})
        result[name] = {"fits_all": all(row["fits"] for row in rows), "pairs": rows}
    return result


def inspect_lesson(grids, competitors):
    outputs = [boolean_output(grid, XOR_TABLE) for grid in grids]
    truth_survivors = [table for table in range(16)
                       if all(boolean_output(grid, table) == output for grid, output in zip(grids[:3], outputs[:3]))]
    boolean_query_wrong = [table for table in truth_survivors
                           if boolean_output(grids[3], table) != outputs[3]]
    surviving, query_wrong, errors = [], [], {}
    rejected = {}
    for name, function in competitors.items():
        predictions = [evaluate(function, grid) for grid in grids]
        err = [error for _, error in predictions if error]
        if err:
            errors[name] = err[0]
        rejection = next((i for i, ((predicted, error), output) in enumerate(zip(predictions[:3], outputs[:3]))
                          if error is not None or predicted != output), None)
        if rejection is None:
            surviving.append(name)
            if predictions[3][1] or predictions[3][0] != outputs[3]:
                query_wrong.append(name)
        else:
            rejected[name] = rejection
    return {"boolean_survivors": truth_survivors,
            "boolean_query_disagreeing_survivors": boolean_query_wrong, "declaration_survivors": surviving,
            "query_disagreeing_survivors": query_wrong, "declaration_errors": errors,
            "first_rejection_demo": rejected}, outputs


def compact_witness(seed, indices, band, grids, inspection, outputs):
    return {"seed": seed, "sample_indices": indices, "difficulty": band,
            "demonstrations": [{"input": grid, "python_xor_output": output}
                               for grid, output in zip(grids[:3], outputs[:3])],
            "query": {"input": grids[3], "python_xor_output": outputs[3]},
            **inspection}


def measure(module, competitors, shortcuts, *, lessons_per_band=100, seed=0,
            sample_index=0, overlap_windows=100, schedule_cycle=None):
    if lessons_per_band < 1 or overlap_windows < 0:
        raise ValueError("positive lessons_per_band and nonnegative overlap_windows required")
    profiles = tuple(getattr(module, "SCHEDULE_PROFILES", ()))
    cycle = schedule_cycle if schedule_cycle is not None else (len(profiles) or 2)
    if cycle < 1:
        raise ValueError("empty SCHEDULE_PROFILES")
    unique = {mode: {key: set() for key in ("inputs", "outputs", "pairs", "lessons")}
              for mode in ("independent", "overlapping", "all")}
    result = {"independent_lessons_per_band": lessons_per_band,
              "overlapping_windows_per_band": overlap_windows,
              "schedule_cycle_length": cycle, "generator_declared_schedule_profiles": list(profiles),
              "schedule_cycle_source": "explicit diagnostic indexing cycle" if schedule_cycle is not None
              else "generator declaration" if profiles else "diagnostic fallback (not a baseline-native schedule)",
              "bands": {}, "first_genuine_ambiguous_lesson": None,
              "first_surviving_rival_lesson": None, "first_failures": {}}
    for band in BANDS:
        band_result = {"independent": {}, "overlapping": {}}
        result["bands"][band] = band_result
        for mode, count in (("independent", lessons_per_band), ("overlapping", overlap_windows)):
            stats = {"lesson_count": 0, "input_appearances": 0, "output_appearances": 0,
                     "schedule_starts": dict.fromkeys(map(str, range(cycle)), 0),
                     "seeds_and_sample_indices": [], "failures": Counter(),
                     "declaration_survival_counts": Counter(dict.fromkeys(competitors, 0)),
                     "query_disagreement_counts": Counter(dict.fromkeys(competitors, 0)),
                     "boolean_survival_counts": Counter(dict.fromkeys(map(str, range(16)), 0)),
                     "boolean_query_disagreement_counts": Counter(dict.fromkeys(map(str, range(16)), 0)), "first_rejections": {}}
            inputs_seen, outputs_seen, pair_seen, lessons_seen = set(), set(), set(), set()
            for number in range(count):
                current_seed = seed + number if mode == "independent" else seed + lessons_per_band
                start = sample_index + number % cycle if mode == "independent" else sample_index + number
                indices = list(range(start, start + 4))
                stats["seeds_and_sample_indices"].append({"seed": current_seed, "sample_indices": indices})
                stats["schedule_starts"][str(start % cycle)] += 1
                try:
                    grids = [module.generate(current_seed, index, difficulty=band) for index in indices]
                    inspection, outputs = inspect_lesson(grids, competitors)
                except Exception as exc:
                    stats["failures"]["generation_or_python_rule_error"] += 1
                    result["first_failures"].setdefault("generation_or_python_rule_error", {
                        "band": band, "mode": mode, "seed": current_seed, "sample_indices": indices,
                        "error": f"{type(exc).__name__}: {exc}"})
                    continue
                stats["lesson_count"] += 1
                stats["input_appearances"] += 4
                stats["output_appearances"] += 4
                input_keys = [grid_hash(g) for g in grids]
                output_keys = [grid_hash(g) for g in outputs]
                inputs_seen.update(input_keys); outputs_seen.update(output_keys)
                pair_seen.update(zip(input_keys, output_keys)); lessons_seen.add(tuple(input_keys))
                for union_mode in (mode, "all"):
                    unique[union_mode]["inputs"].update(input_keys)
                    unique[union_mode]["outputs"].update(output_keys)
                    unique[union_mode]["pairs"].update(zip(input_keys, output_keys))
                    unique[union_mode]["lessons"].add(tuple(input_keys))
                for key, value in (("declaration_survival_counts", inspection["declaration_survivors"]),
                                   ("query_disagreement_counts", inspection["query_disagreeing_survivors"]),
                                   ("boolean_survival_counts", map(str, inspection["boolean_survivors"])),
                                   ("boolean_query_disagreement_counts", map(str, inspection["boolean_query_disagreeing_survivors"]))):
                    stats[key].update(value)
                issues = []
                for index, grid in zip(indices, grids):
                    try:
                        check = module.self_check(grid, difficulty=band)
                    except Exception as exc:
                        check = [f"self_check raised {type(exc).__name__}: {exc}"]
                    if check:
                        issues.append({"sample_index": index, "issues": check})
                checks = {"self_check_rejection": bool(issues),
                          "missing_occupancy_state": any(set(occupancy_states(g)) != {0, 1, 2, 3} for g in grids),
                          "boolean_ambiguity": inspection["boolean_survivors"] != [XOR_TABLE],
                          "declared_competitor_survival": bool(inspection["declaration_survivors"]),
                          "genuine_query_ambiguity": bool(inspection["query_disagreeing_survivors"] or inspection["boolean_query_disagreeing_survivors"]),
                          "competitor_exception": bool(inspection["declaration_errors"])}
                for name, failed in checks.items():
                    if failed:
                        stats["failures"][name] += 1
                        if name not in result["first_failures"]:
                            result["first_failures"][name] = compact_witness(current_seed, indices, band, grids, inspection, outputs)
                            if issues:
                                result["first_failures"][name]["self_check_issues"] = issues
                for name, demo in inspection["first_rejection_demo"].items():
                    stats["first_rejections"].setdefault(name, {"seed": current_seed, "sample_index": indices[demo],
                        "input": grids[demo], "python_xor_output": outputs[demo],
                        "rival_output": evaluate(competitors[name], grids[demo])[0],
                        "rival_error": evaluate(competitors[name], grids[demo])[1]})
                if inspection["declaration_survivors"] and result["first_surviving_rival_lesson"] is None:
                    result["first_surviving_rival_lesson"] = compact_witness(current_seed, indices, band, grids, inspection, outputs)
                if (inspection["query_disagreeing_survivors"] or inspection["boolean_query_disagreeing_survivors"]) and result["first_genuine_ambiguous_lesson"] is None:
                    result["first_genuine_ambiguous_lesson"] = compact_witness(current_seed, indices, band, grids, inspection, outputs)
            stats.update(distinct_inputs=len(inputs_seen), distinct_outputs=len(outputs_seen),
                         distinct_input_output_pairs=len(pair_seen), distinct_lessons=len(lessons_seen))
            band_result[mode] = stats
    result["global_union_counts"] = {mode: {"distinct_" + key: len(values) for key, values in sets.items()}
                                    for mode, sets in unique.items()}
    return result


def parity_matrix(module, seed):
    """Bounded matrix: all64 ordered allowed foreground pairs, plus edge/default/texture cases."""
    cases = []
    colors = tuple(c for c in range(1, 10) if c != 4)
    # 2 is a lawful foreground: nonzero occupancy remains the input distinction.
    for left in colors:
        for right in colors:
            grid = [[0, 0, left, left, 4, 0, right, 0, right]]
            cases.append({"kind": "ordered_foreground_pair", "left": left, "right": right, "input": grid})
    for h, pw in ((1, 1), (1, 14), (18, 1), (18, 14)):
        for table_state in range(4):
            left, right = (1 if table_state & 2 else 0), (3 if table_state & 1 else 0)
            cases.append({"kind": "dimension_and_occupancy_edge", "height": h, "panel_width": pw,
                          "state": table_state, "input": [[left] * pw + [4] + [right] * pw for _ in range(h)]})
    for band in (None, *BANDS):
        cases.append({"kind": "default", "difficulty": band,
                      "input": module.generate(seed, 0, difficulty=band)})
    textures = tuple(dict.fromkeys((*getattr(module, "PANEL_PATTERNS", ()),
                                   *getattr(module, "DEGENERATE_TEXTURES", ()))))
    for texture in textures:
        cases.append({"kind": "texture", "texture": texture,
                      "input": module.generate(seed, 0, texture=texture)})
    return cases


def racket_parity(module, library_root, *, seed, expected_rule_normalized_sha256, canonical_pairs=(), expected_generator_sha256=None):
    """Public supported application; no runner/bridge private functions."""
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import MAX_APPLY_INPUTS
    cases = parity_matrix(module, seed)
    cases.extend({"kind": "canonical", "split": pair["split"], "index": pair["index"],
                  "input": pair["input"], "canonical_output": pair["output"]} for pair in canonical_pairs)
    applications, applied_results = [], []
    catalog = Catalog(library_root)
    for start in range(0, len(cases), MAX_APPLY_INPUTS):
        application = catalog.apply(TASK_ID, [case["input"] for case in cases[start:start + MAX_APPLY_INPUTS]], timeout=180)
        if application["executed_rule_hash"] != expected_rule_normalized_sha256[:12] or not application["rule_hash_matches_catalog"]:
            raise ValueError("executed Racket rule does not match this probe's canonical authority")
        if expected_generator_sha256 is not None and application["generator_sha256"] != expected_generator_sha256:
            raise ValueError("public Racket application staged different generator bytes")
        applications.append({k: v for k, v in application.items() if k != "results"})
        applied_results.extend(application["results"])
    rows = []
    for case, result in zip(cases, applied_results, strict=True):
        expected = boolean_output(case["input"], XOR_TABLE)
        rows.append({**case, "python_xor_output": expected, "racket_output": result["output"],
                     "error": result["error"], "matches": result["error"] is None and result["output"] == expected
                     and ("canonical_output" not in case or result["output"] == case["canonical_output"])})
    return {"route": "public Catalog.apply", "matrix_count": len(rows), "all_match": all(r["matches"] for r in rows),
            "application_provenance": applications, "cases": rows}



def diagnostic_gate(report, *, require_rival_refutation=False):
    """A finite measured gate; it does not change catalog approval."""
    problems = []
    if not report["canonical_python_xor_matches"]:
        problems.append({"kind": "canonical_python_mismatch"})
    for name, value in report["canonical_shortcuts"].items():
        if not value["fits_all"]:
            problems.append({"kind": "false_canonical_shortcut_claim", "name": name})
    required_zero = {"generation_or_python_rule_error", "self_check_rejection", "competitor_exception", "genuine_query_ambiguity"}
    if require_rival_refutation:
        required_zero.add("declared_competitor_survival")
    for band, modes in report["lessons"]["bands"].items():
        for mode, values in modes.items():
            for name in sorted(required_zero):
                count = values["failures"].get(name, 0)
                if count:
                    problems.append({"kind": name, "band": band, "mode": mode, "count": count})
    if "racket_parity" in report and not report["racket_parity"].get("all_match", False):
        problems.append({"kind": "racket_parity_failure", "error": report["racket_parity"].get("error")})
    return {"status": "FAIL" if problems else "PASS", "require_rival_refutation": require_rival_refutation,
            "policy": "reject false canonical claims, canonical Python mismatches, generation/input-validation/self-check errors, competitor exceptions, genuine surviving-rival query disagreements, and requested Racket parity failures; demonstration survival alone is rejected only under strict rival refutation",
            "problems": problems}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator-file", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--competitor-file", type=Path, help="declaration source when inspecting an older baseline")
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--canonical-file", type=Path)
    parser.add_argument("--library-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--overlap-windows", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--schedule-cycle", type=int, help="explicit diagnostic start cycle for comparable baseline/final tuples")
    parser.add_argument("--racket-parity", action="store_true")
    parser.add_argument("--require-pass", action="store_true", help="exit2 if the documented finite diagnostic gate fails")
    parser.add_argument("--require-rival-refutation", action="store_true", help="also require all declared rivals rejected by demonstrations; implies --require-pass")
    args = parser.parse_args(argv)
    runtime, library = bootstrap(args.generator_file, args.runtime_root)
    library = args.library_root.resolve() if args.library_root else library
    if library is not None and (library / "src/arcpuzzles").is_dir():
        sys.path.insert(0, str(library / "src"))
    canonical_file = args.canonical_file or ((library / "shared/data/canonical/puzzles.jsonl") if library else runtime / "data/canonical/puzzles.jsonl")
    module = load_generator(args.generator_file, args.runtime_root)
    competitor_file = args.competitor_file or args.generator_file
    rival_module = module if competitor_file.resolve() == args.generator_file.resolve() else load_generator(competitor_file, args.runtime_root)
    competitors = declarations(rival_module, "LESSON_COMPETITORS")
    shortcuts = declarations(rival_module, "CANONICAL_SHORTCUTS")
    pairs, rule_provenance = authority(canonical_file)
    report = {"schema": "source-bound-lesson-diagnostic-v1", "task_id": TASK_ID,
              "label_authority": "independent Python occupancy XOR; only racket_parity carries executed Racket outputs",
              "finite_rival_scope": "all16 independent occupancy tables plus actual source-declared LESSON_COMPETITORS",
              "provenance": {"generator_file": str(args.generator_file.resolve()),
                             "generator_sha256": module.__lesson_probe_source_sha256__,
                             "tool_file": str(Path(__file__).resolve()), "tool_sha256": sha256(Path(__file__).read_bytes()),
                             "competitor_file": str(competitor_file.resolve()), "competitor_source_sha256": rival_module.__lesson_probe_source_sha256__,
                             "generator_version": getattr(module, "VERSION", None), "seed": args.seed,
                             "sample_index": args.sample_index, **rule_provenance},
              "declared_competitors": list(competitors), "declared_canonical_shortcuts": list(shortcuts),
              "canonical_python_xor_matches": all(boolean_output(p["input"], XOR_TABLE) == p["output"] for p in pairs),
              "canonical_shortcuts": canonical_checks(shortcuts, pairs)}
    report["lessons"] = measure(module, competitors, shortcuts, lessons_per_band=args.lessons_per_band,
                                  seed=args.seed, sample_index=args.sample_index, overlap_windows=args.overlap_windows, schedule_cycle=args.schedule_cycle)
    if args.racket_parity:
        if library is None:
            parser.error("--racket-parity needs the source library (--library-root)")
        try:
            report["racket_parity"] = racket_parity(module, library, seed=args.seed, expected_rule_normalized_sha256=rule_provenance["rule_normalized_sha256"], canonical_pairs=pairs, expected_generator_sha256=module.__lesson_probe_source_sha256__)
        except Exception as exc:
            report["racket_parity"] = {"route": "public Catalog.apply", "all_match": False, "error": f"{type(exc).__name__}: {exc}"}
    report["measurement_completed"] = True
    report["diagnostic_gate"] = diagnostic_gate(report, require_rival_refutation=args.require_rival_refutation)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "generator_sha256": report["provenance"]["generator_sha256"],
                      "canonical_shortcuts_fit": all(v["fits_all"] for v in report["canonical_shortcuts"].values()),
                      "diagnostic_gate": report["diagnostic_gate"]["status"],
                      "failures": {band: {mode: dict(stats["failures"]) for mode, stats in values.items()}
                                   for band, values in report["lessons"]["bands"].items()}}, indent=2))
    return 2 if (args.require_pass or args.require_rival_refutation) and report["diagnostic_gate"]["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

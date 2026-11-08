"""Extract compact, source-bound semantic evidence from a completed public census.

No new lesson sampling or private runner API is used. Predictions are evaluated
from the selected module's actual mappings; expected labels stay Racket-derived.
Run through run_with_racket.py from the packet root. See the command manifest.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

sys.dont_write_bytecode = True
TASK_ID = "547c45a21db1"
NAMESPACES = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    if path.exists():
        raise FileExistsError(f"Use a new evidence path: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def load_generator():
    path = Path(__file__).resolve().parents[2] / "generator.py"
    spec = importlib.util.spec_from_file_location("reviewed_task_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return path, module


def input_profile(grid):
    return (len(grid), len(grid[0]), tuple(sorted({v for row in grid for v in row})))


def pair_profile(pair):
    return input_profile(pair["input"]), input_profile(pair["output"])


def differences(predicted, actual):
    return [[r, c, predicted[r][c], actual[r][c]] for r in range(len(actual))
            for c in range(len(actual[0])) if predicted[r][c] != actual[r][c]]


def path_order(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (1, 2, 3)}
    point = next(p for p in cells if grid[p[0]][p[1]] == 2)
    path, previous = [], None
    while point is not None:
        path.append(point)
        onward = [(point[0]+dr, point[1]+dc) for dr, dc in ((1,0),(-1,0),(0,1),(0,-1))
                  if (point[0]+dr, point[1]+dc) in cells and (point[0]+dr, point[1]+dc) != previous]
        assert len(onward) <= 1 and len(path) <= len(cells)
        previous, point = point, onward[0] if onward else None
    assert len(path) == len(cells)
    return path


def extract(args):
    source, module = load_generator()
    source_hash = file_hash(source)
    assert source_hash == args.expected_generator_hash
    census = json.loads(args.census.read_text())
    assert census["generator_sha256"] == source_hash
    assert census["status"] == "no_ambiguity_found", census["status"]
    assert census["summary"]["requested"] == census["summary"]["materialized"]
    assert not census["errors"]
    assert module.RULE_HASH == census["declared_rule_hash"] == census["rule_source_sha256"][:12]
    mappings = {namespace: getattr(module, namespace) for namespace in NAMESPACES}
    assert all(isinstance(mapping, dict) and mapping for mapping in mappings.values())
    declarations = {f"{namespace}:{name}": fn for namespace, mapping in mappings.items() for name, fn in mapping.items()}
    assert all(callable(fn) for fn in declarations.values())
    assert set(declarations) == set(census["rivals"])
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    canonical_fit = {}
    for name, fn in declarations.items():
        cases = [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"],
                  "differences": differences(fn(deepcopy(p["input"])), p["output"])} for p in canonical]
        fits = sum(not case["differences"] for case in cases)
        assert fits == census["canonical_rival_fit"][name]["fits"]
        canonical_fit[name] = {"fits": fits, "pairs": len(cases), "cases": cases}
        if name.startswith("CANONICAL_SHORTCUTS:"):
            assert fits == len(cases)
    canonical_validation = [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"],
                             "self_check": module.self_check(p["input"]),
                             "strict_check": module.strict_canonical_like(p["input"]),
                             "observed": module.observe_overrides(p["input"])} for p in canonical]
    assert all(not p["self_check"] and not p["strict_check"] for p in canonical_validation)
    canonical_inputs = {input_profile(p["input"]) for p in canonical}
    canonical_io = {pair_profile(p) for p in canonical}
    witnesses = getattr(module, "SEMANTIC_WITNESSES")
    witness_rivals = getattr(module, "WITNESS_RIVALS")
    assert set(witnesses) == set(witness_rivals)
    lesson_rivals = mappings["LESSON_COMPETITORS"]
    assert all(set(names) <= set(lesson_rivals) for names in witness_rivals.values())
    predicted, observed_labels, selected = {}, {}, {}
    band_counts, cycle_examples = defaultdict(Counter), {}
    witness_counts = defaultdict(Counter)
    lesson_support, production_counts, rotation_counts = [], Counter(), Counter()
    accepted_schedule_exceptions = []
    min_rotated_refutations = {name: None for name in lesson_rivals}
    period = len(module.SCHEDULE_PROFILES)

    def predict(fn, pair):
        key = id(fn), digest(pair["input"])
        if key not in predicted:
            predicted[key] = fn(deepcopy(pair["input"]))
        return predicted[key]

    def score(pairs, train_indices, query_indices):
        return {name: ("refuted" if any(predict(fn, pairs[i]) != pairs[i]["output"] for i in train_indices)
                       else "ambiguous" if any(predict(fn, pairs[i]) != pairs[i]["output"] for i in query_indices)
                       else "survived_all") for name, fn in declarations.items()}

    for lesson in census["lessons"]:
        band, seed = lesson["band"], lesson["seed"]
        instance = lesson["instance"]
        sampling = instance["sampling"]
        pairs = instance["train"] + instance["test"]
        accepted = sampling["accepted_pairs"]
        assert len(accepted) == len(pairs)
        metadata = {(p["split"], p["pair_index"]): p for p in accepted}
        support = Counter()
        geometry = []
        for position, pair in enumerate(pairs):
            split = "train" if position < len(instance["train"]) else "test"
            pair_index = position if split == "train" else position - len(instance["train"])
            accepted_pair = metadata[(split, pair_index)]
            index, grid = accepted_pair["sample_index"], pair["input"]
            input_hash = digest(grid)
            assert input_hash == accepted_pair["input_sha256"]
            assert not module.self_check(grid) and not module.strict_canonical_like(grid)
            assert observed_labels.setdefault(input_hash, pair["output"]) == pair["output"]
            profile = module.schedule_profile(seed, index, band)
            axes = module.observe_overrides(grid)
            band_counts[band]["pairs"] += 1
            band_counts[band]["canonical_input_profile_hits"] += input_profile(grid) in canonical_inputs
            band_counts[band]["canonical_input_output_profile_hits"] += pair_profile(pair) in canonical_io
            band_counts[band][f"schedule:{profile}"] += 1
            band_counts[band][f"length:{axes['path_len']}"] += 1
            hits = [name for name, fn in witnesses.items() if fn(deepcopy(grid))]
            refuted = [name for name, fn in lesson_rivals.items() if predict(fn, pair) != pair["output"]]
            for witness_name in hits:
                assert set(witness_rivals[witness_name]) <= set(refuted)
                support[witness_name] += 1
                witness_counts[band][witness_name] += 1
                candidate = {"declared_witness": witness_name, "band": band, "lesson_index": lesson["index"],
                             "seed": seed, "requested_start": lesson["sample_index"], "actual_sample_index": index,
                             "split": split, "pair_index": pair_index, "pair_position": position,
                             "instance_sha256": lesson["instance_sha256"], "input_sha256": input_hash,
                             "output_sha256": digest(pair["output"]), "schedule_profile": profile, "observed_axes": axes,
                             "input": grid, "racket_output": pair["output"], "refuted_lesson_competitors": refuted,
                             "required_rivals": witness_rivals[witness_name]}
                rank = (len(grid)*len(grid[0]), axes["path_len"], lesson["index"], position, input_hash)
                if witness_name not in selected or rank < selected[witness_name][0]:
                    selected[witness_name] = rank, candidate
            route = path_order(grid)
            reconstructed = [[0]*len(grid[0]) for _ in grid]
            for r, c in route:
                reconstructed[r][c] = 1
            reconstructed[route[0][0]][route[0][1]] = 2
            reconstructed[route[-1][0]][route[-1][1]] = 3
            assert reconstructed == grid
            geometry.append({"position": position, "split": split, "pair_index": pair_index,
                             "actual_sample_index": index, "schedule_profile": profile, "input_sha256": input_hash,
                             "output_sha256": digest(pair["output"]), "shape": [len(grid), len(grid[0])],
                             "path_from_seed2_to_seed3": route,
                             "racket_colors_along_path": [pair["output"][r][c] for r, c in route],
                             "witnesses": hits, "refuted_lesson_competitors": refuted})
        cycle_key = band, lesson["sample_index"] % period
        cycle_examples.setdefault(cycle_key, {"band": band, "requested_start_residue": cycle_key[1],
            "seed": seed, "requested_start": lesson["sample_index"], "lesson_index": lesson["index"],
            "instance_sha256": lesson["instance_sha256"], "sampling": sampling, "pairs": geometry})
        production = score(pairs, range(len(instance["train"])), range(len(instance["train"]), len(pairs)))
        assert production == lesson["rivals"]
        production_counts.update(production.values())
        for rotation in lesson["rotations"]:
            status = score(pairs, rotation["train_indices"], [rotation["query_index"]])
            assert status == rotation["rivals"]
            rotation_counts.update(status.values())
        for name in lesson_rivals:
            refuting_pairs = sum(name in pair["refuted_lesson_competitors"] for pair in geometry)
            minimum = max(refuting_pairs - 1, 0)
            previous = min_rotated_refutations[name]
            min_rotated_refutations[name] = minimum if previous is None else min(previous, minimum)
        if sampling["rejections"] or any(support[name] < 2 for name in witnesses):
            accepted_schedule_exceptions.append({"band": band, "seed": seed, "lesson_index": lesson["index"],
                "requested_start": lesson["sample_index"], "instance_sha256": lesson["instance_sha256"],
                "sampling": sampling, "witness_counts": dict(support), "pairs": geometry,
                "production_rivals": production, "rotation_rivals": [rotation["rivals"] for rotation in lesson["rotations"]]})
        lesson_support.append({"band": band, "index": lesson["index"], "seed": seed,
                               "requested_start": lesson["sample_index"],
                               "actual_indices": [p["sample_index"] for p in accepted],
                               "witness_counts": dict(support), "rejections": sampling["rejections"]})
    assert len(observed_labels) == census["summary"]["unique_inputs"]
    assert len(selected) == len(witnesses)
    exported = []
    for name in witnesses:
        item = selected[name][1]
        regenerated = module.generate(item["seed"], item["actual_sample_index"], difficulty=item["band"])
        assert regenerated == item["input"]
        item["generate_replay_matches"] = True
        pair = {"input": item["input"], "output": item["racket_output"]}
        item["lesson_competitor_predictions"] = {rival_name: {
            "output": predict(fn, pair), "differences": differences(predict(fn, pair), pair["output"])
        } for rival_name, fn in lesson_rivals.items()}
        exported.append(item)
    assert set().union(*(set(w["refuted_lesson_competitors"]) for w in exported)) == set(lesson_rivals)
    assert file_hash(source) == source_hash, "Generator changed while extracting evidence"
    output_dir = args.out.parent
    write_json(output_dir / "witnesses.json", {"generator_sha256": source_hash,
        "rule_source_sha256": census["rule_source_sha256"], "census_sha256": file_hash(args.census), "witnesses": exported})
    write_json(output_dir / "witness_inputs.json", [w["input"] for w in exported])
    write_json(output_dir / "cycle_examples.json", {"generator_sha256": source_hash, "period": period,
        "geometry_encoding": "Shape plus occupied path from seed2 to seed3 exactly reconstructs each input; unspecified cells are0. Output colors are retained along that path.",
        "examples": list(cycle_examples.values())})
    write_json(output_dir / "accepted_schedule_exceptions.json", {"generator_sha256": source_hash,
        "census_sha256": file_hash(args.census), "exceptions": accepted_schedule_exceptions})
    report = {
        "schema": "547c45a21db1-final-semantic-extraction-v1", "phase": "final", "task_id": TASK_ID,
        "generator_version": module.VERSION, "generator_sha256": source_hash,
        "rule_source_sha256": census["rule_source_sha256"], "rule_callable_sha256": census["rule_callable_sha256"],
        "declared_rule_hash": module.RULE_HASH, "probe_sha256": file_hash(Path(__file__)),
        "census_path": str(args.census), "census_sha256": file_hash(args.census), "census_status": census["status"],
        "census_summary": census["summary"], "sampler": census["sampler"],
        "declarations": {namespace: list(mapping) for namespace, mapping in mappings.items()},
        "declaration_count": len(declarations), "distinct_lesson_competitors": len(lesson_rivals),
        "canonical_fit": canonical_fit, "canonical_validation": canonical_validation,
        "canonical_shortcut_checks": len(mappings["CANONICAL_SHORTCUTS"]) * len(canonical),
        "recomputed_status_counts": {"production": production_counts, "rotations": rotation_counts},
        "per_band_profile_counts": dict(band_counts), "per_band_witness_counts": dict(witness_counts),
        "minimum_witnesses_per_materialized_lesson": {name: min(item["witness_counts"].get(name, 0) for item in lesson_support) for name in witnesses},
        "minimum_witnesses_after_any_one_query_holdout": {name: min(item["witness_counts"].get(name, 0)-1 for item in lesson_support) for name in witnesses},
        "minimum_refuting_demonstrations_after_any_one_query_holdout": min_rotated_refutations,
        "lessons_with_rejections": sum(bool(item["rejections"]) for item in lesson_support),
        "accepted_index_ranges": {band: [min(i for item in lesson_support if item["band"] == band for i in item["actual_indices"]),
                                         max(i for item in lesson_support if item["band"] == band for i in item["actual_indices"])] for band in band_counts},
        "lesson_index_ranges": {band: [min(item["index"] for item in lesson_support if item["band"] == band),
                                        max(item["index"] for item in lesson_support if item["band"] == band)] for band in band_counts},
        "witness_artifact": "witnesses.json", "cycle_artifact": "cycle_examples.json",
        "accepted_schedule_exception_artifact": "accepted_schedule_exceptions.json",
        "witness_summary": [{key: value for key, value in w.items() if key not in ("input", "racket_output", "lesson_competitor_predictions")} for w in exported],
        "limits": ["Reuses the completed census's Racket labels; it does not run a new sampling census.",
                   "The29 namespace-qualified declarations include aliases of11 competitor rules; they are not29 independent hypotheses.",
                   "Finite declared-rival evidence does not establish universal identifiability or eliminate undeclared conditional shortcuts.",
                   "The inspected default policy has five demonstrations and one query; exact overrides can suppress the witness schedule.",
                   "Profile counts are explicitly input and input/output shape-palette matches over existing census pairs, not a replacement profile-floor gate.",
                   "Representative cycle geometry covers every requested residue in each band; the300 source lessons are not an exhaustive enumeration of seeds or cyclic windows."],
    }
    write_json(args.out, report)
    print(json.dumps({"out": str(args.out), "generator_sha256": source_hash,
                      "canonical_shortcut_checks": report["canonical_shortcut_checks"], "census_summary": census["summary"],
                      "minimum_witnesses": report["minimum_witnesses_per_materialized_lesson"],
                      "selected_witnesses": [(w["declared_witness"], w["seed"], w["actual_sample_index"], w["observed_axes"]) for w in exported]}, indent=2))


def verify_apply(args):
    report = json.loads(args.report.read_text())
    selected = json.loads((args.report.parent / report["witness_artifact"]).read_text())["witnesses"]
    receipt = json.loads(args.receipt.read_text())
    assert receipt["generator_sha256"] == report["generator_sha256"]
    assert receipt["executed_rule_hash"] == report["declared_rule_hash"]
    assert receipt["rule_text_sha256"] == report["rule_callable_sha256"]
    assert len(selected) == len(receipt["results"])
    for witness, result in zip(selected, receipt["results"]):
        assert result["valid_output"] and not result["error"]
        assert witness["input"] == result["input"] and witness["racket_output"] == result["output"]
        assert witness["input_sha256"] == result["input_sha256"]
        assert witness["output_sha256"] == result["output_sha256"]
    result = {"matched": len(selected), "total": len(selected), "generator_sha256": report["generator_sha256"],
              "rule_source_sha256": report["rule_source_sha256"], "probe_sha256": file_hash(Path(__file__)),
              "report_sha256": file_hash(args.report), "receipt_sha256": file_hash(args.receipt)}
    write_json(args.out, result)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)
    one = subparsers.add_parser("extract")
    one.add_argument("--census", type=Path, required=True)
    one.add_argument("--out", type=Path, required=True)
    one.add_argument("--expected-generator-hash", required=True)
    two = subparsers.add_parser("verify-apply")
    two.add_argument("--report", type=Path, required=True)
    two.add_argument("--receipt", type=Path, required=True)
    two.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    extract(args) if args.action == "extract" else verify_apply(args)


if __name__ == "__main__":
    main()

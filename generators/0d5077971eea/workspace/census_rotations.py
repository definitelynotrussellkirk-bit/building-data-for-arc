"""Score every cyclic three-demo window in retained public census instances.

Uses only saved authoritative labels and the actual final generator declarations.
No private runner APIs; never regenerates a different lesson population.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from review_support import (TASK_ID, declared_rivals, digest, load_generator, pairs,
                            score_window)


def audit(census, gen):
    source_hash = hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
    report = {"schema": "0d5077971eea-census-rotations-v1", "task_id": TASK_ID,
              "generator_sha256": source_hash, "declared_rule_hash": gen.RULE_HASH,
              "census_generator_sha256": census.get("generator_sha256"),
              "census_status": census.get("status"),
              "rule_source_sha256": census.get("rule_source_sha256"),
              "rule_callable_sha256": census.get("rule_callable_sha256"),
              "census_sampler": census.get("sampler"),
              "runtime_manifest_sha256": census.get("runtime_manifest_sha256"),
              "errors": [], "canonical_rival_fit": {}, "per_band": {}, "windows": [],
              "ambiguous_witnesses": [], "limits": [
                  "Finite saved authoritative instances against declared rivals only.",
                  "Each window has three cyclic consecutive demonstrations and every remaining pair as a query.",
                  "Counts overlap windows; unique-input counts use exact normalized input hashes."]}
    if census.get("task_id") != TASK_ID:
        report["errors"].append("Census task differs from selected generator")
    if census.get("generator_sha256") != source_hash:
        report["errors"].append("Census generator bytes differ from final generator; do not mix sources")
    if census.get("declared_rule_hash") != gen.RULE_HASH:
        report["errors"].append("Census declared authority pin differs from final generator")
    if census.get("status") not in ("no_declared_ambiguity", "ambiguous", "warning"):
        report["errors"].append("Census is incomplete, errored, or lacks a rival contract")
    rivals = declared_rivals(gen)
    report["rivals"] = sorted(rivals)
    canonical = pairs()
    report["canonical_pairs"] = len(canonical)
    for name, fn in rivals.items():
        fits, errors = 0, []
        for index, pair in enumerate(canonical):
            try:
                from reviewer_support import normalize_grid
                fits += int(normalize_grid(fn(deepcopy(pair["input"]))) == pair["output"])
            except Exception as exc:
                errors.append({"pair_index": index, "error": f"{type(exc).__name__}: {exc}"})
        report["canonical_rival_fit"][name] = {"fits": fits, "pairs": len(canonical), "errors": errors,
                                               "status": "error" if errors else "fits_all" if fits == len(canonical) else "refuted"}
        if errors:
            report["errors"].append(f"Canonical scoring error: {name}")
        if name.startswith("CANONICAL_SHORTCUTS:") and fits != len(canonical):
            report["errors"].append(f"Declared canonical shortcut does not fit every canonical pair: {name}")
    # A hash mismatch is a completed failure report, not permission to score
    # old labels using newly edited rival functions.
    if report["errors"]:
        report["status"] = "error"
        return report
    inputs, total = set(), Counter()
    bands = {}
    for row in census.get("lessons", []):
        band = row["band"]
        if band not in bands:
            bands[band] = {"counts": Counter(), "inputs": set(),
                           "rivals": {name: Counter() for name in rivals}}
        state = bands[band]
        state["counts"]["source_lessons"] += 1
        if row.get("errors") or "instance" not in row:
            report["errors"].append(f"Unusable source lesson {band}/{row['index']}")
            continue
        instance = row["instance"]
        if digest(instance) != row.get("instance_sha256"):
            report["errors"].append(f"Instance hash mismatch {band}/{row['index']}")
            continue
        lesson = instance["train"] + instance["test"]
        if len(lesson) < 4:
            report["errors"].append(f"Too few pairs for cyclic windows {band}/{row['index']}")
            continue
        state["counts"]["materialized_lessons"] += 1
        state["counts"]["source_pairs"] += len(lesson)
        for pair in lesson:
            state["inputs"].add(digest(pair["input"]))
            inputs.add(digest(pair["input"]))
        for rotation in range(len(lesson)):
            rotated = lesson[rotation:] + lesson[:rotation]
            demos, queries = rotated[:3], rotated[3:]
            window = {"band": band, "lesson_index": row["index"], "seed": row["seed"],
                      "sample_index": row["sample_index"], "rotation": rotation,
                      "source_instance_sha256": row["instance_sha256"],
                      "demo_indices": [(rotation + j) % len(lesson) for j in range(3)],
                      "query_indices": [(rotation + j) % len(lesson) for j in range(3, len(lesson))],
                      "rivals": {}, "errors": [], "hook_reasons": []}
            state["counts"]["windows"] += 1
            state["counts"]["query_pairs"] += len(queries)
            try:
                window["rivals"] = score_window(rivals, demos, queries)
                for name, status in window["rivals"].items():
                    state["rivals"][name][status] += 1
                ambiguous = [name for name, status in window["rivals"].items() if status == "ambiguous"]
                state["counts"]["ambiguous_windows"] += int(bool(ambiguous))
                if ambiguous:
                    witness = {**window, "ambiguous_rivals": ambiguous, "demos": demos, "queries": queries,
                               "rival_query_outputs": {name: [rivals[name](deepcopy(p["input"])) for p in queries]
                                                       for name in ambiguous}}
                    report["ambiguous_witnesses"].append(witness)
                hook = getattr(gen, "lesson_identifiable", None)
                if hook:
                    for query in queries:
                        reasons = hook(deepcopy(demos), deepcopy(query))
                        if not isinstance(reasons, list) or any(not isinstance(x, str) for x in reasons):
                            raise TypeError("lesson_identifiable must return list[str]")
                        window["hook_reasons"].extend(reasons)
                state["counts"]["hook_warning_windows"] += int(bool(window["hook_reasons"]))
            except Exception as exc:
                window["errors"].append(f"{type(exc).__name__}: {exc}")
                report["errors"].append(f"Window scoring error {band}/{row['index']}/{rotation}: {exc}")
            report["windows"].append(window)
    for band, state in bands.items():
        total.update(state["counts"])
        report["per_band"][band] = {**dict(state["counts"]), "unique_inputs": len(state["inputs"]),
                                     "unique_input_set_sha256": digest(sorted(state["inputs"])),
                                     "rivals": {name: dict(c) for name, c in state["rivals"].items()}}
    sampler = census.get("sampler", {})
    for band in sampler.get("bands", ()):
        materialized = report["per_band"].get(band, {}).get("materialized_lessons", 0)
        if materialized != sampler.get("per_band"):
            report["errors"].append(f"Incomplete saved population in {band}: {materialized}/{sampler.get('per_band')}")
    report["totals"] = dict(total)
    report["unique_inputs"] = len(inputs)
    report["unique_input_set_sha256"] = digest(sorted(inputs))
    report["unique_input_sha256s"] = sorted(inputs)
    if not report["windows"]:
        report["errors"].append("No complete saved lessons scored")
    report["status"] = ("error" if report["errors"] else "ambiguous" if report["ambiguous_witnesses"]
                        else "warning" if total["hook_warning_windows"] else "no_declared_ambiguity")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"Output already exists: {args.out}; use a new evidence filename")
    raw = args.census.read_bytes()
    result = audit(json.loads(raw), load_generator())
    result["census_path"] = str(args.census.resolve())
    result["census_sha256"] = hashlib.sha256(raw).hexdigest()
    result["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result.get(key) for key in
                      ("status", "generator_sha256", "totals", "unique_inputs", "errors")}, indent=2))
    return 2 if result["status"] == "error" else 1 if result["status"] in ("ambiguous", "warning") else 0


if __name__ == "__main__":
    raise SystemExit(main())

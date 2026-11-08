"""Retain bounded, source-bound lesson-census ambiguity evidence.

Canonical outputs come from the completed public Racket census. This extraction
re-executes only the two Python rivals to verify the stored ambiguity witnesses.
"""
from copy import deepcopy
import gzip
import hashlib
import inspect
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import find_root, load_selected_generator


def sha(body):
    return hashlib.sha256(body).hexdigest()


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def differences(expected, actual):
    assert len(expected) == len(actual)
    assert all(len(a) == len(b) for a, b in zip(expected, actual))
    return [{"row": r, "column": c, "canonical": a, "rival": b}
            for r, (er, ar) in enumerate(zip(expected, actual))
            for c, (a, b) in enumerate(zip(er, ar)) if a != b]


def main():
    compressed = (HERE / "census.json.gz").read_bytes()
    raw = gzip.decompress(compressed)
    report = json.loads(raw)
    manifest = json.loads((HERE / "census.compression.json").read_text())["files"][0]
    assert len(raw) == manifest["raw_size"] and sha(raw) == manifest["raw_sha256"]
    assert len(compressed) == manifest["compressed_size"] and sha(compressed) == manifest["compressed_sha256"]
    module, source, digest = load_selected_generator("dc2c4869445c", root=find_root(__file__))
    assert digest == report["generator_sha256"] == "f200365928e54477a847a8494a60c081a4428a6057d99491b1b26de34b94cda4"
    identity = {k: report[k] for k in ["task_id", "generator_sha256", "rule_source_sha256",
                "rule_callable_sha256", "declared_rule_hash", "runtime_manifest_sha256", "controller_sha256"]}
    identity.update({"census_raw_sha256": sha(raw), "census_gzip_sha256": sha(compressed),
                     "label_authority": "Previously executed canonical Racket labels in census.json.gz; extraction does not relabel",
                     "rival_prediction_authority": "Fresh execution of the source-bound selected generator SEMANTIC_RIVALS",
                     "hash_definitions": {
                         "rule_source_sha256": "UTF-8 bytes of raw canonical row program_solution",
                         "rule_callable_sha256": "UTF-8 bytes of the public runner wrapped callable",
                         "rival_function_sha256": "UTF-8 bytes of inspect.getsource(callable), including leading/trailing whitespace"}})
    predictions = {}
    for name, fn in module.SEMANTIC_RIVALS.items():
        predictions["SEMANTIC_RIVALS:" + name] = {
            "callable_name": fn.__name__, "rival_function_sha256": sha(inspect.getsource(fn).encode())}
    identity["rival_sources"] = predictions

    ambiguous = []
    candidates = []
    for row in report["lessons"]:
        bad = [r for r in row["rotations"] if r["ambiguous"]]
        if bad:
            ambiguous.append({k: row[k] for k in ["band", "index", "seed", "sample_index", "instance_sha256", "instance"]}
                             | {"production_ambiguous": row["ambiguous"],
                                "ambiguous_query_indices": [r["query_index"] for r in bad],
                                "rotation_verdicts": [{"query_index": r["query_index"], "rivals": r["rivals"]} for r in row["rotations"]]})
        for rotation in bad:
            score = max(len(differences(w["expected_output"], w["rival_output"]))
                        for w in rotation["rival_witnesses"].values())
            candidates.append((score, row, rotation))

    production = max((c for c in candidates if c[1]["ambiguous"] and c[2]["query_index"] == 3), key=lambda c: c[0])
    rotation_only = max((c for c in candidates if c[2]["query_index"] != 3), key=lambda c: c[0])
    medium = max((c for c in candidates if c[1]["band"] == "medium"), key=lambda c: c[0])
    selections = [("production-ambiguity", production), ("rotation-ambiguity", rotation_only), ("medium-rotation-ambiguity", medium)]
    selected_summary = []
    for stem, (score, row, rotation) in selections:
        pairs = row["instance"]["train"] + row["instance"]["test"]
        q = rotation["query_index"]
        train_indices = rotation["train_indices"]
        lesson = {"train": [deepcopy(pairs[i]) for i in train_indices], "test": [deepcopy(pairs[q])]}
        evidence = {"schema": "dc2c4869445c-census-witness-v1", "source_identity": identity,
                    "selection": {k: row[k] for k in ["band", "index", "seed", "sample_index", "instance_sha256"]},
                    "original_production_ambiguous": row["ambiguous"], "original_query_index": 3,
                    "held_out_pair_index": q, "train_indices": train_indices,
                    "lesson_file": stem + ".lesson.json", "original_instance": row["instance"],
                    "rivals": {}, "strongest_query_difference_cells": score}
        for full_name, source_identity in predictions.items():
            fn = module.SEMANTIC_RIVALS[full_name.split(":", 1)[1]]
            pair_results = []
            for i, pair in enumerate(pairs):
                out = fn(deepcopy(pair["input"]))
                diff = differences(pair["output"], out)
                pair_results.append({"original_pair_index": i, "split": "test" if i == q else "train",
                                     "rival_output": out, "matches_canonical": not diff, "differences": diff})
            status = ("refuted" if any(not pair_results[i]["matches_canonical"] for i in train_indices)
                      else "survived_all" if pair_results[q]["matches_canonical"] else "ambiguous")
            assert status == rotation["rivals"][full_name]
            if full_name in rotation["rival_witnesses"]:
                witness = rotation["rival_witnesses"][full_name]
                assert witness["input"] == pairs[q]["input"]
                assert witness["expected_output"] == pairs[q]["output"]
                assert witness["rival_output"] == pair_results[q]["rival_output"]
            evidence["rivals"][full_name] = source_identity | {"status": status, "pair_predictions": pair_results}
        assert evidence["rivals"]["SEMANTIC_RIVALS:globally_unique_seeds"]["status"] == "ambiguous"
        dump(stem + ".lesson.json", lesson)
        evidence["lesson_file_sha256"] = sha((HERE / (stem + ".lesson.json")).read_bytes())
        dump(stem + ".evidence.json", evidence)
        selected_summary.append({"stem": stem, "band": row["band"], "index": row["index"],
                                 "seed": row["seed"], "query_index": q, "differences": score})

    dump("ambiguous-cases.json", {"schema": "dc2c4869445c-ambiguous-census-cases-v1",
         "source_identity": identity, "count": len(ambiguous), "lessons": ambiguous})
    dump("witness-summary.json", {"source_identity": identity, "selected": selected_summary,
                                  "ambiguous_bundles": len(ambiguous), "census_summary": report["summary"]})
    assert sha(source.read_bytes()) == digest
    print(json.dumps({"status": "verified", "ambiguous_bundles": len(ambiguous), "selected": selected_summary}, sort_keys=True))


if __name__ == "__main__":
    main()

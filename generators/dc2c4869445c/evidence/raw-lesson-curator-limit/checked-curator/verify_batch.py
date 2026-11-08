"""Independent bounded verification of optional strict lesson curation.

Run phases through review.py run. Curate uses the task-local public API. Label
uses public Catalog.apply (the same controller as arcpuzzles apply) in bounded
chunks of 64. Verify requires that independent receipt over every curated pair.
The original source-bound census remains the authority for unchanged pairs.
"""
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback

HERE = Path(__file__).resolve().parent
WORK = HERE.parent.parent
REPO = WORK / "repo"
CENSUS = HERE.parent / "lesson-census"
TASK = "dc2c4869445c"
GENERATOR_SHA = "f200365928e54477a847a8494a60c081a4428a6057d99491b1b26de34b94cda4"
RULE_RAW_SHA = "bf88e8ff998e82775552a9164adcc733433cf5fc60a9df43afa1467a4106b49f"
RULE_CALLABLE_SHA = "4f9e1757d2fb7d1360948dfa342feebdee6f8626f40cef3d88dfaeb989ddfe26"
CENSUS_RAW_SHA = "857229364e0e0c23c3c9cbe0f7137f9d5133847f60669fb45bfa85931a7ba3b9"
HASH_DEFINITIONS = {
    "source_hashes": "SHA-256 of exact source file bytes at the named repository-relative path",
    "before_query_sha256": "SHA-256 of sorted compact JSON for the full query input/output pair plus one newline, UTF-8",
    "after_query_sha256": "Same byte recipe as before_query_sha256",
    "distinct_input_hashes": "SHA-256 of sorted compact JSON for each input grid plus one newline, UTF-8",
    "fresh_racket_receipt_sha256": "SHA-256 of exact decompressed racket-verification.json.gz bytes",
}
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import load_selected_generator, normalize_grid


def sha(body):
    return hashlib.sha256(body).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write(name, value):
    (HERE / name).write_bytes(encoded(value))


def write_gzip(name, value):
    raw = encoded(value)
    compressed = gzip.compress(raw, mtime=0)
    (HERE / (name + ".gz")).write_bytes(compressed)
    write(name + ".compression.json", {"schema": "review-batch-gzip-v1", "path": name,
          "compressed_path": name + ".gz", "raw_size": len(raw), "raw_sha256": sha(raw),
          "compressed_size": len(compressed), "compressed_sha256": sha(compressed),
          "restore_note": "Decompress a copy and verify raw_size/raw_sha256 before use."})


def read_gzip(name):
    compressed = (HERE / (name + ".gz")).read_bytes()
    manifest = json.loads((HERE / (name + ".compression.json")).read_bytes())
    raw = gzip.decompress(compressed)
    assert sha(compressed) == manifest["compressed_sha256"] and len(compressed) == manifest["compressed_size"]
    assert sha(raw) == manifest["raw_sha256"] and len(raw) == manifest["raw_size"]
    return json.loads(raw)


def source_hashes():
    paths = [f"generators/{TASK}/generator.py", f"generators/{TASK}/workspace/lesson_curator.py",
             f"generators/{TASK}/workspace/parametric/gap_variant.py",
             "shared/runtime/reviewer_support.py", "shared/runtime/arc_repl/racket_bridge.py",
             "shared/runtime/puzzle_generators/rule_wrap.py", "shared/runtime/puzzle_generators/runner.py",
             "src/arcpuzzles/catalog.py", "src/arcpuzzles/runtime.py"]
    return {p: sha((REPO / p).read_bytes()) for p in paths}


def plain(instance):
    lesson = {key: deepcopy(instance[key]) for key in ["train", "test"]}
    assert len(lesson["train"]) == 3 and len(lesson["test"]) == 1
    for pair in lesson["train"] + lesson["test"]:
        assert set(pair) == {"input", "output"}
        assert normalize_grid(pair["input"]) == pair["input"]
        assert normalize_grid(pair["output"]) == pair["output"]
    return lesson


def load_census():
    raw = gzip.decompress((CENSUS / "census.json.gz").read_bytes())
    assert sha(raw) == CENSUS_RAW_SHA
    report = json.loads(raw)
    assert report["generator_sha256"] == GENERATOR_SHA
    assert report["rule_source_sha256"] == RULE_RAW_SHA
    assert report["rule_callable_sha256"] == RULE_CALLABLE_SHA
    assert report["summary"]["materialized"] == 300
    return report


def score(lesson, generator):
    pairs = lesson["train"] + lesson["test"]
    disagreements = {}
    for name, rival in generator.SEMANTIC_RIVALS.items():
        disagreements["SEMANTIC_RIVALS:" + name] = [
            normalize_grid(rival(deepcopy(pair["input"]))) != pair["output"] for pair in pairs]
    assert set(disagreements) == {"SEMANTIC_RIVALS:translate_copies", "SEMANTIC_RIVALS:globally_unique_seeds"}
    rotations = []
    for query in range(4):
        statuses = {}
        for name, differs in disagreements.items():
            statuses[name] = ("refuted" if any(differs[i] for i in range(4) if i != query)
                              else "ambiguous" if differs[query] else "survived_all")
        rotations.append({"query_index": query, "rivals": statuses})
    return {"disagreement_counts": {k: sum(v) for k, v in disagreements.items()},
            "pair_disagreements": disagreements, "production": rotations[3]["rivals"], "rotations": rotations,
            "strict_pass": all(v == "refuted" for r in rotations for v in r["rivals"].values())}


def curate():
    snapshot = source_hashes()
    assert snapshot[f"generators/{TASK}/generator.py"] == GENERATOR_SHA
    census = load_census()
    cases = json.loads((CENSUS / "strict-policy-cases.json").read_bytes())
    assert cases["count"] == len(cases["lessons"]) == 71
    generator, _, digest = load_selected_generator(TASK, root=REPO)
    assert digest == GENERATOR_SHA
    path = REPO / f"generators/{TASK}/workspace/lesson_curator.py"
    spec = importlib.util.spec_from_file_location("independent_review_lesson_curator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    records = []
    inputs = []
    total_calls = 0
    active_case = None
    try:
        with module.RuleExecutor() as executor:
            for case in cases["lessons"]:
                active_case = {k: case[k] for k in ["band", "index", "seed", "classification"]}
                before = plain(case["instance"])
                untouched_before = deepcopy(before)
                before_score = score(before, generator)
                assert not before_score["strict_pass"]
                actual_classification = ("observed_ambiguity"
                    if any(value == "ambiguous" for rotation in before_score["rotations"] for value in rotation["rivals"].values())
                    else "answer_equivalent_no_refuting_evidence")
                assert actual_classification == case["classification"]
                observed_before = executor.calls
                result = module.curate_lesson(before, seed=case["seed"], difficulty=case["band"],
                    start_index=case["instance"]["sampling"]["next_sample_index"], max_attempts=128, executor=executor)
                delta = executor.calls - observed_before
                total_calls += delta
                assert delta == result["report"]["actual_racket_label_calls"]
                assert before == untouched_before, "Curator mutated its caller's lesson"
                assert set(result) == {"public", "private", "report"}
                assert set(result["private"]) == {"train", "test"}
                after = plain(result["private"])
                assert after["test"] == before["test"], "Original query input/output changed"
                assert result["public"] == {"train": after["train"], "test": [{"input": after["test"][0]["input"]}]}
                after_score = score(after, generator)
                assert after_score["strict_pass"]
                assert all(not generator.self_check(pair["input"]) for pair in after["train"] + after["test"])
                start = len(inputs)
                inputs.extend(deepcopy(pair["input"]) for pair in after["train"] + after["test"])
                records.append(active_case | {"original_instance_sha256": case["instance_sha256"],
                    "before": before, "after": after, "before_score": before_score, "after_score": after_score,
                    "query_preserved": True, "before_query_sha256": sha(encoded(before["test"][0])),
                    "after_query_sha256": sha(encoded(after["test"][0])),
                    "actual_curator_racket_label_calls": delta, "fresh_apply_result_indices": list(range(start, start + 4)),
                    "curator_report": result["report"]})
                print(json.dumps({"completed": len(records), "requested": 71, **active_case,
                                  "curator_label_calls": delta, "total_curator_label_calls": total_calls}), flush=True)
            assert total_calls == executor.calls
        assert source_hashes() == snapshot
        payload = {"schema": "dc2c4869445c-curator-batch-v1", "source_hashes": snapshot,
                   "hash_definitions": HASH_DEFINITIONS,
                   "census_raw_sha256": CENSUS_RAW_SHA, "count": len(records),
                   "actual_curator_racket_label_calls": total_calls, "records": records}
        write_gzip("curation-records.json", payload)
        write("verification-inputs.json", inputs)
        write("curation-summary.json", {"status": "curation_complete_pending_independent_racket",
              "source_hashes": snapshot, "requested": 71, "curated": len(records),
              "classified_counts": dict(Counter(row["classification"] for row in records)),
              "queries_preserved": sum(row["query_preserved"] for row in records),
              "actual_curator_racket_label_calls": total_calls, "independent_apply_inputs": len(inputs),
              "finite_scope": "Optional demonstration curation only; raw sampler unchanged."})
    except BaseException as exc:
        write_gzip("curation-partial.json", {"source_hashes": snapshot, "records": records})
        write("failure.json", {"phase": "curate", "source_hashes_before": snapshot,
              "source_hashes_after": source_hashes(), "active_case": active_case,
              "completed": len(records), "successful_case_label_calls": total_calls,
              "executor_label_calls_at_failure": getattr(locals().get("executor"), "calls", None),
              "error": repr(exc), "details": getattr(exc, "details", None), "traceback": traceback.format_exc()})
        raise


def label():
    from arcpuzzles import Catalog
    snapshot = source_hashes()
    batch = read_gzip("curation-records.json")
    assert snapshot == batch["source_hashes"]
    inputs = json.loads((HERE / "verification-inputs.json").read_bytes())
    assert len(inputs) == 284
    catalog = Catalog(REPO)
    receipts = []
    try:
        for start in range(0, len(inputs), 64):
            selected = inputs[start:start + 64]
            receipt = catalog.apply(TASK, selected, reference="canonical", timeout=180)
            assert len(receipt["results"]) == len(selected)
            receipts.append({"start_index": start, "input_count": len(selected),
                             "public_api": "Catalog(root=REPO).apply(TASK, inputs, reference='canonical', timeout=180)",
                             "receipt": receipt})
            print(json.dumps({"completed_apply_batches": len(receipts), "completed_inputs": start + len(selected),
                              "requested_inputs": len(inputs)}), flush=True)
        assert source_hashes() == snapshot
        write_gzip("racket-verification.json", {"schema": "review-grouped-public-apply-v1",
                   "source_hashes": snapshot, "label_calls": len(inputs), "batch_size_limit": 64,
                   "batches": receipts})
    except BaseException as exc:
        write_gzip("racket-verification-partial.json", {"source_hashes": snapshot, "batches": receipts})
        write("label-failure.json", {"phase": "label", "source_hashes": snapshot,
              "completed_batches": len(receipts), "error": repr(exc),
              "process_receipt": getattr(exc, "run", None), "traceback": traceback.format_exc()})
        raise


def verify():
    snapshot = source_hashes()
    batch = read_gzip("curation-records.json")
    assert snapshot == batch["source_hashes"]
    assert batch["count"] == len(batch["records"]) == 71
    census = load_census()
    generator, _, digest = load_selected_generator(TASK, root=REPO)
    assert digest == GENERATOR_SHA
    grouped = read_gzip("racket-verification.json")
    assert grouped["source_hashes"] == snapshot
    assert grouped["label_calls"] == 284 and len(grouped["batches"]) == 5
    receipt_digest = sha(gzip.decompress((HERE / "racket-verification.json.gz").read_bytes()))
    fresh_results = []
    for group in grouped["batches"]:
        assert group["start_index"] == len(fresh_results)
        receipt = group["receipt"]
        assert receipt["generator_sha256"] == GENERATOR_SHA
        assert receipt["rule_text_sha256"] == RULE_CALLABLE_SHA
        assert receipt["executed_rule_hash"] == "f9fbf72b057d"
        assert len(receipt["results"]) == group["input_count"]
        fresh_results.extend(receipt["results"])
    assert len(fresh_results) == 284
    curated = {}
    labels_verified = 0
    for row in batch["records"]:
        lesson = plain(row["after"])
        assert lesson["test"] == row["before"]["test"]
        independent = score(lesson, generator)
        assert independent == row["after_score"] and independent["strict_pass"]
        for pair, index in zip(lesson["train"] + lesson["test"], row["fresh_apply_result_indices"]):
            actual = fresh_results[index]
            assert actual["index"] == index % 64 and actual["input"] == pair["input"]
            assert actual["valid_output"] is True and actual["error"] is None
            assert actual["output"] == pair["output"]
            labels_verified += 1
        curated[(row["band"], row["index"])] = row
    assert labels_verified == 284
    union = []
    verdicts = {}
    production_verdicts = {}
    input_hashes = []
    for original in census["lessons"]:
        key = (original["band"], original["index"])
        was_curated = key in curated
        lesson = plain(curated[key]["after"] if was_curated else original["instance"])
        if not was_curated:
            assert lesson == plain(original["instance"])
        assert lesson["test"] == original["instance"]["test"]
        scoring = score(lesson, generator)
        assert scoring["strict_pass"], (key, scoring)
        for rotation in scoring["rotations"]:
            for rival, verdict in rotation["rivals"].items():
                verdicts.setdefault(rival, Counter())[verdict] += 1
        for rival, verdict in scoring["production"].items():
            production_verdicts.setdefault(rival, Counter())[verdict] += 1
        input_hashes.extend(sha(encoded(pair["input"])) for pair in lesson["train"] + lesson["test"])
        union.append({"band": original["band"], "index": original["index"], "seed": original["seed"],
                      "original_instance_sha256": original["instance_sha256"],
                      "disposition": "curated" if was_curated else "unchanged", "lesson": lesson, "scores": scoring})
    assert len(union) == 300 and sum(row["disposition"] == "unchanged" for row in union) == 229
    assert source_hashes() == snapshot
    write_gzip("strict-export-union.json", {"schema": "dc2c4869445c-verified-finite-union-v1",
          "source_hashes": snapshot, "census_raw_sha256": CENSUS_RAW_SHA,
          "fresh_racket_receipt_sha256": receipt_digest, "lessons": union})
    summary = {"status": "verified_finite_batch", "source_hashes": snapshot,
          "hash_definitions": HASH_DEFINITIONS,
          "census_raw_sha256": CENSUS_RAW_SHA, "fresh_racket_receipt_sha256": receipt_digest,
          "original_observed_ambiguity_bundles": 44, "original_answer_equivalent_bundles": 27,
          "curated": 71, "unchanged": 229, "lessons": 300, "pairs": 1200,
          "distinct_input_hashes": len(set(input_hashes)), "queries_preserved": 300,
          "curated_queries_preserved": 71, "production_ambiguous": 0, "rotations": 1200,
          "ambiguous_rotations": 0, "production_rivals": production_verdicts, "rotation_rivals": verdicts,
          "actual_curator_racket_label_calls": batch["actual_curator_racket_label_calls"],
          "independent_fresh_racket_label_calls": labels_verified,
          "total_followup_racket_label_calls": batch["actual_curator_racket_label_calls"] + labels_verified,
          "unchanged_labels_reused_from_original_racket_census": 229 * 4,
          "scope": "Strict elimination of exactly two declared rivals in this finite export of 300 lessons; no raw-sampler fix or unrestricted identifiability claim."}
    write("verification-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["curate"]:
        curate()
    elif sys.argv[1:] == ["label"]:
        label()
    elif sys.argv[1:] == ["verify"]:
        verify()
    else:
        raise SystemExit("usage: verify_batch.py curate|label|verify")

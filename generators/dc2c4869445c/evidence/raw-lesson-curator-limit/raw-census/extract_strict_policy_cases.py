"""Separate answer-equivalent survivors from actual census ambiguities."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "repo/shared/runtime"))
from reviewer_support import find_root, load_selected_generator


def write(name, payload):
    (HERE / name).write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def main():
    raw = gzip.decompress((HERE / "census.json.gz").read_bytes())
    assert hashlib.sha256(raw).hexdigest() == "857229364e0e0c23c3c9cbe0f7137f9d5133847f60669fb45bfa85931a7ba3b9"
    census = json.loads(raw)
    ambiguous_bytes = (HERE / "ambiguous-cases.json").read_bytes()
    ambiguous = json.loads(ambiguous_bytes)
    module, source, digest = load_selected_generator("dc2c4869445c", root=find_root(__file__))
    assert digest == census["generator_sha256"] == ambiguous["source_identity"]["generator_sha256"]
    survivors = []
    strict_cases = []
    for row in census["lessons"]:
        has_ambiguity = any(rotation["ambiguous"] for rotation in row["rotations"])
        strict_ok = all(status == "refuted" for rotation in row["rotations"] for status in rotation["rivals"].values())
        if strict_ok:
            continue
        classification = "observed_ambiguity" if has_ambiguity else "answer_equivalent_no_refuting_evidence"
        case = {k: row[k] for k in ["band", "index", "seed", "sample_index", "instance_sha256", "instance"]}
        case.update({"classification": classification, "production_ambiguous": row["ambiguous"],
                     "ambiguous_query_indices": [r["query_index"] for r in row["rotations"] if r["ambiguous"]],
                     "rotation_verdicts": [{"query_index": r["query_index"], "rivals": r["rivals"]} for r in row["rotations"]]})
        strict_cases.append(case)
        if not has_ambiguity:
            assert all(r["rivals"]["SEMANTIC_RIVALS:globally_unique_seeds"] == "survived_all" for r in row["rotations"])
            assert all(r["rivals"]["SEMANTIC_RIVALS:translate_copies"] == "refuted" for r in row["rotations"])
            survivors.append(case)
    assert len(survivors) == 27 and len(strict_cases) == 71
    assert len(strict_cases) - len(survivors) == ambiguous["count"] == 44
    for name, cases in [("answer-equivalent-cases.json", survivors), ("strict-policy-cases.json", strict_cases)]:
        write(name, {"schema": "dc2c4869445c-strict-policy-cases-v1", "source_identity": ambiguous["source_identity"],
                     "count": len(cases), "lessons": cases})
    selected = survivors[0]
    lesson = {key: deepcopy(selected["instance"][key]) for key in ["train", "test"]}
    evidence = {"schema": "dc2c4869445c-answer-equivalent-witness-v1", "source_identity": ambiguous["source_identity"],
                "classification": selected["classification"],
                "selection": {key: selected[key] for key in ["band", "index", "seed", "sample_index", "instance_sha256"]},
                "original_instance": selected["instance"], "rotation_verdicts": selected["rotation_verdicts"], "rival_predictions": {}}
    pairs = lesson["train"] + lesson["test"]
    for name, rival in module.SEMANTIC_RIVALS.items():
        predictions = [rival(deepcopy(pair["input"])) for pair in pairs]
        evidence["rival_predictions"]["SEMANTIC_RIVALS:" + name] = predictions
        if name == "globally_unique_seeds":
            assert predictions == [pair["output"] for pair in pairs]
    write("answer-equivalent.lesson.json", lesson)
    evidence["lesson_file_sha256"] = hashlib.sha256((HERE / "answer-equivalent.lesson.json").read_bytes()).hexdigest()
    write("answer-equivalent.evidence.json", evidence)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    assert (HERE / "ambiguous-cases.json").read_bytes() == ambiguous_bytes
    print(json.dumps({"status": "verified", "observed_ambiguous_bundles": 44,
                      "answer_equivalent_bundles": 27, "strict_policy_repair_bundles": 71,
                      "strict_policy_unchanged_bundles": 229, "representative": evidence["selection"]}, sort_keys=True))


if __name__ == "__main__":
    main()

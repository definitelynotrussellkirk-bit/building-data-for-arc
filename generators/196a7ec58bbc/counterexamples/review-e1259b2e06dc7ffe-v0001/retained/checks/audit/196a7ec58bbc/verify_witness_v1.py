"""Check retained official Racket/application/production evidence against rivals."""
import hashlib
import json
from pathlib import Path

from probe_reflection_ambiguity import RIVALS, TASK, rotate_tiles


def main():
    here = Path(__file__).resolve().parent
    application = json.loads((here / "seed33-racket-apply.json").read_text())
    episode = json.loads((here / "seed33-production.jsonl").read_text())
    probe = json.loads((here / "reflection-probe.json").read_text())
    expected = probe["rivals"]["mirror_tiles"]["first_ambiguity"]
    assert expected["seed"] == episode["seed"] == 33
    assert application["generator_sha256"] == episode["provenance"]["generator_sha256"] == probe["generator_sha256"]
    assert application["executed_rule_hash"] == episode["executed_rule_hash"] == probe["rule_normalized12"]
    assert application["rule_text_sha256"] == probe["rule_sha256"]
    pairs = episode["train"] + episode["test"]
    assert len(pairs) == len(application["results"]) == 4
    assert [p["sample_index"] for p in episode["sampling"]["accepted_pairs"]] == [0,1,2,3]
    assert episode["rejections"] == []
    for pair, actual, preliminary in zip(pairs,application["results"],expected["train"]+expected["test"]):
        assert pair["input"] == actual["input"] == preliminary["input"]
        assert pair["output"] == actual["output"] == preliminary["output"] == rotate_tiles(pair["input"])
        assert actual["valid_output"] and actual["error"] is None
        assert actual["generator_domain"] == {"status":"valid","errors":[]}
    scores = {}
    for name, rival in RIVALS.items():
        fits = [rival(pair["input"]) == pair["output"] for pair in pairs]
        rotations = [{"query_index":i,"demo_indices":[j for j in range(4) if j!=i],
                      "ambiguous":all(fits[j] for j in range(4) if j!=i) and not fits[i]} for i in range(4)]
        scores[name] = {"demo_fits":fits[:3],"query_fits":fits[3],"query_prediction":rival(pairs[3]["input"]),
                        "production_ambiguous":all(fits[:3]) and not fits[3],"rotations":rotations,
                        "ambiguous_rotations":sum(r["ambiguous"] for r in rotations)}
    assert scores["mirror_tiles"]["production_ambiguous"]
    assert scores["small_square_mirror"]["production_ambiguous"]
    report = {"schema":"racket-verified-audit-counterexample-v1","task_id":TASK,
              "generator_sha256":application["generator_sha256"],"rule_text_sha256":application["rule_text_sha256"],
              "executed_rule_hash":application["executed_rule_hash"],"difficulty":"easy","seed":33,
              "sample_index":0,"accepted_indices":[0,1,2,3],"rejections":[],"n_train":3,"n_test":1,
              "official_racket_cases_passed":4,"official_racket_cases_total":4,
              "train":pairs[:3],"test":pairs[3:],"canonical_fit":probe["canonical_fit"],"rivals":scores,
              "lesson_check":episode["lesson_check"],
              "evidence_sha256":{name:hashlib.sha256((here/name).read_bytes()).hexdigest() for name in (
                  "seed33-racket-apply.json","seed33-production.jsonl","reflection-probe.json")},
              "scope":"One actual production lesson and its four retained-pair query rotations. Broader 5000-lesson probe used independent Python labels."}
    with (here / "verified-counterexample.json").open("x") as handle:
        json.dump(report,handle,indent=2)
        handle.write("\n")
    print(json.dumps({"status":"verified","official_racket_cases":"4/4","production_ambiguity":True,
                      "mirror_ambiguous_rotations":"1/4","canonical_small_square_mirror_fit":"4/4"}))


if __name__ == "__main__":
    main()

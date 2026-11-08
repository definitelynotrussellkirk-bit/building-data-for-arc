from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path.cwd()
TASK = "f13d23b71bd4"
EXPECTED_GENERATOR_SHA = "5b2f9dfdf528813ad9d342a086943138201231be812b77fcf135c510c57b2b32"
EXPECTED_MANIFEST_SHA = "455283a363988018991edee4a8efd3df60f004d8243647ede4647d15b98cfcdd"
MANIFEST = ROOT / "generators/f13d23b71bd4/workspace/parametric/evidence/manifest.json"
EVIDENCE = ROOT / (
    "generators/f13d23b71bd4/workspace/parametric/evidence/reviewer-reported/"
    "ed2d48e0fce78168/parametric/f13d23b71bd4-minimum-fall-size-v1"
)
OUTPUT = ROOT.parent / "checks/tickets/ticket-ee559d478ecebb08/result.json"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


generator = ROOT / f"generators/{TASK}/generator.py"
assert sha256_bytes(generator.read_bytes()) == EXPECTED_GENERATOR_SHA
assert sha256_bytes(MANIFEST.read_bytes()) == EXPECTED_MANIFEST_SHA
manifest = read_json(MANIFEST)
report = read_json(EVIDENCE / "report.json")

assert report["status"] == "proposed_unapproved"
assert report["approved"] is False
assert manifest["variant_approved"] is False
assert manifest["production_parametric_api"] is False
assert manifest["public_identifier_status"] == "external_correction_pending"
assert report["parameter"] == {
    "name": "minimum_fall_size",
    "allowed_values": [3, 4, 5],
    "original_default": 4,
    "selection_scope": "once_per_episode",
    "input_constraints_depend_on_parameter": False,
}
assert report["counts"]["episodes"] == 3
assert report["counts"]["train_pairs"] == 9
assert report["counts"]["query_pairs"] == 12
assert report["counts"]["settings_exercised"] == 3
assert report["counts"]["distinct_input_grids"] == 21

rows = []
for episode_row in report["episodes"]:
    public_path = EVIDENCE / episode_row["public_path"]
    private_path = EVIDENCE / episode_row["private_path"]
    raw = public_path.read_bytes()
    public = json.loads(raw)
    private = read_json(private_path)

    public_id = sha256_bytes(raw)
    assert public_path.name == f"challenge-{public_id}.json"
    assert episode_row["public_id"] == public_id
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public["train"] == [
        {"input": pair["input"], "output": pair["output"]}
        for pair in private["train"]
    ]
    assert public["test"] == [{"input": pair["input"]} for pair in private["test"]]
    assert all("output" in pair for pair in private["test"])
    assert "parameters" in private
    rows.append({
        "seed": episode_row["seed"],
        "minimum_fall_size": private["parameters"]["minimum_fall_size"],
        "public_id": public_id,
        "train_pairs": len(public["train"]),
        "query_inputs": len(public["test"]),
        "public_query_answers": sum("output" in pair for pair in public["test"]),
    })

assert {row["minimum_fall_size"] for row in rows} == {3, 4, 5}
result = {
    "schema": "arc-review-ticket-parameter-boundary-v1",
    "ticket_id": "ticket-ee559d478ecebb08",
    "task_id": TASK,
    "generator_sha256": EXPECTED_GENERATOR_SHA,
    "evidence_manifest_sha256": EXPECTED_MANIFEST_SHA,
    "boundary": {
        "settings": [3, 4, 5],
        "episodes": 3,
        "demonstrations_per_episode": 3,
        "queries_per_episode": 4,
        "public_query_answers": 0,
        "public_ids_match_visible_bytes": True,
        "private_query_answers_retained_separately": True,
    },
    "episodes": rows,
    "approval_separation": {
        "report_status": report["status"],
        "approved": report["approved"],
        "variant_approved": manifest["variant_approved"],
        "production_parametric_api": manifest["production_parametric_api"],
    },
    "known_limit": manifest["owner_public_inspection"],
    "conclusion": (
        "The retained three-setting batch has exactly four masked query inputs per episode "
        "and content-addressed public payloads. This supports the stated count/privacy boundary "
        "only; the prototype remains proposed/unapproved and its separately recorded physical "
        "emission-order gap remains unresolved."
    ),
}
OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": "completed", "result": str(OUTPUT), "episodes": len(rows)}))

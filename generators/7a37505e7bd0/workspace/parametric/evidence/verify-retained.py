"""Read-only cross-file validation of the retained bounded prototype evidence."""
from pathlib import Path
import hashlib
import json


HOME = Path(__file__).resolve().parent
REPO = HOME.parents[1] / "repo"
OUT = HOME / "final"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def grid_digest(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def read(path):
    return json.loads(path.read_text())


def settings_key(parameters):
    return parameters["counting_policy"], parameters["expansion_axis"]


report = read(OUT / "report.json")
for relative, expected in report["artifact_sha256"].items():
    assert digest((OUT / relative).read_bytes()) == expected, relative
for relative, expected in report["sources"].items():
    assert digest((REPO / relative).read_bytes()) == expected, relative
programs = {settings_key(row["parameters"]): row["sha256"] for row in report["settings"]}
for row in report["settings"]:
    assert digest(row["code"].encode()) == row["sha256"]
executions = [json.loads(line) for line in (OUT / "private/racket-executions.jsonl").read_text().splitlines()]
for index, record in enumerate(executions):
    assert record["execution_id"] == index
    assert record["backend"] == "racket"
    assert record["input_sha256"] == grid_digest(record["input"])
    assert record["output_sha256"] == grid_digest(record["output"])
episodes = {}
pair_count = 0
for lesson in report["episodes"]:
    episode = read(OUT / lesson["paths"]["private"])
    public = read(OUT / lesson["paths"]["public"])
    receipt = read(OUT / lesson["paths"]["receipt"])
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 5 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    assert public["train"] == episode["train"]
    assert public["test"][0]["input"] == episode["test"][0]["input"]
    assert receipt["parameters"] == lesson["parameters"] == episode["parameters"]
    assert receipt["private_sha256"] == digest((OUT / lesson["paths"]["private"]).read_bytes())
    assert receipt["public_sha256"] == digest((OUT / lesson["paths"]["public"]).read_bytes())
    pairs = episode["train"] + episode["test"]
    assert receipt["racket_outputs"] == [pair["output"] for pair in pairs]
    assert episode["program"]["sha256"] == programs[settings_key(episode["parameters"])]
    for pair, sample in zip(pairs, episode["sampling"], strict=True):
        record = executions[sample["racket_execution_id"]]
        assert record["program_sha256"] == episode["program"]["sha256"]
        assert record["input"] == pair["input"] and record["output"] == pair["output"]
        pair_count += 1
    episodes[lesson["episode_id"]] = pairs
rotations = read(OUT / "private/query-rotations.json")
rival_count = 0
for row in rotations:
    pairs = episodes[row["episode_id"]]
    assert row["demo_indices"] == [i for i in range(6) if i != row["query_index"]]
    statuses = []
    for rival in row["rivals"]:
        records = [executions[index] for index in rival["execution_ids"]]
        assert len(records) == len(pairs) == 6
        for index, record in enumerate(records):
            assert record["program_sha256"] == programs[settings_key(rival["parameters"])]
            assert record["input"] == pairs[index]["input"]
            assert record["output_sha256"] == rival["output_sha256"][index]
        mismatch = [i for i in row["demo_indices"] if records[i]["output"] != pairs[i]["output"]]
        query_equal = records[row["query_index"]]["output"] == pairs[row["query_index"]]["output"]
        status = "refuted" if mismatch else ("survived_all" if query_equal else "ambiguous")
        assert rival["demo_mismatch_indices"] == mismatch
        assert rival["query_equal"] == query_equal and rival["status"] == status
        statuses.append(status)
        rival_count += 1
    assert row["identified"] == all(status == "refuted" for status in statuses)
    assert row["measured_ambiguity"] == any(status == "ambiguous" for status in statuses)
canonical = read(OUT / "private/canonical-checks.json")
assert len(canonical["pairs"]) == 8
for pair in canonical["pairs"]:
    assert pair["prototype_output"] == pair["authority_output"] == pair["output"]
    assert any(record["purpose"] == "canonical_reference" and record["input"] == pair["input"]
               and record["output"] == pair["authority_output"] for record in executions)
witness = read(OUT / "private/difference-witness.json")
for row in witness["outputs"]:
    assert any(record["program_sha256"] == row["program_sha256"] and record["input"] == witness["input"]
               and record["output"] == row["output"] for record in executions)
control = read(OUT / "private/ambiguity-negative-control.json")
assert control["score"]["measured_ambiguity"] and control["solver_attempts"] == 0
result = {
    "status": "verified",
    "artifact_hashes_checked": len(report["artifact_sha256"]),
    "current_source_hashes_checked": len(report["sources"]),
    "private_episode_labels_bound_to_real_execution_records": pair_count,
    "public_challenges_checked": len(episodes),
    "rotation_scores_recomputed_from_retained_racket_outputs": len(rotations),
    "rotation_rival_scores_recomputed": rival_count,
    "actual_racket_execution_records_checked": len(executions),
    "canonical_reference_outputs_checked": 8,
    "witness_outputs_checked": 6,
    "negative_control_measured_ambiguity": True,
    "scope": "File/provenance consistency; this verification reuses retained real Racket executions and creates no new labels.",
}
print(json.dumps(result, indent=2))

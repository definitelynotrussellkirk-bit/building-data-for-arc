from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
WORK = ROOT.parent
TASK = "44d20451ce17"
EVIDENCE = WORK / "checks/parametric/destination-edge-v2-evidence.json"
PUBLIC_DIR = ROOT / f"generators/{TASK}/workspace/parametric/examples"
PROTOTYPE = ROOT / f"generators/{TASK}/workspace/parametric/prototype.py"
GENERATOR = ROOT / f"generators/{TASK}/generator.py"
EXPECTED_GENERATOR_SHA = "ff9c89eb7fe655b851f32e1e273ad9065bab4f3fa8eb3d383bb973e2714869b0"
EXPECTED_RULES = {
    "bottom": "58a0c5aaca51aaa7a99d13233d936fa9406efa3a127bdc0dc4d88366a8d918c5",
    "top": "c06f627f1dc357b027559f73623a08ab97f6078340e453a5f5621db215b18938",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
assert report["schema"] == "44d20451ce17-parametric-evidence-v2"
assert report["status"] == "proposed"
assert report["checks"]["all_passed"] is True
assert sha(GENERATOR) == EXPECTED_GENERATOR_SHA
assert report["sources"]["selected_generator"]["sha256"] == EXPECTED_GENERATOR_SHA
assert report["sources"]["prototype"]["sha256"] == sha(PROTOTYPE)
assert {
    edge: item["sha256"] for edge, item in report["sources"]["rules"].items()
} == EXPECTED_RULES
assert report["replay"]["n_train"] == 3
assert report["replay"]["n_test"] == 4

episodes = report["private_episodes"]
assert len(episodes) == 2
assert {episode["parameters"]["destination_edge"] for episode in episodes} == {
    "bottom",
    "top",
}
by_public_id = {}
for episode in episodes:
    assert episode["counts"] == {"demonstrations": 3, "queries": 4}
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    assert len(episode["sample_indices"]) == 7
    assert episode["sample_indices"] == sorted(set(episode["sample_indices"]))
    grids = [pair["input"] for pair in [*episode["train"], *episode["test"]]]
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    assert len(set(encoded)) == 7
    assert episode["rival"]["demo_differences"]
    assert episode["rival"]["query_differences"] == [0, 1, 2, 3]
    public_id = public_challenge_id(episode)
    assert public_id not in by_public_id
    by_public_id[public_id] = episode

records = report["public_files"]
assert [record["public_id"] for record in records] == sorted(by_public_id)
hash_files = {
    path.name
    for path in PUBLIC_DIR.glob("*.json")
    if len(path.stem) == 64 and all(ch in "0123456789abcdef" for ch in path.stem)
}
assert hash_files == {f"{public_id}.json" for public_id in by_public_id}
legacy_expected = (
    '{\n'
    '  "schema": "arcpuzzles-retired-public-name-v1",\n'
    '  "status": "retired",\n'
    '  "message": "This ordinal path is not a public challenge. Run prototype.py to materialize visible-content-ID challenge files."\n'
    '}\n'
).encode("utf-8")
for legacy_name in ("episode-a.json", "episode-b.json"):
    legacy_path = PUBLIC_DIR / legacy_name
    assert legacy_path.read_bytes() == legacy_expected
    legacy = json.loads(legacy_expected)
    assert "train" not in legacy and "test" not in legacy
for record in records:
    public_id = record["public_id"]
    path = PUBLIC_DIR / f"{public_id}.json"
    payload = path.read_bytes()
    assert payload == public_challenge_bytes(by_public_id[public_id])
    assert hashlib.sha256(payload).hexdigest() == public_id == record["sha256"]
    public = json.loads(payload)
    assert len(public["train"]) == 3 and len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

summary = {
    "schema": "44d20451ce17-parametric-independent-verification-v1",
    "generator_sha256": sha(GENERATOR),
    "prototype_sha256": sha(PROTOTYPE),
    "episodes": len(episodes),
    "demonstrations_per_episode": 3,
    "queries_per_episode": 4,
    "distinct_inputs_per_episode": 7,
    "public_ids": sorted(by_public_id),
    "all_public_bytes_and_ids_verified": True,
    "legacy_ordinal_paths_retired_as_non_challenges": True,
    "all_private_checks_reported_passed": True,
}
print(json.dumps(summary, indent=2, sort_keys=True))

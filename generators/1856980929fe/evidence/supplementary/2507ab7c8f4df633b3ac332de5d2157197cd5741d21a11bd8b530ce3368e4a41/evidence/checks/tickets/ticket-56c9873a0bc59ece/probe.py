#!/usr/bin/env python3
"""Bounded source-bound four-query/privacy probe for ticket-56c9873a0bc59ece."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
TASK = "1856980929fe"
GENERATOR = REPO / "generators" / TASK / "generator.py"
MANIFEST = REPO / "generators" / TASK / "workspace/parametric/evidence/manifest.json"
EXPECTED_GENERATOR = "cf6e08b5e647f09dd3011b3d7ad3652e37df3f7ec354a7a1ba07bb570df22636"
EXPECTED_MANIFEST = "0468ef8d13bcdb7303491257da5a92eb0e2b02035a98d8e873a829aee04a51a3"
EVIDENCE_REL = Path("generators/1856980929fe/workspace/parametric/evidence/reviewer-reported/9794ad423bfd7c13/parametric/1856980929fe-fan-stride-v1")
FORBIDDEN = ("fan_stride", "query_answers", '"seed"', "program_sha256", "generator_source")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    assert sha(GENERATOR) == EXPECTED_GENERATOR
    assert sha(MANIFEST) == EXPECTED_MANIFEST
    inventory = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert inventory["task_id"] == TASK
    assert inventory["variant_approved"] is False
    assert inventory["production_parametric_api"] is False

    base = REPO / EVIDENCE_REL
    report = json.loads((base / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "proposed_unapproved"
    assert report["parameter"] == {
        "allowed_values": [1, 2],
        "input_constraints_depend_on_parameter": False,
        "name": "fan_stride",
        "original_default": 1,
    }
    assert len(report["episodes"]) == 2

    episode_rows = []
    for row in report["episodes"]:
        assert row["demo_count"] == 3
        assert row["query_count"] == 4
        assert row["deterministic_replay"] is True
        assert sorted(r["fan_stride"] for r in row["rivals"]) == [1, 2]
        selected = row["parameters"]["fan_stride"]
        matching = [r for r in row["rivals"] if r["status"] == "matches_episode"]
        rejected = [r for r in row["rivals"] if r["status"] == "refuted_by_demonstrations"]
        assert [r["fan_stride"] for r in matching] == [selected]
        assert len(rejected) == 1 and rejected[0]["demonstration_mismatch_indices"] == [0, 1, 2]
        assert rejected[0]["query_mismatch_indices"] == [0, 1, 2, 3]

        public_path = base / row["public_path"]
        private_path = base / row["private_path"]
        raw = public_path.read_bytes()
        public = json.loads(raw)
        private = json.loads(private_path.read_text(encoding="utf-8"))
        assert public_path.name == f"challenge-{row['public_id']}.json"
        assert sha(public_path) == row["public_id"]
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == len(private["train"]) == 3
        assert len(public["test"]) == len(private["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert private["parameters"] == {"fan_stride": selected}
        visible_inputs = [pair["input"] for pair in public["train"] + public["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in visible_inputs}) == 7
        text = raw.decode("utf-8")
        assert not any(token in text for token in FORBIDDEN)
        episode_rows.append({
            "seed": row["seed"],
            "fan_stride": selected,
            "demo_count": 3,
            "query_count": 4,
            "distinct_visible_inputs": 7,
            "public_id": row["public_id"],
            "opposite_setting_refuted_on_all_queries": True,
        })

    result = {
        "schema": "arcpuzzles-ticket-parameter-queries-v1",
        "ticket_id": "ticket-56c9873a0bc59ece",
        "task_id": TASK,
        "status": "completed",
        "source_bound": True,
        "variant_approved": False,
        "training_admitted": False,
        "boundary_checked": "four-query count plus public/private projection",
        "episodes": sorted(episode_rows, key=lambda x: x["fan_stride"]),
        "summary": "Both proposed fan_stride settings retain 3 identifying demonstrations, 4 distinct hidden-answer queries, fixed episode semantics, and visible-only content-addressed public files. This supports follow-up only; it does not approve the variant.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()

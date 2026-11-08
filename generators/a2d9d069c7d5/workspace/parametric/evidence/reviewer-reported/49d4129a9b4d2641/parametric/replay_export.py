"""Replay the returned private examples and check their exact public projection."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes, public_challenge_id

WORK = Path(__file__).resolve().parents[2]
SOURCE = WORK / "repo/generators/a2d9d069c7d5/workspace/parametric/prototype.py"
spec = importlib.util.spec_from_file_location("returned_block_vote", SOURCE)
family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(family)
directory = WORK / "checks/parametric/final-four-settings"
episodes = json.loads((directory / "private/episodes.json").read_text())
summary = json.loads((directory / "summary.json").read_text())
assert summary["source_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert sorted(episodes) == summary["public_ids"]
assert sorted(p.stem for p in (directory / "public").glob("*.json")) == sorted(episodes)
rows = []
with family.RacketLabeler() as labeler:
    for identifier, episode in sorted(episodes.items()):
        assert identifier == public_challenge_id(episode)
        assert (directory / "public" / (identifier + ".json")).read_bytes() == public_challenge_bytes(episode)
        certificate = family.verify_episode(episode, labeler=labeler)
        rows.append({"public_id": identifier, "parameters": episode["parameters"],
                     "program_sha256": episode["program_sha256"],
                     "demonstrations": len(episode["train"]), "queries": len(episode["test"]),
                     "surviving_shortcuts": certificate["surviving_shortcuts"],
                     "identifiable_queries": sum(q["identifiable"] for q in certificate["queries"])})
    result = {"status": "passed", "episodes": rows, "racket_calls": labeler.calls,
              "racket_identity": labeler.identity, "source_sha256": summary["source_sha256"],
              "template_sha256": summary["template_sha256"],
              "scope": "Replay of all exported train/query labels and exact public bytes; finite certificate only"}
(WORK / "checks/parametric/final-export-replay.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": result["status"], "episodes": len(rows),
                  "racket_calls": result["racket_calls"], "identifiable_queries": sum(r["identifiable_queries"] for r in rows)}))

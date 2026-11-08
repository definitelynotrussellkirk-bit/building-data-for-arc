"""Bounded adversarial replay for the three packet-local parametric proposals."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2] / "repo"
RUNTIME = ROOT / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id

TARGETS = {
    "d07a6cba78c7": "marker_side",
    "cddbee92b2f3": "source_side",
    "bb75d495c809": "connectivity",
}


def load(task_id: str):
    path = ROOT / "generators" / task_id / "workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location(f"probe_{task_id}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    result = {
        "schema": "packet-parametric-bounded-probe-v2",
        "scope": [
            "teaching and protected-Racket replay at 2 and 6 demonstrations",
            "matched-input and public/private projection under private/query-answer mutation",
            "one-query sequential reveal and first-turn byte invariance under future-input mutation",
        ],
        "seed": 17,
        "queries": 4,
        "targets": {},
    }
    for task_id in TARGETS:
        p = load(task_id)
        rows = []
        with p.RacketRunner() as execute:
            for demos in (2, 6):
                episodes = [p.generate(17, setting, demos=demos, queries=4) for setting in p.SETTINGS]
                streams = [
                    [pair["input"] for pair in episode["train"] + episode["test"]]
                    for episode in episodes
                ]
                assert all(stream == streams[0] for stream in streams[1:])
                for setting, episode in zip(p.SETTINGS, episodes):
                    cert = p.certify(episode, execute)
                    assert cert["survivors"] == [setting]
                    assert cert["racket_checked"] is True
                    assert len(cert["queries"]) == 4
                    assert len({json.dumps(pair["input"], separators=(",", ":"))
                                for pair in episode["train"] + episode["test"]}) == demos + 4
                    controller_body = public_challenge_bytes(episode)
                    first_turn = p.public_turn_bytes(episode, 0)
                    first_visible = json.loads(first_turn)
                    assert len(first_visible["test"]) == 1
                    assert first_turn == public_challenge_bytes({
                        "train": episode["train"],
                        "test": episode["test"][:1],
                    })
                    changed = copy.deepcopy(episode)
                    changed["settings"] = {"private": "mutated"}
                    changed["program_solution"] = "mutated"
                    changed["test"][0]["output"] = [[9]]
                    changed["test"][-1]["input"] = [[9]]
                    changed["test"][-1]["output"] = [[8]]
                    assert public_challenge_bytes(changed) != controller_body
                    assert p.public_turn_bytes(changed, 0) == first_turn
                    rows.append({
                        "settings": setting,
                        "demos": demos,
                        "pairs_racket_checked": demos + 4,
                        "survivors": cert["survivors"],
                        "controller_id": public_challenge_id(episode),
                        "first_turn_id": __import__("hashlib").sha256(first_turn).hexdigest(),
                        "first_turn_query_count": len(first_visible["test"]),
                    })
            runtime_identity = execute.identity
        result["targets"][task_id] = {
            "status": "passed",
            "jobs": rows,
            "jobs_checked": len(rows),
            "pair_labels_checked": sum(row["pairs_racket_checked"] for row in rows),
            "runtime_identity": runtime_identity,
            "limitations": "finite settings, seed 17, demo boundaries 2 and 6 only",
        }
    destination = Path(__file__).with_name("bounded-probe.json")
    destination.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "status": "passed",
        "targets": len(result["targets"]),
        "jobs": sum(row["jobs_checked"] for row in result["targets"].values()),
        "pair_labels_checked": sum(row["pair_labels_checked"] for row in result["targets"].values()),
        "out": str(destination),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

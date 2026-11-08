#!/usr/bin/env python3
"""Exercise the documented minimum and maximum episode sizes on final source."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root

ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/74a14031dc79/workspace/parametric/prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location("boundary_parametric_74a14031dc79", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(module, episode: dict) -> dict:
    pairs = episode["train"] + episode["test"]
    identities = [module.grid_sha256(pair["input"]) for pair in pairs]
    expected_query_indices = list(range(episode["counts"]["queries"]))
    selected = episode["parameters"]["occupancy_rule"]
    assert len(identities) == len(set(identities))
    assert all(module.relation_set(pair["input"]) == {"00", "10", "01", "11"} for pair in pairs)
    assert episode["ambiguities"] == []
    for rival in episode["parameter_rivals"]:
        if rival["occupancy_rule"] == selected:
            assert rival["status"] == "matches_episode"
            assert rival["query_mismatch_indices"] == []
        else:
            assert rival["status"] == "refuted_by_demonstrations"
            assert rival["query_mismatch_indices"] == expected_query_indices
    return {
        "setting": selected,
        "counts": episode["counts"],
        "unique_inputs": len(set(identities)),
        "rival_checks": len(episode["parameter_rivals"]),
        "ambiguities": len(episode["ambiguities"]),
    }


def main() -> int:
    module = load_prototype()
    with RacketBridge() as bridge:
        minimum = module.make_episode(1, demo_count=1, query_count=1, root=ROOT, bridge=bridge)
        maximum = module.make_episode(1, demo_count=16, query_count=16, root=ROOT, bridge=bridge)
    result = {
        "status": "passed",
        "task_id": module.TASK_ID,
        "prototype_sha256": sha256(PROTOTYPE_PATH),
        "minimum": summarize(module, minimum),
        "maximum": summarize(module, maximum),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

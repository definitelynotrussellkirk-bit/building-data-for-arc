"""Bounded deterministic self-audit for the rarest-color plus family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("b159_audit_prototype", HOME / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load prototype")
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def run() -> dict:
    episodes = 0
    pairs = 0
    settings_identified = 0
    first_turn_checks = 0
    sizes = set()
    max_targets = 0
    max_decoys = 0
    for seed in (0, 17, 41):
        for scope in prototype.FILL_SCOPES:
            for demos in range(2, 7):
                episode = prototype.generate_episode(seed, fill_scope=scope, demos=demos, queries=4)
                episodes += 1
                pairs += demos + 4
                serialized = []
                for split in ("train", "test"):
                    for pair in episode[split]:
                        assert pair["output"] == prototype.apply_mode(pair["input"], scope)
                        serialized.append(json.dumps(pair["input"], separators=(",", ":")))
                        sizes.add((len(pair["input"]), len(pair["input"][0])))
                        info = prototype.analyze(pair["input"])
                        max_targets = max(max_targets, len(info["qualifying_centers"]))
                        max_decoys = max(max_decoys, len(info["decoy_centers"]))
                assert len(serialized) == len(set(serialized))
                survivors = [
                    candidate
                    for candidate in prototype.FILL_SCOPES
                    if all(prototype.apply_mode(pair["input"], candidate) == pair["output"] for pair in episode["train"])
                ]
                assert survivors == [scope]
                settings_identified += 1
                one = prototype.generate_episode(seed, fill_scope=scope, demos=demos, queries=1)
                assert prototype.public_bytes(one, 0) == prototype.public_bytes(episode, 0)
                first_turn_checks += 1
    case = prototype.causal_case(17)
    assert case["output"] != case["counterfactual_output"]
    return {
        "schema": "b159f935141a-parametric-self-audit-v1",
        "status": "pass",
        "episodes": episodes,
        "pairs": pairs,
        "settings_identified": settings_identified,
        "first_turn_prefix_checks": first_turn_checks,
        "sizes": sorted([list(size) for size in sizes]),
        "has_30x30": [30, 30] in [list(size) for size in sizes],
        "max_qualifying_centers": max_targets,
        "max_detected_decoys": max_decoys,
        "causal_counterfactual_changed": True,
        "limits": "Finite matched-input audit over three seeds and all supported demo counts; not universal uniqueness.",
    }


if __name__ == "__main__":
    report = run()
    if len(sys.argv) == 3 and sys.argv[1] == "--out":
        path = Path(sys.argv[2])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))

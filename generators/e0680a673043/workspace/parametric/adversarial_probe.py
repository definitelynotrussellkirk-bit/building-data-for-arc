#!/usr/bin/env python3
"""Bounded structural probe for the rank-policy family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("rank_probe_proto", HERE / "prototype.py")
assert SPEC and SPEC.loader
proto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proto)


def main() -> int:
    episodes = 0
    selected_locations = set()
    minimum_nonzero_30 = 10**9
    for demos in (2, 3, 6):
        for seed in range(8):
            for chosen in proto.RANK_POLICIES:
                episode = proto.generate_claims(seed, chosen, demos, 4)
                survivors = [
                    policy
                    for policy in proto.RANK_POLICIES
                    if all(
                        proto.python_mirror(pair["input"], rank_policy=policy) == pair["output"]
                        for pair in episode["train"]
                    )
                ]
                if survivors != [chosen]:
                    raise AssertionError((seed, demos, chosen, survivors))
                inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
                if len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) != len(inputs):
                    raise AssertionError("duplicate input")
                stress = episode["test"][-1]["input"]
                if (len(stress), len(stress[0])) != (30, 30):
                    raise AssertionError("missing 30x30 stress")
                minimum_nonzero_30 = min(
                    minimum_nonzero_30,
                    sum(cell != 0 for row in stress for cell in row),
                )
                facts = proto.scene_facts(episode["test"][0]["input"])
                selected = proto.select_intermediate(facts, chosen)
                selected_locations.add((chosen, selected["r1"], selected["c1"], selected["size"], selected["color"]))
                episodes += 1
    report = {
        "schema": "e0680a673043-rank-policy-probe-v1",
        "episodes": episodes,
        "seeds": [0, 7],
        "demo_counts": [2, 3, 6],
        "settings": list(proto.RANK_POLICIES),
        "unique_selected_signatures": len(selected_locations),
        "minimum_nonzero_cells_in_30x30": minimum_nonzero_30,
        "all_demo_sets_single_survivor": True,
        "all_inputs_distinct_within_episode": True,
    }
    out = HERE / "evidence" / "focused" / "adversarial-probe.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

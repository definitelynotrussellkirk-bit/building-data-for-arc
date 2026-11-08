#!/usr/bin/env python3
"""Bounded structural probe for the halo-component family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("halo_probe_proto", HERE / "prototype.py")
assert SPEC and SPEC.loader
proto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proto)


def main() -> int:
    episodes = 0
    selected_signatures = set()
    component_size_sets = set()
    red_count_sets = set()
    minimum_nonzero_30 = 10**9
    boundary_touches = set()
    shortcut_checks = 0
    for demos in (2, 3, 6):
        for seed in range(8):
            for chosen in proto.COMPONENT_POLICIES:
                episode = proto.generate_claims(seed, chosen, demos, 4)
                survivors = [
                    policy
                    for policy in proto.COMPONENT_POLICIES
                    if all(
                        proto.python_mirror(pair["input"], component_policy=policy) == pair["output"]
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
                if len(facts["components"]) != 3:
                    raise AssertionError("wrong component count")
                sizes = tuple(sorted(component["size"] for component in facts["components"]))
                if len(set(sizes)) != 3:
                    raise AssertionError("component-size tie")
                component_size_sets.add(sizes)
                red_counts = tuple(sorted(len(component["red_cells"]) for component in facts["components"]))
                red_count_sets.add(red_counts)
                largest = proto.select_intermediate(facts, "highlight_largest")
                smallest = proto.select_intermediate(facts, "highlight_smallest")
                if len(largest["red_cells"]) == max(red_counts):
                    raise AssertionError("largest selection collapses to maximum pre-halo red count")
                if len(smallest["red_cells"]) == min(red_counts):
                    raise AssertionError("smallest selection collapses to minimum pre-halo red count")
                shortcut_checks += 2
                h = len(episode["test"][0]["input"])
                w = len(episode["test"][0]["input"][0])
                for component in facts["components"]:
                    if component["r1"] == 0:
                        boundary_touches.add("top")
                    if component["r2"] == h - 1:
                        boundary_touches.add("bottom")
                    if component["c1"] == 0:
                        boundary_touches.add("left")
                    if component["c2"] == w - 1:
                        boundary_touches.add("right")
                if chosen != "plain":
                    selected = proto.select_intermediate(facts, chosen)
                    selected_signatures.add((chosen, selected["r1"], selected["c1"], selected["size"], len(selected["magenta_cells"])))
                episodes += 1
    report = {
        "schema": "1ba9f2a08016-halo-component-probe-v1",
        "episodes": episodes,
        "seeds": [0, 7],
        "demo_counts": [2, 3, 6],
        "settings": list(proto.COMPONENT_POLICIES),
        "unique_selected_signatures": len(selected_signatures),
        "unique_component_size_sets": len(component_size_sets),
        "unique_red_count_sets": len(red_count_sets),
        "boundary_touches": sorted(boundary_touches),
        "minimum_nonzero_cells_in_30x30_input": minimum_nonzero_30,
        "all_demo_sets_single_survivor": True,
        "all_inputs_distinct_within_episode": True,
        "prehalo_seed_count_shortcut_refuted": True,
        "prehalo_seed_count_checks": shortcut_checks,
    }
    out = HERE / "evidence" / "focused" / "adversarial-probe.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

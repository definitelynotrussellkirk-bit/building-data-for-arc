"""Reusable bounded self-review for the reflected-probe route family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _load(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("_329_audit_" + name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def audit(seed_count=20):
    adapter, family = _load("adapter"), _load("family")
    settings = [{"mode": value} for value in family.MODES]
    failures = []
    rows = []
    distinct_targets = set()
    sampled_grids = 0
    far_side_all_rejected = 0
    hit_side_only_rejected = 0
    for seed in range(seed_count):
        for demos in range(2, 7):
            try:
                episodes = [adapter.generate(seed, setting, demos, 4) for setting in settings]
                inputs = [[pair["input"] for split in ("train", "test") for pair in episode[split]]
                          for episode in episodes]
                assert inputs[0] == inputs[1]
                assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs[0]}) == demos + 4
                for grid in inputs[0]:
                    info = family.analyze(grid)
                    source_side = -1 if (info["sources"][0][0] if info["axis"] == "row" else info["sources"][0][1]) < info["divider"] else 1
                    probe_side = -source_side
                    def side_of(r, c):
                        coordinate = r if info["axis"] == "row" else c
                        return -1 if coordinate < info["divider"] else 1
                    correct = family.apply(grid, settings[1])
                    far_side_all = [[
                        8 if side_of(r, c) == probe_side and value not in (0, 6, 7, 8) else value
                        for c, value in enumerate(row)
                    ] for r, row in enumerate(grid)]
                    hit_side_only = [[
                        8 if side_of(r, c) == probe_side and value in info["target_colors"] else value
                        for c, value in enumerate(row)
                    ] for r, row in enumerate(grid)]
                    assert far_side_all != correct
                    assert hit_side_only != correct
                    sampled_grids += 1
                    far_side_all_rejected += 1
                    hit_side_only_rejected += 1
                for chosen, episode in enumerate(episodes):
                    survivors = [index for index, setting in enumerate(settings)
                                 if all(family.apply(pair["input"], setting) == pair["output"]
                                        for pair in episode["train"])]
                    assert survivors == [chosen]
                    for pair in episode["train"] + episode["test"]:
                        info = family.analyze(pair["input"])
                        assert set(info["target_colors"]).isdisjoint(info["source_side_colors"])
                        assert family.apply_with_route(pair["input"], use_reflected_probes=False) != family.apply_with_route(pair["input"], use_reflected_probes=True)
                        distinct_targets.add(tuple(info["target_colors"]))
                rows.append({"seed": seed, "demos": demos, "status": "passed"})
            except Exception as exc:
                failures.append({"seed": seed, "demos": demos, "error": f"{type(exc).__name__}: {exc}"})
    return {"schema": "329f699c3e09-probe-route-audit-v1",
            "status": "passed" if not failures else "failed",
            "seed_count": seed_count, "jobs": seed_count * 5, "rows": rows,
            "sampled_grids": sampled_grids,
            "distinct_target_sets": len(distinct_targets),
            "rival_checks": {
                "far_side_all_rejected": far_side_all_rejected,
                "hit_side_only_rejected": hit_side_only_rejected,
            },
            "failures": failures,
            "limits": "Finite Python-mirror audit over declared settings and two plausible shortcut rivals; protected Racket evidence is separate."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "seed_count", "jobs", "distinct_target_sets")}))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()

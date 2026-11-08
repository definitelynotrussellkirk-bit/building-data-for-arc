"""Reusable bounded self-review for the area-ranked gallery family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _load(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("_2f4_audit_" + name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def audit(seed_count=20):
    adapter, family = _load("adapter"), _load("family")
    settings = [{"layout": value} for value in family.LAYOUTS]
    failures, rows = [], []
    area_signatures = set()
    permutations = set()
    sampled_grids = 0
    constant_order_rejected = 0
    bbox_area_order_rejected = 0
    source_order_rejected = 0
    for seed in range(seed_count):
        for demos in range(2, 7):
            try:
                episodes = [adapter.generate(seed, setting, demos, 4) for setting in settings]
                inputs = [[pair["input"] for split in ("train", "test") for pair in episode[split]]
                          for episode in episodes]
                assert inputs[0] == inputs[1]
                assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs[0]}) == demos + 4

                # The first two visible demonstrations deliberately require two
                # different permutations, rejecting any episode-fixed order.
                train_infos = [family.analyze(pair["input"]) for pair in episodes[1]["train"]]
                train_permutations = [info["permutation"] for info in train_infos]
                assert len(set(train_permutations)) >= 2
                constant = train_permutations[0]
                assert any(
                    family.area_ranked_output(pair["input"], constant) != pair["output"]
                    for pair in episodes[1]["train"]
                )
                constant_order_rejected += 1

                # At least one visible demonstration separates occupied-cell area
                # from the cheaper bounding-box-area heuristic.
                bbox_rejected = False
                for pair, info in zip(episodes[1]["train"], train_infos):
                    bbox_order = tuple(entry["source_index"] for entry in sorted(
                        info["entries"],
                        key=lambda entry: (len(entry["mask"]) * len(entry["mask"][0]), entry["source_index"]),
                    ))
                    if family.area_ranked_output(pair["input"], bbox_order) != pair["output"]:
                        bbox_rejected = True
                        break
                assert bbox_rejected
                bbox_area_order_rejected += 1

                for grid in inputs[0]:
                    info = family.analyze(grid)
                    permutations.add(info["permutation"])
                    assert family.area_ranked_output(grid, (0, 1, 2)) != family.area_ranked_output(grid)
                    sampled_grids += 1
                    source_order_rejected += 1
                for chosen, episode in enumerate(episodes):
                    survivors = [index for index, setting in enumerate(settings)
                                 if all(family.apply(pair["input"], setting) == pair["output"]
                                        for pair in episode["train"])]
                    assert survivors == [chosen]
                    for pair in episode["train"] + episode["test"]:
                        info = family.analyze(pair["input"])
                        assert info["areas"] == sorted(info["areas"])
                        assert len(set(info["areas"])) == 3
                        assert family.area_ranked_output(pair["input"], (2, 1, 0)) != family.area_ranked_output(pair["input"])
                        assert family.canonical_output(pair["input"]) != family.area_ranked_output(pair["input"])
                        area_signatures.add(tuple(info["areas"]))
                rows.append({"seed": seed, "demos": demos, "status": "passed"})
            except Exception as exc:
                failures.append({"seed": seed, "demos": demos,
                                 "error": f"{type(exc).__name__}: {exc}"})
    return {"schema": "2f4a0e633093-area-ranked-audit-v1",
            "status": "passed" if not failures else "failed",
            "seed_count": seed_count, "jobs": seed_count * 5, "rows": rows,
            "sampled_grids": sampled_grids,
            "distinct_area_signatures": len(area_signatures),
            "distinct_permutations": len(permutations),
            "rival_checks": {
                "constant_order_rejected": constant_order_rejected,
                "bbox_area_order_rejected": bbox_area_order_rejected,
                "source_order_rejected": source_order_rejected,
            },
            "failures": failures,
            "limits": "Finite Python-mirror audit over declared settings and three plausible order rivals; protected Racket evidence is separate."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "seed_count", "jobs", "distinct_area_signatures")}))
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()

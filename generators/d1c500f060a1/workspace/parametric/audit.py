"""Reusable bounded self-review for d1c transformed-accent ordering."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _load(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("_d1c_audit_" + name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def audit(seed_count=20):
    adapter, family = _load("adapter"), _load("family")
    settings = [{"pack_order": value} for value in family.PACK_ORDERS]
    rows, key_orders = [], set()
    for seed in range(seed_count):
        for demos in range(2, 7):
            episodes = [adapter.generate(seed, setting, demos, 4) for setting in settings]
            inputs = [[pair["input"] for split in ("train", "test")
                       for pair in episode[split]] for episode in episodes]
            assert inputs[0] == inputs[1]
            assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs[0]}) == demos + 4
            for chosen, episode in enumerate(episodes):
                survivors = []
                for index, setting in enumerate(settings):
                    if all(family.apply(pair["input"], setting) == pair["output"]
                           for pair in episode["train"]):
                        survivors.append(index)
                assert survivors == [chosen]
            for grid in inputs[0]:
                info = family.analyze(grid)
                keys = family.transformed_keys(info)
                key_orders.add(tuple(sorted(range(len(keys)), key=keys.__getitem__)))
            rows.append({"seed": seed, "demos": demos, "status": "passed"})
    return {"schema": "d1c-parametric-bounded-audit-v1", "status": "passed",
            "seed_count": seed_count, "jobs": len(rows), "rows": rows,
            "distinct_derived_orders": len(key_orders),
            "limits": "Finite Python-mirror audit; protected Racket evidence is separate."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "seed_count", "jobs", "distinct_derived_orders")}))


if __name__ == "__main__":
    main()

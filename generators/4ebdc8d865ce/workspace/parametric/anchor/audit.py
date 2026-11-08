"""Run a bounded demo-only finite-rival learnability audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def load(filename, label):
    path = HERE / filename
    name = label + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    adapter = load("adapter.py", "_audit_adapter_")
    rivals = load("rivals.py", "_audit_rivals_")
    cases = []
    failures = []
    for seed in (0, 17, 31):
        for demos in (2, 3, 6):
            for selection in adapter.SELECTIONS:
                setting = {"selection": selection}
                episode = adapter.generate(seed, setting, demos, 4)
                survivors = [
                    name for name in rivals.RIVAL_NAMES
                    if all(rivals.predict(pair["input"], name) == pair["output"]
                           for pair in episode["train"])
                ]
                query_matches = {
                    name: sum(rivals.predict(pair["input"], name) == pair["output"]
                              for pair in episode["test"])
                    for name in rivals.RIVAL_NAMES
                }
                row = {
                    "seed": seed,
                    "demos": demos,
                    "queries": 4,
                    "selection": selection,
                    "anchor_sizes": [adapter.analyze(pair["input"])["anchor_size"]
                                     for pair in episode["train"]],
                    "survivors_after_demonstrations": survivors,
                    "query_matches_out_of_4": query_matches,
                }
                cases.append(row)
                if survivors != [selection] or query_matches[selection] != 4:
                    failures.append(row)
    report = {
        "schema": "4ebdc8d865ce-finite-teaching-audit-v1",
        "status": "passed" if not failures else "failed",
        "method": "Fit the finite named rival bank to visible demonstrations only; inspect query labels only after survivor selection.",
        "limits": "Finite executable rivals and sampled seeds/counts only; this is not universal uniqueness or measured learning benefit.",
        "rivals": list(rivals.RIVAL_NAMES),
        "case_count": len(cases),
        "failures": failures,
        "cases": cases,
    }
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw)
    else:
        print(raw, end="")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run bounded protected-Racket and sequential-export checks for this prototype."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root

HERE = Path(__file__).resolve().parent
TASK_ID = "a452b4b4f04a"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out)
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    root = find_root(__file__)
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"render": render}, "demos": demos, "queries": 4}
        for seed in (0, 17)
        for demos in (2, 3, 6)
        for render in ("outline", "filled")
    ]
    result = evaluate_contract(root, TASK_ID, contract, jobs)
    prototype = _load(HERE / "prototype.py", "a452_probe_prototype")
    episode_io = _load(HERE / "episode_io.py", "a452_probe_io")
    episodes = [prototype.generate(41, {"render": render}, 3, 4)
                for render in ("outline", "filled")]
    temp = Path(tempfile.mkdtemp(prefix="a452-probe-", dir=output.parent))
    try:
        bundle_receipt = episode_io.write_bundle(episodes, temp / "bundle")
        verified = episode_io.verify_bundle(temp / "bundle")
        report = {
            "schema": "a452-parametric-probe-v1",
            "task_id": TASK_ID,
            "jobs": len(jobs),
            "racket": result["racket"],
            "racket_evaluations": result["racket_evaluations"],
            "checks": result["checks"],
            "query_shapes": [list(shape) for shape in sorted({
                (len(pair["input"]), len(pair["input"][0]))
                for episode in result["episodes"] for pair in episode["test"]
            })],
            "bundle": bundle_receipt,
            "bundle_verified": verified == bundle_receipt,
            "adversarial_scope": [
                "native worker fitted every declared program to demonstrations only",
                "minimum 2-demo and maximum 6-demo requests retained four queries",
                "30x30 query labels executed through protected Racket",
                "bundle verifier checked visible hashes and public/private projection",
            ],
        }
        (temp / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        temp.rename(output)
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    print(json.dumps({"out": str(output), "jobs": len(jobs), "racket_evaluations": result["racket_evaluations"]}))


if __name__ == "__main__":
    main()

"""Bounded adversarial and protected-Racket audit for bf47583ab6e3."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root

TASK_ID = "bf47583ab6e3"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def _load(label: str, path: Path):
    body = path.read_bytes()
    name = f"_{TASK_ID}_{label}_{hashlib.sha256(body).hexdigest()}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


FAMILY = _load("family", HERE / "family.py")
ADAPTER = _load("adapter", HERE / "adapter.py")


def finite_audit(seeds=range(32), demo_counts=(2, 3, 6)) -> dict:
    failures: list[dict] = []
    refutations: dict[str, dict] = {}
    episodes = 0
    distinct_inputs: set[str] = set()
    output_disagreements = 0
    for seed in seeds:
        full = {
            mode: ADAPTER.generate(seed, {"output_mode": mode}, 6, 4)
            for mode in FAMILY.MODES
        }
        base_inputs = [p["input"] for p in full[FAMILY.MODES[0]]["train"] + full[FAMILY.MODES[0]]["test"]]
        other_inputs = [p["input"] for p in full[FAMILY.MODES[1]]["train"] + full[FAMILY.MODES[1]]["test"]]
        if base_inputs != other_inputs:
            failures.append({"seed": seed, "failure": "setting-dependent inputs"})
        distinct_inputs.update(json.dumps(grid, separators=(",", ":")) for grid in base_inputs)
        for split in ("train", "test"):
            for left, right in zip(full[FAMILY.MODES[0]][split], full[FAMILY.MODES[1]][split]):
                output_disagreements += left["output"] != right["output"]
        for demos in demo_counts:
            for mode in FAMILY.MODES:
                episodes += 1
                episode = ADAPTER.generate(seed, {"output_mode": mode}, demos, 4)
                if episode["train"] != full[mode]["train"][:demos] or episode["test"] != full[mode]["test"]:
                    failures.append({"seed": seed, "demos": demos, "mode": mode, "failure": "prefix instability"})
                survivors = FAMILY.teaching_survivors(episode["train"])
                if survivors != [mode]:
                    failures.append({"seed": seed, "demos": demos, "mode": mode,
                                     "failure": "declared setting not uniquely identified", "survivors": survivors})
                holes = FAMILY.finite_rival_holes(episode["train"], episode["test"], mode)
                failures.extend({"seed": seed, "demos": demos, "mode": mode, **hole} for hole in holes)
                for name, rival in FAMILY.RIVAL_SOLVERS.items():
                    if name in refutations:
                        continue
                    for index, pair in enumerate(episode["train"]):
                        if rival(pair["input"]) != pair["output"]:
                            refutations[name] = {"seed": seed, "demos": demos, "mode": mode,
                                                 "split": "train", "pair_index": index}
                            break
    stress = FAMILY.episode_inputs(31)["test"][-1]
    boxed = FAMILY.solve(stress, "component_boxes")
    return {
        "schema": "bf47583ab6e3-parametric-self-audit-v1",
        "status": "passed" if not failures else "failed",
        "episodes_checked": episodes,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": 4,
        "distinct_input_serializations": len(distinct_inputs),
        "cross_setting_pair_disagreements": output_disagreements,
        "finite_rivals": sorted(FAMILY.RIVAL_SOLVERS),
        "refutation_witnesses": refutations,
        "failures": failures,
        "boundary": {
            "grid": [len(stress), len(stress[0])],
            "seed_count": len(FAMILY.seed_cells(stress)),
            "canonical_nonzero": sum(v != 0 for row in FAMILY.solve(stress, "plus_union") for v in row),
            "component_boxes_nonzero": sum(v != 0 for row in boxed for v in row),
        },
        "limits": "Finite named rivals, seeds, and counts only; no universal uniqueness or learning-gain claim.",
    }


def native_probe() -> dict:
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    jobs = [
        {"seed": seed, "settings": {"output_mode": mode}, "demos": 2, "queries": 4}
        for mode in FAMILY.MODES
        for seed in (0, 17)
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    return {
        "racket": result["racket"],
        "racket_evaluations": result["racket_evaluations"],
        "jobs": jobs,
        "checks": result["checks"],
        "episode_sha256": [
            hashlib.sha256(json.dumps(ep, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            for ep in result["episodes"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = finite_audit()
    report["native_probe"] = native_probe()
    report["passed"] = (
        report["status"] == "passed"
        and report["native_probe"]["racket"].get("backend") == "racket"
        and report["native_probe"]["racket"].get("protected") is True
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "passed": report["passed"],
        "episodes_checked": report["episodes_checked"],
        "distinct_inputs": report["distinct_input_serializations"],
        "racket_evaluations": report["native_probe"]["racket_evaluations"],
        "failures": len(report["failures"]),
        "boundary": report["boundary"],
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

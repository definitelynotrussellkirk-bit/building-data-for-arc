"""Bounded protected-Racket self-audit for the crop-perimeter family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _real_evaluator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def _load_family():
    path = HERE / "family.py"
    spec = importlib.util.spec_from_file_location("audit_26_family", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(out: Path) -> dict:
    family = _load_family()
    seeds = (0, 17, 91)
    racket_candidates = (
        "crop_only",
        "highlight_perimeter_mode",
        "highlight_global_mode",
        "highlight_first_nonzero",
    )
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    evaluations = 0
    jobs = []
    first_disagreements = {}
    try:
        programs = {name: family.rival_program(name) for name in racket_candidates}
        for seed in seeds:
            for setting in family.BORDER_RULES:
                episode = family.generate_episode(seed, setting, demos=2, queries=4)
                python_survivors = family.teaching_survivors(episode["train"])
                if python_survivors != [setting]:
                    raise AssertionError((seed, setting, python_survivors))
                racket_survivors = []
                for name, program in programs.items():
                    survives = True
                    for pair_index, pair in enumerate(episode["train"]):
                        actual = apply(program, pair["input"])
                        evaluations += 1
                        expected_mirror = family.evaluate_candidate(pair["input"], name)
                        if actual != expected_mirror:
                            raise AssertionError(("mirror mismatch", seed, setting, name, pair_index))
                        if actual != pair["output"]:
                            survives = False
                            first_disagreements.setdefault(
                                f"{setting}:{name}",
                                {"seed": seed, "split": "train", "pair_index": pair_index},
                            )
                    if survives:
                        racket_survivors.append(name)
                if racket_survivors != [setting]:
                    raise AssertionError(("racket survivors", seed, setting, racket_survivors))
                for pair_index, pair in enumerate(episode["test"]):
                    actual = apply(programs[setting], pair["input"])
                    evaluations += 1
                    if actual != pair["output"]:
                        raise AssertionError(("query label", seed, setting, pair_index))
                jobs.append(
                    {
                        "seed": seed,
                        "settings": {"border_rule": setting},
                        "demos": 2,
                        "queries": 4,
                        "python_survivors": python_survivors,
                        "racket_survivors": racket_survivors,
                        "has_30x30_query": any(
                            len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                            for pair in episode["test"]
                        ),
                    }
                )
    finally:
        bridge.close()
    report = {
        "schema": "arcpuzzles-parametric-bounded-self-audit-v1",
        "task_id": family.TASK_ID,
        "status": "passed",
        "seeds": list(seeds),
        "jobs": jobs,
        "racket": identity,
        "racket_evaluations": evaluations,
        "racket_candidates": list(racket_candidates),
        "python_candidates": list(family.CANDIDATE_RULES),
        "first_disagreements": first_disagreements,
        "limits": "Finite named-rival audit; not a proof of universal uniqueness.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out)
    print(json.dumps({"status": report["status"], "jobs": len(report["jobs"]),
                      "racket_evaluations": report["racket_evaluations"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

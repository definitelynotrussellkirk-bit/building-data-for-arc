"""Bounded authoring audit for the 60baf0d49ed5 native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "60baf0d49ed5"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared" / "runtime")]

from arcpuzzles.parametric_worker import evaluate_contract  # noqa: E402
from reviewer_support import public_challenge_bytes  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


adapter = _load("_audit_adapter_60baf0d49ed5", HERE / "adapter.py")
generator = _load("_audit_generator_60baf0d49ed5", HERE.parents[1] / "generator.py")
SETTINGS = ({"application_mode": "direct"}, {"application_mode": "repeat_transform"})


def _projection(episode):
    full = json.loads(public_challenge_bytes(episode))
    first = json.loads(public_challenge_bytes({
        "train": episode["train"],
        "test": [episode["test"][0]],
        "settings": {"application_mode": "private"},
        "program_solution": "private",
    }))
    return {
        "settings_hidden": "settings" not in full and "settings" not in first,
        "program_hidden": "program_solution" not in full and "program_solution" not in first,
        "query_outputs_hidden": all("output" not in pair for pair in full["test"] + first["test"]),
        "first_turn_one_query": len(first["test"]) == 1,
        "first_turn_matches": first["test"][0]["input"] == full["test"][0]["input"],
    }


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(out: Path, seeds: int) -> dict:
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    jobs = 0
    pairs = 0
    projections = {key: True for key in _projection(adapter.generate(0, SETTINGS[0], 2, 1))}
    operation_sets = []
    for seed in range(seeds):
        for demos in range(2, 7):
            episodes = [adapter.generate(seed, setting, demos, 4) for setting in SETTINGS]
            repeats = [adapter.generate(seed, setting, demos, 4) for setting in SETTINGS]
            if episodes != repeats:
                raise AssertionError("generation is not deterministic")
            visible = [[p["input"] for p in e["train"] + e["test"]] for e in episodes]
            if visible[0] != visible[1]:
                raise AssertionError("settings changed visible inputs")
            if len({json.dumps(g, separators=(",", ":")) for g in visible[0]}) != demos + 4:
                raise AssertionError("duplicate visible inputs")
            for setting, episode in zip(SETTINGS, episodes):
                if episode["certificate"]["surviving_settings"] != [setting]:
                    raise AssertionError((seed, demos, setting, episode["certificate"]))
                if episode["certificate"]["ambiguous_rivals"]:
                    raise AssertionError((seed, demos, setting, episode["certificate"]))
                mode = setting["application_mode"]
                if any(p["output"] != adapter.transform(p["input"], mode) for p in episode["train"] + episode["test"]):
                    raise AssertionError("Python label mismatch")
                for q in range(1, 5):
                    prefix = adapter.generate(seed, setting, demos, q)
                    if [p["input"] for p in prefix["test"]] != [p["input"] for p in episode["test"][:q]]:
                        raise AssertionError("query prefix instability")
                stress = [p["input"] for p in episode["test"] if (len(p["input"]), len(p["input"][0])) == (9, 29)]
                if len(stress) != 1 or sum(cell != 0 for row in stress[0] for cell in row) < 90:
                    raise AssertionError("missing substantive 9x29 domain maximum")
                current = _projection(episode)
                projections = {k: projections[k] and current[k] for k in projections}
                jobs += 1
                pairs += demos + 4
            operations = [adapter.infer_transform(pair["input"]) for pair in episodes[0]["train"]]
            if len(set(operations)) < min(demos, 5):
                raise AssertionError("demonstrations do not vary inferred operations")
            operation_sets.append(operations)
    if not all(projections.values()):
        raise AssertionError(projections)

    # Reproduce the old exact-control defect and prove the repaired controls vary output.
    controls = []
    for palette in ("warm", "cool"):
        for count in (1, 3):
            grid = generator.generate(7, 0, palette_kind=palette, n_distinct_colors=count)
            observed = sorted({cell for row in grid for cell in row if cell not in (0, 9)})
            if len(observed) != count or not set(observed) <= set(generator.PALETTES[palette]):
                raise AssertionError((palette, count, observed))
            controls.append({"palette": palette, "requested": count, "observed": observed})

    contract = json.loads((HERE / "promotion.json").read_text())
    racket_jobs = [
        {"seed": seed, "settings": setting, "demos": 3, "queries": 4}
        for setting in SETTINGS for seed in (0, 17)
    ]
    executed = evaluate_contract(ROOT, TASK, contract, racket_jobs)
    if executed["racket"].get("backend") != "racket" or executed["racket"].get("protected") is not True:
        raise AssertionError("protected Racket unavailable")
    direct = next(e for e in executed["episodes"] if e["seed"] == 0 and e["settings"] == SETTINGS[0])
    repeated = next(e for e in executed["episodes"] if e["seed"] == 0 and e["settings"] == SETTINGS[1])
    if direct["test"][0]["input"] != repeated["test"][0]["input"] or direct["test"][0]["output"] == repeated["test"][0]["output"]:
        raise AssertionError("retained matched-input case does not distinguish settings")

    source_paths = [
        HERE / "adapter.py",
        HERE / "audit.py",
        HERE / "canonical.rkt",
        HERE / "native.py",
        HERE / "promotion.json",
        HERE / "repeat_transform.rkt",
        HERE.parents[1] / "generator.py",
        HERE.parents[1] / "tests" / "test_parametric_60.py",
    ]
    sources = {path.relative_to(ROOT).as_posix(): _sha(path) for path in source_paths}
    report = {
        "schema": "arcpuzzles-60baf0d49ed5-self-audit-v1",
        "status": "passed",
        "task_id": TASK,
        "scope": f"{seeds} seeds x 5 demo counts x 2 settings plus four protected-Racket jobs",
        "limits": "Finite authored rivals and seeds only; no universal uniqueness or training-gain claim.",
        "sources": sources,
        "structural": {
            "seeds": seeds,
            "demo_counts": [2, 3, 4, 5, 6],
            "settings": SETTINGS,
            "jobs": jobs,
            "visible_pairs": pairs,
            "projection": projections,
            "control_checks": controls,
            "operation_sets_sample": operation_sets[:5],
            "max_scene": [9, 29],
            "why_not_30x30": "three square SxS panels plus two divider columns require width=3S+2, so S=9 yields the largest legal <=30 canvas, 9x29",
        },
        "racket": executed["racket"],
        "racket_dry_run": {
            "jobs": racket_jobs,
            "checks": executed["checks"],
            "evaluations": executed["racket_evaluations"],
            "program_sha256": {json.dumps(e["settings"], sort_keys=True): e["program_sha256"] for e in executed["episodes"]},
        },
        "retained_matched_case": {
            "settings": repeated["settings"],
            "program": repeated["program"],
            "input": repeated["test"][0]["input"],
            "output": repeated["test"][0]["output"],
            "counterfactual_output": direct["test"][0]["output"],
        },
        "training_admitted": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out, args.seeds)
    print(json.dumps({"status": report["status"], "jobs": report["structural"]["jobs"], "racket_evaluations": report["racket_dry_run"]["evaluations"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

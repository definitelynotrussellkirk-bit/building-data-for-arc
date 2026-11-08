"""Finite self-audit for the component-motion parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK = "483682b75e12"
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


prototype = _load("_component_motion_audit_prototype", HERE / "prototype.py")
adapter = _load("_component_motion_audit_adapter", HERE / "adapter.py")


def _sha(value) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(body).hexdigest()


def _projection_checks(episode):
    full = json.loads(public_challenge_bytes(episode))
    first = json.loads(public_challenge_bytes({
        "train": episode["train"],
        "test": [episode["test"][0]],
        "settings": {"motion_mode": "private"},
        "program_solution": "private",
    }))
    return {
        "settings_hidden": "settings" not in full and "settings" not in first,
        "program_hidden": "program_solution" not in full and "program_solution" not in first,
        "query_outputs_hidden": all("output" not in pair for pair in full["test"] + first["test"]),
        "first_turn_has_one_query": len(first["test"]) == 1,
        "first_turn_input_matches": first["test"][0]["input"] == full["test"][0]["input"],
    }


def run(output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    structural_jobs = 0
    visible_pairs = 0
    rival_checks = 0
    query_disagreements = 0
    thirty = 0
    projection = {
        "settings_hidden": True,
        "program_hidden": True,
        "query_outputs_hidden": True,
        "first_turn_has_one_query": True,
        "first_turn_input_matches": True,
    }
    for seed in range(32):
        for demos in range(2, 7):
            by_mode = {}
            for mode in prototype.MODES:
                episode = adapter.generate(seed, {"motion_mode": mode}, demos, 4)
                by_mode[mode] = episode
                certificate = prototype.lesson_certificate(episode, mode)
                if certificate["setting_survivors"] != [mode] or certificate["rival_survivors"]:
                    raise AssertionError((seed, demos, mode, certificate))
                structural_jobs += 1
                visible_pairs += demos + 4
                rival_checks += certificate["rivals_checked"]
                query_disagreements += certificate["query_disagreements"]
                facts = prototype.scene_facts(episode["test"][3]["input"])
                if (facts["height"], facts["width"]) != (30, 30):
                    raise AssertionError("fourth query lost 30x30 stress")
                thirty += 1
                current = _projection_checks(episode)
                projection = {key: projection[key] and current[key] for key in projection}
            own = by_mode["own_size"]
            alt = by_mode["complement_to_largest"]
            for split in ("train", "test"):
                if [p["input"] for p in own[split]] != [p["input"] for p in alt[split]]:
                    raise AssertionError("setting changed visible inputs")
    if not all(projection.values()):
        raise AssertionError(projection)

    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"motion_mode": mode}, "demos": 3, "queries": 4}
        for mode in prototype.MODES for seed in (0, 17)
    ]
    executed = evaluate_contract(ROOT, TASK, contract, jobs)
    if executed["racket"].get("backend") != "racket" or executed["racket"].get("protected") is not True:
        raise AssertionError("protected Racket unavailable")
    episodes = executed["episodes"]
    own = next(e for e in episodes if e["seed"] == 0 and e["settings"]["motion_mode"] == "own_size")
    alt = next(e for e in episodes if e["seed"] == 0 and e["settings"]["motion_mode"] == "complement_to_largest")
    if own["test"][0]["input"] != alt["test"][0]["input"] or own["test"][0]["output"] == alt["test"][0]["output"]:
        raise AssertionError("retained matched-input case does not distinguish settings")

    sources = {}
    for name in ("adapter.py", "audit.py", "canonical.rkt", "complement_to_largest.rkt",
                 "promotion.json", "prototype.py"):
        path = HERE / name
        sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "schema": "483682b75e12-parametric-self-audit-v1",
        "status": "passed",
        "task_id": TASK,
        "scope": "finite two-setting and twelve-rival visible-demonstration audit plus protected-Racket native dry run",
        "limits": "Finite authored rivals/seeds only; no universal uniqueness or measured training-gain claim.",
        "sources": sources,
        "structural": {
            "seeds": 32,
            "demo_counts": [2, 3, 4, 5, 6],
            "settings": list(prototype.MODES),
            "jobs": structural_jobs,
            "visible_pairs": visible_pairs,
            "declared_rival_checks": rival_checks,
            "query_setting_disagreements": query_disagreements,
            "actual_30x30_queries": thirty,
            "projection": projection,
        },
        "racket": executed["racket"],
        "racket_dry_run": {
            "jobs": jobs,
            "checks": executed["checks"],
            "evaluations": executed["racket_evaluations"],
            "program_sha256": {e["settings"]["motion_mode"]: e["program_sha256"] for e in episodes},
        },
        "retained_matched_input_case": {
            "seed": 0,
            "split": "test",
            "pair_index": 0,
            "input": own["test"][0]["input"],
            "own_size_output": own["test"][0]["output"],
            "complement_to_largest_output": alt["test"][0]["output"],
            "input_sha256": _sha(own["test"][0]["input"]),
            "own_size_output_sha256": _sha(own["test"][0]["output"]),
            "complement_to_largest_output_sha256": _sha(alt["test"][0]["output"]),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out)
    print(json.dumps({
        "status": report["status"],
        "structural_jobs": report["structural"]["jobs"],
        "declared_rival_checks": report["structural"]["declared_rival_checks"],
        "racket_evaluations": report["racket_dry_run"]["evaluations"],
        "report": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

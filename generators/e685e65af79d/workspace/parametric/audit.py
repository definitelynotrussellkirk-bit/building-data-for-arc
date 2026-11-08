"""Bounded authoring audit for the e685e65af79d native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "e685e65af79d"
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


adapter = _load("_audit_adapter_e685e65af79d", HERE / "adapter.py")
generator = _load("_audit_generator_e685e65af79d", HERE.parents[1] / "generator.py")
SETTINGS = ({"symmetry_closure": "rotational_4"}, {"symmetry_closure": "largest_closure_dihedral"})


def _projection(episode):
    full = json.loads(public_challenge_bytes(episode))
    first = json.loads(public_challenge_bytes({
        "train": episode["train"],
        "test": [episode["test"][0]],
        "settings": {"symmetry_closure": "private"},
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
    for seed in range(seeds):
        for demos in range(2, 7):
            episodes = [adapter.generate(seed, setting, demos, 4) for setting in SETTINGS]
            if episodes != [adapter.generate(seed, setting, demos, 4) for setting in SETTINGS]:
                raise AssertionError("generation is not deterministic")
            visible = [[p["input"] for p in e["train"] + e["test"]] for e in episodes]
            if visible[0] != visible[1]:
                raise AssertionError("settings changed visible inputs")
            if len({json.dumps(g, separators=(",", ":")) for g in visible[0]}) != demos + 4:
                raise AssertionError("duplicate visible inputs")
            for setting, episode in zip(SETTINGS, episodes):
                certificate = episode["certificate"]
                if certificate["surviving_settings"] != [setting] or certificate["ambiguous_rivals"]:
                    raise AssertionError((seed, demos, setting, certificate))
                if setting == SETTINGS[1]:
                    required_rivals = {
                        "fill_each_bbox",
                        "all_dihedral",
                        "first_object_dihedral",
                        "smallest_closure_dihedral",
                        "largest_original_area_dihedral",
                    }
                    if not required_rivals <= set(certificate["tested_rivals"]):
                        raise AssertionError(("missing selector rivals", certificate))
                closure = setting["symmetry_closure"]
                if any(p["output"] != adapter.transform(p["input"], closure) for p in episode["train"] + episode["test"]):
                    raise AssertionError("Python label mismatch")
                for q in range(1, 5):
                    prefix = adapter.generate(seed, setting, demos, q)
                    if [p["input"] for p in prefix["test"]] != [p["input"] for p in episode["test"][:q]]:
                        raise AssertionError("query prefix instability")
                stress = [p["input"] for p in episode["test"] if (len(p["input"]), len(p["input"][0])) == (30, 30)]
                if len(stress) != 1:
                    raise AssertionError("missing 30x30 stress query")
                facts = adapter.analyze(stress[0])
                if (
                    facts["component_count"] != 8
                    or facts["nonzero_cells"] < 80
                    or facts["selected_object_index"] in (None, 0)
                    or facts["rotational_closure_areas"].count(max(facts["rotational_closure_areas"])) != 1
                ):
                    raise AssertionError(facts)
                current = _projection(episode)
                projections = {k: projections[k] and current[k] for k in projections}
                jobs += 1
                pairs += demos + 4
    if not all(projections.values()):
        raise AssertionError(projections)

    # Reproduce the old seed-59 surface and ensure every ordinary sample now refutes half-turn-only.
    base_checks = []
    for sample_index in range(4):
        grid = generator.generate(59, sample_index)
        components = generator._components(grid)
        diagnostic = sum(
            len(generator._rotation_closure(cells)) > len(generator._half_turn_closure(cells))
            for _color, cells, _bbox in components
        )
        if diagnostic < 1 or generator.self_check(grid) != []:
            raise AssertionError((sample_index, diagnostic, generator.self_check(grid)))
        base_checks.append({"sample_index": sample_index, "objects": len(components), "diagnostic_objects": diagnostic})
    forced = generator.generate(11, 0, n_blobs=2, blob_shape_idx=3)
    if any(generator._norm(cells) != generator._norm(generator._SHAPE_BANK[3]) for _color, cells, _bbox in generator._components(forced)):
        raise AssertionError("blob_shape_idx override is not exact")

    contract = json.loads((HERE / "promotion.json").read_text())
    racket_jobs = [
        {"seed": seed, "settings": setting, "demos": 3, "queries": 4}
        for setting in SETTINGS for seed in (0, 17)
    ]
    executed = evaluate_contract(ROOT, TASK, contract, racket_jobs)
    if executed["racket"].get("backend") != "racket" or executed["racket"].get("protected") is not True:
        raise AssertionError("protected Racket unavailable")
    rotational = next(e for e in executed["episodes"] if e["seed"] == 0 and e["settings"] == SETTINGS[0])
    routed = next(e for e in executed["episodes"] if e["seed"] == 0 and e["settings"] == SETTINGS[1])
    if rotational["test"][0]["input"] != routed["test"][0]["input"] or rotational["test"][0]["output"] == routed["test"][0]["output"]:
        raise AssertionError("retained matched-input case does not distinguish settings")
    routed_facts = adapter.analyze(routed["test"][0]["input"])
    if routed_facts["selected_object_index"] in (None, 0):
        raise AssertionError(("selector witness is not diagnostic", routed_facts))

    source_paths = [
        HERE / "adapter.py",
        HERE / "audit.py",
        HERE / "canonical.rkt",
        HERE / "first_object_dihedral.rkt",
        HERE / "largest_closure_dihedral.rkt",
        HERE / "native.py",
        HERE / "promotion.json",
        HERE.parents[1] / "generator.py",
        HERE.parents[1] / "tests" / "test_parametric_e685.py",
    ]
    sources = {path.relative_to(ROOT).as_posix(): _sha(path) for path in source_paths}
    report = {
        "schema": "arcpuzzles-e685e65af79d-self-audit-v2",
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
            "base_seed_59_checks": base_checks,
            "max_scene": [30, 30],
            "max_scene_objects": 8,
        },
        "racket": executed["racket"],
        "racket_dry_run": {
            "jobs": racket_jobs,
            "checks": executed["checks"],
            "evaluations": executed["racket_evaluations"],
            "program_sha256": {json.dumps(e["settings"], sort_keys=True): e["program_sha256"] for e in executed["episodes"]},
        },
        "retained_matched_case": {
            "settings": routed["settings"],
            "program": routed["program"],
            "input": routed["test"][0]["input"],
            "output": routed["test"][0]["output"],
            "canonical_output": rotational["test"][0]["output"],
            "intermediate": routed_facts,
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

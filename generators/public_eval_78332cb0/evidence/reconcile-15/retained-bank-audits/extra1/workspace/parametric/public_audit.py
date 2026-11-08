"""Verify source-bound sequential public views for an unapproved preflight."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = next(p for p in HERE.parents if (p / "src/arcpuzzles/review_public_creation.py").is_file())
TASK = HOME.name


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("_public_audit_" + TASK, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _bound(preflight: Path):
    receipt = json.loads(preflight.read_text())
    if (receipt.get("schema") != "arcpuzzles-public-eval-authoring-preflight-v1"
            or receipt.get("status") != "passed" or receipt.get("task_id") != TASK
            or receipt.get("owner_accepted") is not False):
        raise ValueError("need this task's passing unapproved authoring preflight")
    for row in receipt["source_binding"]["files"]:
        path = ROOT / row["path"]
        if not path.is_file() or path.is_symlink() or _sha(path.read_bytes()) != row["sha256"]:
            raise ValueError("preflight source binding drift: " + row["path"])
    for name, digest in receipt["evidence_sha256"].items():
        if _sha((preflight.parent / name).read_bytes()) != digest:
            raise ValueError("preflight evidence drift: " + name)
    execution = json.loads((preflight.parent / "execution.json").read_text())
    return receipt, execution


def run(preflight: Path, out: Path, presentation_seed: int = 41):
    if out.exists() or out.is_symlink():
        raise FileExistsError("choose a fresh output path")
    if type(presentation_seed) is not int:
        raise ValueError("presentation_seed must be an exact integer")
    receipt, execution = _bound(preflight)
    adapter = _load_adapter()
    rows = []
    visible_hashes = set()
    private_mutations = 0
    positive_controls = 0
    for episode_index, source in enumerate(execution["episodes"]):
        full = adapter.present(source["seed"], source["settings"], len(source["train"]), 4,
                               presentation_seed=presentation_seed)
        one = adapter.present(source["seed"], source["settings"], len(source["train"]), 1,
                              presentation_seed=presentation_seed)
        if full["public"][:1] != one["public"]:
            raise ValueError("first public turn depends on requested total query count")
        if full["private"]["source_pairs"] != source["test"]:
            raise ValueError("private source pairs differ from protected preflight episode")
        if len(full["public"]) != 4 or sorted(full["private"]["source_indices"]) != list(range(4)):
            raise ValueError("expected a complete independently shuffled four-query bank")
        for turn, view in enumerate(full["public"]):
            if set(view) != {"train", "test"} or len(view["test"]) != 1 or set(view["test"][0]) != {"input"}:
                raise ValueError("public view leaks private fields")
            digest = _sha(_raw(view))
            if digest in visible_hashes:
                raise ValueError("duplicate visible public view")
            visible_hashes.add(digest)
            rows.append({"episode_index": episode_index, "turn": turn, "sha256": digest,
                         "source_index": full["private"]["source_indices"][turn]})
        baseline = copy.deepcopy(full["public"])
        variants = []
        for field, value in (("settings", {"private": "changed"}),
                             ("program", "private-program"),
                             ("seed", source["seed"] + 999),
                             ("presentation_seed", presentation_seed + 999)):
            changed = copy.deepcopy(full)
            changed["private"][field] = value
            variants.append(changed)
        changed = copy.deepcopy(full)
        changed["private"]["source_pairs"][0]["output"] = [[9]]
        variants.append(changed)
        changed = copy.deepcopy(full)
        changed["private"]["source_pairs"].append({"input": [[1]], "output": [[2]]})
        variants.append(changed)
        for changed in variants:
            if changed["public"] != baseline:
                raise ValueError("private field mutation changed visible bytes")
            private_mutations += 1
        positive = copy.deepcopy(full)
        positive["public"][0]["test"][0]["input"][0][0] = (positive["public"][0]["test"][0]["input"][0][0] + 1) % 10
        if positive["public"] == baseline:
            raise ValueError("visible positive control did not change")
        positive_controls += 1
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "arcpuzzles-unapproved-public-authoring-projection-audit-v1",
        "task_id": TASK,
        "status": "passed",
        "owner_accepted": False,
        "training_admitted": False,
        "presentation_seed": presentation_seed,
        "episodes": len(execution["episodes"]),
        "views": len(rows),
        "private_field_mutations": private_mutations,
        "positive_controls": positive_controls,
        "views_manifest": rows,
        "source_binding": receipt["source_binding"],
        "limits": "Serialized one-query views from protected authoring episodes; no native qualification, owner acceptance, or training admission.",
    }
    out.write_bytes(_raw(report))
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--presentation-seed", type=int, default=41)
    args = parser.parse_args()
    result = run(args.preflight, args.out, args.presentation_seed)
    print(json.dumps({k: result[k] for k in ("status", "episodes", "views", "private_field_mutations", "positive_controls")}, sort_keys=True))

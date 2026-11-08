#!/usr/bin/env python3
"""Bounded sampler and qualified-evidence audit for 252ff772a276."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_audit_252ff772a276_impl", HERE / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load prototype")
IMPL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPL)


def _write(path: Path, value) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _visible(episode, index: int):
    return {
        "train": episode["train"],
        "test": [{"input": episode["test"][index]["input"]}],
    }


def sampler_audit(seeds: int, demo_counts: tuple[int, ...]) -> dict:
    rows = []
    failures = []
    inputs_checked = 0
    large_checked = 0
    for seed in range(seeds):
        for demos in demo_counts:
            generated = {
                scope: IMPL.generate(seed, {"fill_scope": scope}, demos, 4)
                for scope in IMPL.SETTINGS
            }
            base_inputs = [pair["input"] for split in ("train", "test") for pair in generated[IMPL.SETTINGS[0]][split]]
            for scope in IMPL.SETTINGS[1:]:
                other_inputs = [pair["input"] for split in ("train", "test") for pair in generated[scope][split]]
                if other_inputs != base_inputs:
                    failures.append(f"setting-dependent inputs: seed={seed} demos={demos}")
            for scope, episode in generated.items():
                report = IMPL.audit_episode(episode, scope)
                if report["harmful_survivors"]:
                    failures.append(f"harmful rivals: seed={seed} demos={demos} scope={scope}: {report['harmful_survivors']}")
                if any(pair["output"] != IMPL.apply_rule(pair["input"], scope) for split in ("train", "test") for pair in episode[split]):
                    failures.append(f"python label mismatch: seed={seed} demos={demos} scope={scope}")
                large = IMPL.analyze(episode["test"][-1]["input"])
                if (large["height"], large["width"]) != (30, 30) or large["winner_interior_area"] < 120:
                    failures.append(f"weak 30x30 case: seed={seed} demos={demos} scope={scope}")
                large_checked += 1
                rows.append({"seed": seed, "demos": demos, "scope": scope, **report})
            inputs_checked += len(base_inputs)
    return {
        "schema": "252ff772a276-sampler-audit-v1",
        "status": "failed" if failures else "passed",
        "seeds": seeds,
        "demo_counts": list(demo_counts),
        "episodes_checked": len(rows),
        "inputs_checked": inputs_checked,
        "substantive_30x30_checks": large_checked,
        "finite_rivals": list(IMPL.RIVALS),
        "rows": rows,
        "failures": failures,
        "limits": "Finite named rivals and sampled seeds only; this is not universal uniqueness evidence.",
    }


def qualification_audit(path: Path, public_dir: Path | None) -> dict:
    qualification = json.loads(path.read_text())
    execution_path = path.parent / qualification["execution"]["path"]
    raw_execution = execution_path.read_bytes()
    if hashlib.sha256(raw_execution).hexdigest() != qualification["execution"]["sha256"]:
        raise ValueError("qualification execution hash mismatch")
    execution = json.loads(raw_execution)
    failures = []
    rows = []
    public_files = []
    if public_dir is not None:
        if public_dir.exists() or public_dir.is_symlink():
            raise FileExistsError(public_dir)
        public_dir.mkdir(parents=True)
    for episode in execution["episodes"]:
        scope = episode["settings"]["fill_scope"]
        report = IMPL.audit_episode(episode, scope)
        if report["harmful_survivors"]:
            failures.append(f"qualified harmful rivals: seed={episode['seed']} scope={scope}")
        for split in ("train", "test"):
            for pair in episode[split]:
                if pair["output"] != IMPL.apply_rule(pair["input"], scope):
                    failures.append(f"qualified Python/Racket mismatch: seed={episode['seed']} scope={scope} split={split}")
        rows.append({"seed": episode["seed"], "settings": episode["settings"], **report})
        if public_dir is not None:
            for index in range(len(episode["test"])):
                visible = _visible(episode, index)
                payload = public_challenge_bytes(visible)
                identifier = public_challenge_id(visible)
                target = public_dir / f"{identifier}.json"
                if target.exists() and target.read_bytes() != payload:
                    raise ValueError("public identifier collision")
                target.write_bytes(payload)
                public_files.append({
                    "path": str(target),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "seed_private": episode["seed"],
                    "settings_private": episode["settings"],
                    "query_index_private": index,
                })
    return {
        "schema": "252ff772a276-qualified-audit-v1",
        "status": "failed" if failures else "passed",
        "qualification_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "execution_sha256": hashlib.sha256(raw_execution).hexdigest(),
        "racket": execution["racket"],
        "racket_evaluations": execution["racket_evaluations"],
        "episodes_checked": len(rows),
        "rows": rows,
        "public_files": public_files,
        "failures": failures,
        "limits": "Protected-Racket-qualified labels, but only named finite rivals and qualified jobs are audited.",
    }


def _demo_counts(raw: str) -> tuple[int, ...]:
    values = tuple(int(item) for item in raw.split(",") if item)
    if not values or any(value < IMPL.MIN_DEMOS or value > IMPL.MAX_DEMOS for value in values):
        raise argparse.ArgumentTypeError("demo counts must be in 2..6")
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--demo-counts", type=_demo_counts, default=(2, 3, 6))
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--public-dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.seeds < 1:
            raise ValueError("seeds must be positive")
        if args.qualification is None and args.public_dir is not None:
            raise ValueError("--public-dir requires --qualification")
        report = qualification_audit(args.qualification, args.public_dir) if args.qualification else sampler_audit(args.seeds, args.demo_counts)
        _write(args.out, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "passed" else 1
    except Exception as error:
        report = {"schema": "252ff772a276-audit-error-v1", "status": "failed", "error": type(error).__name__, "message": str(error)}
        if not args.out.exists():
            _write(args.out, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

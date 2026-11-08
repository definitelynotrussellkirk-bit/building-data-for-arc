#!/usr/bin/env python3
"""Bounded teaching/public-projection audit for the marker-scan family.

Without ``--qualification`` this attacks sampler and finite-rival behavior on a
small seed/count grid.  With a native qualification it reuses its protected-
Racket-verified episodes, checks the same finite rivals against those labels,
and can materialize hash-named public challenges with all four query inputs and
no private setting, program, seed, or query answer.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id

_HOME = Path(__file__).resolve().parent
_IMPL_PATH = _HOME / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_0a9e3d364bb3_parametric_audit_impl", _IMPL_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_IMPL_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _episode_key(episode: dict[str, Any]) -> str:
    return json.dumps(episode["settings"], sort_keys=True, separators=(",", ":"))


def _public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": episode["train"],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def run_sampler(*, seeds: int, demo_counts: tuple[int, ...], queries: int) -> dict[str, Any]:
    failures = []
    requests = 0
    unique_inputs: set[str] = set()
    for seed in range(seeds):
        for demos in demo_counts:
            episodes = {
                setting: _IMPL.generate(seed, {"marker_scan": setting}, demos, queries)
                for setting in _IMPL.SETTINGS
            }
            requests += len(episodes)
            left, right = (episodes[setting] for setting in _IMPL.SETTINGS)
            left_inputs = [pair["input"] for split in ("train", "test") for pair in left[split]]
            right_inputs = [pair["input"] for split in ("train", "test") for pair in right[split]]
            if left_inputs != right_inputs:
                failures.append(
                    {"kind": "setting_dependent_inputs", "seed": seed, "demos": demos}
                )
            for grid in left_inputs:
                unique_inputs.add(json.dumps(grid, separators=(",", ":")))
            for setting, episode in episodes.items():
                audit = _IMPL.audit_episode(episode, setting)
                if audit["harmful_survivors"]:
                    failures.append(
                        {
                            "kind": "harmful_finite_rival",
                            "seed": seed,
                            "demos": demos,
                            "setting": setting,
                            "survivors": audit["harmful_survivors"],
                        }
                    )
    return {
        "schema": "0a9e3d364bb3-parametric-sampler-audit-v1",
        "status": "failed" if failures else "passed",
        "seed_count": seeds,
        "demo_counts": list(demo_counts),
        "queries": queries,
        "settings": list(_IMPL.SETTINGS),
        "requests": requests,
        "unique_inputs": len(unique_inputs),
        "failures": failures,
        "limits": "Finite named rivals and sampled seeds/counts only; no universal uniqueness claim.",
    }


def run_qualification(
    qualification_path: Path,
    *,
    public_dir: Path | None,
) -> dict[str, Any]:
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    if qualification.get("schema") != "arcpuzzles-parametric-qualification-v1":
        raise ValueError("not a native parametric qualification")
    execution_ref = qualification.get("execution", {})
    execution_path = qualification_path.parent / execution_ref.get("path", "")
    raw_execution = execution_path.read_bytes()
    if hashlib.sha256(raw_execution).hexdigest() != execution_ref.get("sha256"):
        raise ValueError("qualification execution hash differs")
    execution = json.loads(raw_execution)
    if (
        qualification.get("status") != "qualified"
        or execution.get("racket", {}).get("backend") != "racket"
        or execution.get("racket", {}).get("protected") is not True
    ):
        raise ValueError("qualification is not protected-Racket qualified")

    rows = []
    failures = []
    first_by_setting: dict[str, dict[str, Any]] = {}
    for episode in execution.get("episodes", []):
        setting = episode.get("settings", {}).get("marker_scan")
        if setting not in _IMPL.SETTINGS:
            failures.append({"kind": "unexpected_setting", "settings": episode.get("settings")})
            continue
        audit = _IMPL.audit_episode(episode, setting)
        rows.append(
            {
                "seed": episode["seed"],
                "settings": episode["settings"],
                "program_sha256": episode["program_sha256"],
                "demos": len(episode["train"]),
                "queries": len(episode["test"]),
                "survivors": audit["survivors"],
                "harmful_survivors": audit["harmful_survivors"],
            }
        )
        if audit["harmful_survivors"]:
            failures.append(
                {
                    "kind": "harmful_finite_rival",
                    "seed": episode["seed"],
                    "settings": episode["settings"],
                    "survivors": audit["harmful_survivors"],
                }
            )
        first_by_setting.setdefault(_episode_key(episode), episode)

    public_files = []
    if public_dir is not None:
        if public_dir.exists():
            raise FileExistsError(public_dir)
        public_dir.mkdir(parents=True)
        for episode in first_by_setting.values():
            visible = _public_episode(episode)
            payload = public_challenge_bytes(visible)
            identifier = public_challenge_id(visible)
            path = public_dir / f"{identifier}.json"
            path.write_bytes(payload)
            public_files.append(
                {
                    "path": str(path),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "settings_private": episode["settings"],
                    "demos": len(episode["train"]),
                    "queries": len(episode["test"]),
                }
            )

    return {
        "schema": "0a9e3d364bb3-qualified-teaching-audit-v1",
        "status": "failed" if failures else "passed",
        "qualification_sha256": hashlib.sha256(qualification_path.read_bytes()).hexdigest(),
        "execution_sha256": hashlib.sha256(raw_execution).hexdigest(),
        "racket": execution["racket"],
        "racket_evaluations": execution.get("racket_evaluations"),
        "episodes_checked": len(rows),
        "settings": list(_IMPL.SETTINGS),
        "rows": rows,
        "public_files": public_files,
        "failures": failures,
        "limits": "Protected-Racket-qualified labels, but only the named finite rivals and qualified jobs are audited.",
    }


def _positive(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("use a positive integer")
    return parsed


def _demo_counts(value: str) -> tuple[int, ...]:
    result = tuple(int(item) for item in value.split(",") if item)
    if not result or any(not _IMPL.MIN_DEMOS <= item <= _IMPL.MAX_DEMOS for item in result):
        raise argparse.ArgumentTypeError(
            f"demo counts must be comma-separated values in {_IMPL.MIN_DEMOS}..{_IMPL.MAX_DEMOS}"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=_positive, default=8)
    parser.add_argument("--demo-counts", type=_demo_counts, default=(2, 3, 6))
    parser.add_argument("--queries", type=_positive, default=4)
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--public-dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.queries != 4:
        parser.error("this retained audit requires exactly four queries")
    try:
        if args.qualification:
            report = run_qualification(args.qualification, public_dir=args.public_dir)
        else:
            if args.public_dir:
                parser.error("--public-dir requires --qualification")
            report = run_sampler(
                seeds=args.seeds,
                demo_counts=args.demo_counts,
                queries=args.queries,
            )
        _write_json(args.out, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "passed" else 1
    except Exception as error:
        report = {
            "schema": "0a9e3d364bb3-parametric-audit-error-v1",
            "status": "failed",
            "error": type(error).__name__,
            "message": str(error),
        }
        _write_json(args.out, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build and independently verify one proposed episode per path policy."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root


def _load_prototype():
    path = Path(__file__).with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "_db63430eeffa_parametric_prototype_for_verify",
        path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()
ROOT = find_root(__file__)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_verification(
    destination: Path,
    *,
    seed_base: int = 3000,
    root: Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write source-bound private/public evidence and return its summary."""
    if type(seed_base) is not int or seed_base < 0:
        raise ValueError("seed_base must be a nonnegative exact integer")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    active_root = ROOT if root is None else Path(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.tmp-",
            dir=destination.parent,
        )
    )

    try:
        episodes: dict[str, dict[str, Any]] = {}
        verifications: dict[str, dict[str, Any]] = {}
        sequential_witness: dict[str, Any] | None = None
        runtime_identity: dict[str, Any] | None = None
        context = RacketBridge() if bridge is None else nullcontext(bridge)
        with context as active_bridge:
            runtime_identity = active_bridge.runtime_identity
            for index, policy in enumerate(prototype.PATH_POLICIES):
                episode = prototype.build_episode(
                    seed_base + index,
                    policy,
                    root=active_root,
                    bridge=active_bridge,
                )
                verification = prototype.verify_episode(
                    episode,
                    root=active_root,
                    bridge=active_bridge,
                )
                episodes[policy] = episode
                verifications[policy] = verification
            sequential_witness = prototype.build_sequential_dependency_witness(
                episodes["both"]["train"][0]["input"],
                "both",
                root=active_root,
                bridge=active_bridge,
            )

        assert sequential_witness is not None
        private_dir = temp / "private"
        private_dir.mkdir(parents=True)
        for policy, episode in episodes.items():
            _write_json(private_dir / f"episode-{policy}.json", episode)
        public_paths = prototype.write_public_batch(
            episodes.values(),
            temp / "public",
        )
        _write_json(temp / "sequential-dependency.json", sequential_witness)

        generated_count = sum(
            episode["racket_evaluation_count"] for episode in episodes.values()
        )
        verification_count = sum(
            row["racket_evaluation_count"] for row in verifications.values()
        )
        report = {
            "schema": "arcpuzzles-path-policy-prototype-verification-v1",
            "task_id": prototype.TASK_ID,
            "status": "proposed_unapproved",
            "approved": False,
            "passed": (
                all(row["passed"] for row in verifications.values())
                and sequential_witness["differing_cell_count"] > 0
                and sequential_witness["racket"].get("protected") is True
            ),
            "settings_verified": len(episodes),
            "path_policies": list(prototype.PATH_POLICIES),
            "seed_base": seed_base,
            "demonstration_count_per_episode": prototype.DEFAULT_DEMONSTRATION_COUNT,
            "query_count_per_episode": prototype.DEFAULT_QUERY_COUNT,
            "generated_racket_evaluation_count": generated_count,
            "verification_racket_evaluation_count": verification_count,
            "sequential_witness_racket_evaluation_count": 2,
            "total_racket_evaluation_count": generated_count + verification_count + 2,
            "canonical_program_sha256": prototype.CANONICAL_SOURCE_SHA256,
            "prototype_sha256": _sha256(Path(prototype.__file__)),
            "generator_sha256": prototype.GENERATOR_SHA256,
            "runtime_identity": runtime_identity,
            "episodes": {
                policy: {
                    "seed": episode["seed"],
                    "program_sha256": episode["program_sha256"],
                    "public_id": prototype.public_id(episode),
                    "public_filename": prototype.public_filename(episode),
                    "rivals": episode["parameter_rivals"],
                    "shortcut_rivals": episode["shortcut_rivals"],
                    "shortcut_survivors": verifications[policy]["shortcut_survivors"],
                    "dimensions": [
                        list(value)
                        for value in sorted(
                            {
                                (len(pair["input"]), len(pair["input"][0]))
                                for pair in episode["train"] + episode["test"]
                            }
                        )
                    ],
                    "verification": verifications[policy],
                }
                for policy, episode in episodes.items()
            },
            "public_files": sorted(path.name for path in public_paths),
            "sequential_dependency": {
                key: sequential_witness[key]
                for key in (
                    "step_a",
                    "intermediate",
                    "wrong_intermediate",
                    "step_b",
                    "why_b_depends_on_a",
                    "differing_cell_count",
                    "correct_program_sha256",
                    "wrong_intermediate_program_sha256",
                )
            },
            "limits": [
                "This is bounded evidence for three fixed seeds, not proof over every lawful input.",
                "The adapter is qualified separately; this report alone grants no acceptance or training admission.",
                "Public files intentionally omit hidden policy, seed, Racket source, and query answers.",
            ],
        }
        _write_json(temp / "report.json", report)

        evidence_files = sorted(
            path for path in temp.rglob("*") if path.is_file()
        )
        manifest = {
            "schema": "arcpuzzles-path-policy-evidence-manifest-v1",
            "task_id": prototype.TASK_ID,
            "file_count": len(evidence_files),
            "files": [
                {
                    "path": str(path.relative_to(temp)),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
                for path in evidence_files
            ],
        }
        _write_json(temp / "manifest.json", manifest)
        temp.replace(destination)
        return report
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the proposed db63430eeffa path-policy prototype"
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="new evidence directory (must not already exist)",
    )
    parser.add_argument("--seed-base", type=int, default=3000)
    args = parser.parse_args(argv)
    report = run_verification(args.out, seed_base=args.seed_base)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

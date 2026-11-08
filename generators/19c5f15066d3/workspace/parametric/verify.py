#!/usr/bin/env python3
"""Materialize and exact-Racket-verify the proposed proximity-radius episodes."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
TASK_ID = "19c5f15066d3"
REPORT_SCHEMA = "19c5f15066d3-parametric-proximity-radius-v1"


def _load_prototype():
    source = HERE.with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "verify_proximity_radius_prototype_19c5f15066d3", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import prototype from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _public_is_masked(public: dict[str, Any]) -> bool:
    return (
        set(public) == {"train", "test"}
        and bool(public["train"])
        and bool(public["test"])
        and all(set(pair) == {"input", "output"} for pair in public["train"])
        and all(set(pair) == {"input"} for pair in public["test"])
    )


def _sorted_unique_episode_artifacts(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sort pending outputs by visible ID and reject duplicate payload IDs."""
    ids = [row.get("public_challenge_id") for row in rows]
    if any(not isinstance(value, str) or not value for value in ids):
        raise ValueError("episode artifact lacks a visible public challenge ID")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate visible public challenge ID")
    return sorted(rows, key=lambda row: row["public_challenge_id"])


def _source_row(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": _sha_bytes(path.read_bytes()),
        "bytes": path.stat().st_size,
    }


def build_report(out_dir: Path) -> dict[str, Any]:
    """Write bounded private/public evidence and return its report."""
    proto = _load_prototype()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    private_dir = out_dir / "private"
    public_dir = out_dir / "public"
    programs_dir = private_dir / "programs"
    episodes_dir = private_dir / "episodes"
    snapshots_dir = private_dir / "source_snapshot"
    for directory in (programs_dir, episodes_dir, public_dir, snapshots_dir):
        directory.mkdir(parents=True, exist_ok=True)

    source_paths = [
        HERE.with_name("prototype.py"),
        HERE,
        ROOT / f"generators/{TASK_ID}/tests/test_parametric_proximity.py",
        ROOT / f"generators/{TASK_ID}/generator.py",
    ]
    source_rows = []
    for path in source_paths:
        if not path.is_file():
            continue
        source_rows.append(_source_row(path))
        (snapshots_dir / path.name).write_bytes(path.read_bytes())

    programs = {
        radius: proto.materialize_rule(radius, root=ROOT)
        for radius in proto.ALLOWED_PROXIMITY_RADII
    }
    program_rows = []
    for radius, source in programs.items():
        path = programs_dir / f"proximity-radius-{radius}.rkt"
        path.write_text(source + "\n", encoding="utf-8")
        program_rows.append(
            {
                "proximity_radius": radius,
                "path": str(path.relative_to(out_dir)),
                "sha256": _sha_bytes(path.read_bytes()),
                "source_sha256": _sha_bytes(source.encode()),
                "normalized_rule_hash": proto.normalized_program_hash(
                    radius, root=ROOT
                ),
                "is_exact_canonical_source": (
                    radius == proto.DEFAULT_PROXIMITY_RADIUS
                    and source == proto.canonical_source(root=ROOT)
                ),
            }
        )

    canonical_rows = []
    episode_artifacts = []
    unique_input_hashes = set()
    all_racket_exact = True
    all_rival_racket_exact = True
    all_rivals_refuted_by_every_demo = True
    all_queries_setting_sensitive = True
    all_public_challenges_masked = True
    all_public_ids_visible_only = True

    with RacketBridge() as bridge:
        canonical_program = programs[proto.DEFAULT_PROXIMITY_RADIUS]
        for index, pair in enumerate(
            canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        ):
            got = proto.execute_rule(
                canonical_program,
                pair["input"],
                bridge=bridge,
            )
            row = {
                "index": index,
                "input_sha256": _sha_json(pair["input"]),
                "expected_output_sha256": _sha_json(pair["output"]),
                "racket_output_sha256": _sha_json(got),
                "racket_matches_canonical": got == pair["output"],
            }
            canonical_rows.append(row)
            all_racket_exact &= row["racket_matches_canonical"]

        for radius in proto.ALLOWED_PROXIMITY_RADII:
            seed = radius
            episode = proto.make_episode(
                seed,
                proximity_radius=radius,
                n_train=3,
                n_test=4,
                root=ROOT,
            )
            public = proto.public_challenge(episode)
            public_id = public_challenge_id(public)
            public_path = public_dir / f"challenge-{public_id}.json"
            public_bytes = public_challenge_bytes(public)

            private_bytes = (
                json.dumps(episode, indent=2, sort_keys=True) + "\n"
            ).encode()
            private_id = _sha_bytes(private_bytes)
            private_path = episodes_dir / f"episode-{private_id}.json"

            pairs = [
                (split, index, pair)
                for split in ("train", "test")
                for index, pair in enumerate(episode[split])
            ]
            predictions: dict[int, list[Any]] = {}
            for candidate_radius, source in programs.items():
                predictions[candidate_radius] = [
                    proto.execute_rule(source, pair["input"], bridge=bridge)
                    for _split, _index, pair in pairs
                ]

            pair_rows = []
            for pair_offset, (split, index, pair) in enumerate(pairs):
                intended = predictions[radius][pair_offset]
                intended_python = proto.solve(
                    pair["input"], proximity_radius=radius
                )
                intended_exact = (
                    intended == pair["output"] == intended_python
                )
                all_racket_exact &= intended_exact
                unique_input_hashes.add(_sha_json(pair["input"]))

                rival_rows = []
                for rival_radius in proto.ALLOWED_PROXIMITY_RADII:
                    if rival_radius == radius:
                        continue
                    rival_racket = predictions[rival_radius][pair_offset]
                    rival_python = proto.solve(
                        pair["input"], proximity_radius=rival_radius
                    )
                    rival_exact = rival_racket == rival_python
                    rival_differs = rival_racket != pair["output"]
                    all_rival_racket_exact &= rival_exact
                    if split == "train":
                        all_rivals_refuted_by_every_demo &= rival_differs
                    else:
                        all_queries_setting_sensitive &= rival_differs
                    rival_rows.append(
                        {
                            "proximity_radius": rival_radius,
                            "racket_output_sha256": _sha_json(rival_racket),
                            "python_output_sha256": _sha_json(rival_python),
                            "racket_matches_python": rival_exact,
                            "differs_from_intended": rival_differs,
                        }
                    )

                pair_rows.append(
                    {
                        "split": split,
                        "index": index,
                        "input_sha256": _sha_json(pair["input"]),
                        "stored_output_sha256": _sha_json(pair["output"]),
                        "intended_racket_output_sha256": _sha_json(intended),
                        "intended_python_output_sha256": _sha_json(
                            intended_python
                        ),
                        "intended_racket_exact": intended_exact,
                        "rivals": rival_rows,
                    }
                )

            public_masked = _public_is_masked(public)
            public_id_visible_only = (
                public_path.name == f"challenge-{public_challenge_id(public)}.json"
                and _sha_bytes(public_bytes) == public_id
            )
            all_public_challenges_masked &= public_masked
            all_public_ids_visible_only &= public_id_visible_only
            episode_artifacts.append(
                {
                    "public_challenge_id": public_id,
                    "public_path_object": public_path,
                    "public_bytes": public_bytes,
                    "private_path_object": private_path,
                    "private_bytes": private_bytes,
                    "report_row": {
                        "proximity_radius": radius,
                        "seed": seed,
                        "counts": copy.deepcopy(episode["counts"]),
                        "private_episode_path": str(private_path.relative_to(out_dir)),
                        "private_episode_sha256": _sha_bytes(private_bytes),
                        "public_path": str(public_path.relative_to(out_dir)),
                        "public_sha256": _sha_bytes(public_bytes),
                        "public_challenge_id": public_id,
                        "public_answer_masked": public_masked,
                        "public_id_visible_only": public_id_visible_only,
                        "pairs": pair_rows,
                    },
                }
            )

    ordered_artifacts = _sorted_unique_episode_artifacts(episode_artifacts)
    for artifact in ordered_artifacts:
        artifact["public_path_object"].write_bytes(artifact["public_bytes"])
        artifact["private_path_object"].write_bytes(artifact["private_bytes"])
    episode_rows = [artifact["report_row"] for artifact in ordered_artifacts]

    counts = {
        "episodes": len(episode_rows),
        "demonstrations": sum(row["counts"]["demonstrations"] for row in episode_rows),
        "queries": sum(row["counts"]["queries"] for row in episode_rows),
        "retained_pairs": sum(
            row["counts"]["demonstrations"] + row["counts"]["queries"]
            for row in episode_rows
        ),
        "canonical_pairs_checked": len(canonical_rows),
    }
    report = {
        "schema": REPORT_SCHEMA,
        "task_id": TASK_ID,
        "status": "proposed_unapproved",
        "approved": False,
        "parameters": {
            "proximity_radius": {
                "allowed_values": list(proto.ALLOWED_PROXIMITY_RADII),
                "original_default": proto.DEFAULT_PROXIMITY_RADIUS,
                "selection_scope": "once per complete episode",
                "input_constraint": (
                    "each retained input contains distance-0, distance-1, "
                    "distance-2, and distance-4 red objects"
                ),
            }
        },
        "counts": counts,
        "programs": program_rows,
        "canonical_pairs": canonical_rows,
        "episodes": episode_rows,
        "source_files": source_rows,
        "unique_input_count": len(unique_input_hashes),
        "all_racket_exact": bool(all_racket_exact),
        "all_rival_racket_exact": bool(all_rival_racket_exact),
        "all_rivals_refuted_by_every_demo": bool(
            all_rivals_refuted_by_every_demo
        ),
        "all_queries_setting_sensitive": bool(all_queries_setting_sensitive),
        "all_public_challenges_masked": bool(all_public_challenges_masked),
        "all_public_ids_visible_only": bool(all_public_ids_visible_only),
        "limitations": [
            "This is a task-local proposed prototype; production generator.py and canonical authority are unchanged.",
            "Evidence covers one retained 3-demo/4-query episode per radius, not every seed or lawful input.",
            "Named rivals are only the other two bounded radius values; this is not proof against every conceivable rule.",
        ],
        "replay": {
            "cwd": "repo",
            "argv": [
                "python3",
                f"generators/{TASK_ID}/workspace/parametric/verify.py",
                "--out-dir",
                f"../checks/parametric/{TASK_ID}-proximity-radius-v1",
            ],
        },
    }
    _write_json(out_dir / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report(args.out_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    gates = (
        report["all_racket_exact"],
        report["all_rival_racket_exact"],
        report["all_rivals_refuted_by_every_demo"],
        report["all_queries_setting_sensitive"],
        report["all_public_challenges_masked"],
        report["all_public_ids_visible_only"],
    )
    return 0 if all(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())

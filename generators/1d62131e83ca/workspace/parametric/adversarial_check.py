#!/usr/bin/env python3
"""Run the bounded sampler/privacy attack retained for the ray-orientation prototype."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
ROOT = HERE.parents[4]
DEFAULT_OUT = ROOT.parent / "checks" / "parametric" / "1d62131e83ca-adversarial.json"


def _load_prototype():
    path = HERE.with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "adversarial_proto_1d62131e83ca", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report(*, out_path: Path | None = None) -> dict[str, Any]:
    """Exercise two bounded attack surfaces and optionally retain a JSON receipt."""
    proto = _load_prototype()
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    all_hashes: set[str] = set()

    for difficulty in ("easy", "medium", "hard"):
        for setting in proto.SETTINGS:
            for seed in range(4):
                episode_seed = seed + (100 if setting == "ne_sw" else 0)
                episode = proto.generate_episode(
                    episode_seed,
                    difficulty=difficulty,
                    ray_orientation=setting,
                    demo_count=3,
                    query_count=4,
                )
                replay = proto.generate_episode(
                    episode_seed,
                    difficulty=difficulty,
                    ray_orientation=setting,
                    demo_count=3,
                    query_count=4,
                )
                if episode != replay:
                    raise AssertionError("same-seed episode replay changed")
                rival = next(value for value in proto.SETTINGS if value != setting)
                hashes = []
                for pair in episode["train"] + episode["test"]:
                    digest = proto._grid_hash(pair["input"])
                    hashes.append(digest)
                    all_hashes.add(digest)
                    if not proto.input_is_valid(
                        pair["input"], ray_orientation=setting
                    ) or not proto.input_is_valid(
                        pair["input"], ray_orientation=rival
                    ):
                        raise AssertionError("sampler escaped common lawful support")
                    if proto.solve(
                        pair["input"], ray_orientation=setting
                    ) != pair["output"]:
                        raise AssertionError("stored answer differs from selected setting")
                    if proto.solve(
                        pair["input"], ray_orientation=rival
                    ) == pair["output"]:
                        raise AssertionError("declared rival survived a retained pair")
                    if any(
                        type(cell) is not int
                        for row in pair["input"]
                        for cell in row
                    ):
                        raise AssertionError("sampler emitted a non-exact integer cell")
                if len(set(hashes)) != 7:
                    raise AssertionError("episode contains duplicate visible inputs")
                rows.append(
                    {
                        "difficulty": difficulty,
                        "setting": setting,
                        "seed": episode_seed,
                        "pairs": 7,
                        "distinct_inputs": 7,
                        "deterministic_replay": True,
                    }
                )

    boundary_rows = []
    for setting in proto.SETTINGS:
        for demo_count, query_count in ((1, 1), (8, 8)):
            episode = proto.generate_episode(
                900 + demo_count + (100 if setting == "ne_sw" else 0),
                ray_orientation=setting,
                demo_count=demo_count,
                query_count=query_count,
            )
            hashes = [
                proto._grid_hash(pair["input"])
                for pair in episode["train"] + episode["test"]
            ]
            if len(hashes) != demo_count + query_count or len(set(hashes)) != len(
                hashes
            ):
                raise AssertionError("boundary-count episode lost or duplicated inputs")
            boundary_rows.append(
                {
                    "setting": setting,
                    "demo_count": demo_count,
                    "query_count": query_count,
                    "distinct_inputs": len(set(hashes)),
                }
            )

    privacy_episode = proto.generate_episode(777, ray_orientation="ne_sw")
    identity = proto.public_id(privacy_episode)
    hidden = copy.deepcopy(privacy_episode)
    hidden["parameters"]["ray_orientation"] = "nw_se"
    hidden["program"] = "changed privately"
    hidden["meta"]["seed"] = 0
    for pair in hidden["test"]:
        pair["output"] = [[9]]
    visible = copy.deepcopy(privacy_episode)
    visible["train"][0]["output"][0][0] = (
        visible["train"][0]["output"][0][0] + 1
    ) % 10
    public = json.loads(proto.public_bytes(privacy_episode))
    privacy = {
        "hidden_metadata_and_query_answer_stable": proto.public_id(hidden)
        == identity,
        "visible_demo_change_changes_id": proto.public_id(visible) != identity,
        "public_keys_exact": set(public) == {"train", "test"},
        "query_answers_absent": all(
            "output" not in pair for pair in public["test"]
        ),
        "private_fields_absent": not any(
            key in public for key in ("parameters", "program", "meta")
        ),
    }
    if not all(privacy.values()):
        raise AssertionError(f"public/private projection invariant failed: {privacy}")

    report: dict[str, Any] = {
        "schema": "1d62131e83ca-parametric-adversarial-v1",
        "status": "bounded_no_finding",
        "task_id": proto.TASK_ID,
        "surfaces": [
            "sampler_count_retry_boundaries",
            "public_private_projection_identity",
        ],
        "source_hashes": {
            str(HERE.with_name("prototype.py").relative_to(ROOT)): _sha256(
                HERE.with_name("prototype.py")
            ),
            str(HERE.relative_to(ROOT)): _sha256(HERE),
        },
        "seed_sweep": {
            "episodes": len(rows),
            "pairs": sum(row["pairs"] for row in rows),
            "globally_distinct_inputs": len(all_hashes),
            "rows": rows,
        },
        "boundary_counts": boundary_rows,
        "privacy": privacy,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "limitations": [
            "Finite sweep: four seeds per difficulty and setting.",
            "No claim about every seed or every conceivable rival.",
            "Racket parity is covered by the separate exact verifier, not repeated here.",
        ],
    }
    if out_path is not None:
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = build_report(out_path=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

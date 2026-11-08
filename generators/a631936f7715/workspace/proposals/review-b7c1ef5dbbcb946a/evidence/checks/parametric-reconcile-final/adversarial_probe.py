#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from typing import Any

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    parametric = root / "generators" / "a631936f7715" / "workspace" / "parametric"
    proto = load_module("a631_adversarial_proto", parametric / "prototype.py")

    support_rows = []
    for seed in (0, -17, 20261023):
        inputs = proto.build_inputs(seed, proto.MAX_UNIQUE_INPUTS)
        keys = [canonical_bytes(grid) for grid in inputs]
        support_rows.append(
            {
                "seed": seed,
                "count": len(inputs),
                "unique": len(set(keys)),
                "all_exact_int_colors": all(
                    type(value) is int and 0 <= value <= 9
                    for grid in inputs
                    for row in grid
                    for value in row
                ),
            }
        )
    try:
        proto.build_inputs(0, proto.MAX_UNIQUE_INPUTS + 1)
    except ValueError as exc:
        overflow_rejected = "finite support" in str(exc)
        overflow_message = str(exc)
    else:
        overflow_rejected = False
        overflow_message = None

    episode_rows = []
    identifier_rows = []
    for connectivity in proto.ALLOWED_CONNECTIVITIES:
        episode = proto.build_episode(20261023, connectivity=connectivity, n_train=3, n_test=4)
        all_pairs = episode["train"] + episode["test"]
        all_keys = [canonical_bytes(pair["input"]) for pair in all_pairs]
        public_name = proto.public_artifact_name(episode)

        private_variant = deepcopy(episode)
        private_variant["seed"] = -999
        private_variant["parameters"] = {"component_connectivity": 99}
        private_variant["program"] = "changed-private-program"
        private_variant["generator_source"] = "changed/private.py"
        private_variant["generator_sha256"] = "f" * 64
        private_variant["train"][0]["sampling"] = {"seed": 123, "input_index": 456}
        private_variant["test"][0]["sampling"] = {"seed": 789, "input_index": 1011}
        private_variant["test"][0]["output"] = [[0]]

        visible_demo_variant = deepcopy(episode)
        visible_demo_variant["train"][0]["output"][0][0] = (
            visible_demo_variant["train"][0]["output"][0][0] + 1
        ) % 10
        visible_query_variant = deepcopy(episode)
        visible_query_variant["test"][0]["input"][0][0] = (
            visible_query_variant["test"][0]["input"][0][0] + 1
        ) % 10

        episode_rows.append(
            {
                "connectivity": connectivity,
                "train": len(episode["train"]),
                "test": len(episode["test"]),
                "unique_inputs": len(set(all_keys)),
                "episode_errors": proto.episode_errors(episode),
            }
        )
        identifier_rows.append(
            {
                "connectivity": connectivity,
                "name": public_name,
                "opaque_pattern": bool(re.fullmatch(r"challenge-[0-9a-f]{64}\.json", public_name)),
                "private_changes_preserve_name": proto.public_artifact_name(private_variant) == public_name,
                "demo_output_change_changes_name": proto.public_artifact_name(visible_demo_variant) != public_name,
                "query_input_change_changes_name": proto.public_artifact_name(visible_query_variant) != public_name,
            }
        )

    artifact_dir = Path(args.artifact_dir)
    public_dir = artifact_dir / "public"
    public_rows = []
    for path in sorted(public_dir.glob("*.json")):
        raw = path.read_bytes()
        payload = json.loads(raw)
        expected = f"challenge-{public_challenge_id(payload)}.json"
        public_rows.append(
            {
                "name": path.name,
                "name_matches_visible_payload": path.name == expected,
                "bytes_match_shared_contract": raw == public_challenge_bytes(payload),
                "top_keys": sorted(payload),
                "train_count": len(payload.get("train", [])),
                "test_count": len(payload.get("test", [])),
                "train_pair_keys_ok": all(set(pair) == {"input", "output"} for pair in payload.get("train", [])),
                "test_pair_keys_ok": all(set(pair) == {"input"} for pair in payload.get("test", [])),
                "path_has_private_token": any(token in path.name for token in ("connectivity", "seed", "20261023")),
            }
        )

    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    result = {
        "schema": "a631936f7715-parametric-adversarial-v1",
        "status": "passed",
        "surfaces": ["sampler boundaries and finite support", "public/private export and identifier privacy"],
        "support": support_rows,
        "overflow_rejected": overflow_rejected,
        "overflow_message": overflow_message,
        "episodes": episode_rows,
        "identifiers": identifier_rows,
        "public_files": public_rows,
        "racket_report": {
            "status": report.get("status"),
            "counts": report.get("counts"),
            "identifiability_from_demonstrations": report.get("identifiability_from_demonstrations"),
        },
    }

    predicates = [
        all(row["count"] == proto.MAX_UNIQUE_INPUTS for row in support_rows),
        all(row["unique"] == proto.MAX_UNIQUE_INPUTS for row in support_rows),
        all(row["all_exact_int_colors"] for row in support_rows),
        overflow_rejected,
        all(row["train"] == 3 and row["test"] == 4 and row["unique_inputs"] == 7 for row in episode_rows),
        all(row["episode_errors"] == [] for row in episode_rows),
        all(row["opaque_pattern"] for row in identifier_rows),
        all(row["private_changes_preserve_name"] for row in identifier_rows),
        all(row["demo_output_change_changes_name"] for row in identifier_rows),
        all(row["query_input_change_changes_name"] for row in identifier_rows),
        len(public_rows) == 2,
        all(row["name_matches_visible_payload"] for row in public_rows),
        all(row["bytes_match_shared_contract"] for row in public_rows),
        all(row["top_keys"] == ["test", "train"] for row in public_rows),
        all(row["train_count"] == 3 and row["test_count"] == 4 for row in public_rows),
        all(row["train_pair_keys_ok"] and row["test_pair_keys_ok"] for row in public_rows),
        not any(row["path_has_private_token"] for row in public_rows),
        report.get("status") == "passed",
        report.get("counts", {}).get("racket_executions") == 28,
        report.get("identifiability_from_demonstrations", {}).get("query_answers_used_to_select_setting") is False,
    ]
    if not all(predicates):
        result["status"] = "failed"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "out": str(out)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

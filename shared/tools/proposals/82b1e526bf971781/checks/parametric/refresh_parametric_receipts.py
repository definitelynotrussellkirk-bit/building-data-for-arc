#!/usr/bin/env python3
"""Verify packet-local parametric exports and refresh source-bound receipts.

This is deliberately task-agnostic for the three assigned homes.  It verifies
serialized hashes, opaque visible-byte IDs, four-query controller storage,
one-query public turns, and the private mapping needed for sequential reveal.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import public_challenge_bytes  # noqa: E402

TARGETS = {
    "d07a6cba78c7": "test_parametric_marker_side.py",
    "cddbee92b2f3": "test_parametric_source_side.py",
    "bb75d495c809": "test_parametric_connectivity.py",
}


class VerificationError(ValueError):
    """The serialized export is not a valid sequential public projection."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot read JSON {path}: {exc}") from exc


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def _example_root(task_id: str) -> Path:
    if task_id not in TARGETS:
        raise KeyError(f"unknown task {task_id!r}")
    return WORK / "checks/parametric" / f"{task_id}-example"


def _verify_export_root(task_id: str, root: Path) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    private_path = root / "private.json"
    manifest = _load_json(manifest_path)
    private = _load_json(private_path)

    files = manifest.get("files")
    _require(isinstance(files, dict) and files, "manifest.files must be a nonempty object")
    actual_members = {
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    _require(set(files) == actual_members, "manifest member set does not match export files")
    for relative, expected in files.items():
        path = root / relative
        _require(path.is_file(), f"missing manifest member {relative}")
        _require(_sha256(path) == expected, f"hash mismatch for {relative}")

    episodes = manifest.get("episodes")
    private_episodes = private.get("episodes")
    _require(isinstance(episodes, list) and episodes, "manifest must index at least one episode")
    _require(isinstance(private_episodes, list) and len(private_episodes) == len(episodes),
             "private/manifest episode counts differ")

    flattened_turn_ids = [turn_id for row in episodes for turn_id in row.get("turn_ids", [])]
    _require(manifest.get("public_ids") == flattened_turn_ids,
             "public_ids must equal the episode turn order")
    _require(len(flattened_turn_ids) == len(set(flattened_turn_ids)),
             "public turn IDs must be unique")

    controller_query_counts: list[int] = []
    all_racket_checked = True
    first_turn_matches = True
    pair_labels = 0
    settings: list[dict[str, Any]] = []
    demos_per_episode: list[int] = []
    queries_per_episode: list[int] = []

    for public_index, (index_row, episode) in enumerate(zip(episodes, private_episodes)):
        controller_rel = index_row.get("controller")
        turn_ids = index_row.get("turn_ids")
        _require(isinstance(controller_rel, str), f"episode {public_index}: missing controller path")
        _require(isinstance(turn_ids, list) and len(turn_ids) == 4,
                 f"episode {public_index}: exactly four turn IDs required")
        controller_path = root / controller_rel
        controller_bytes = controller_path.read_bytes()
        _require(controller_path.stem == hashlib.sha256(controller_bytes).hexdigest(),
                 f"episode {public_index}: controller filename is not visible-byte SHA-256")
        controller = json.loads(controller_bytes)
        _require(set(controller) == {"train", "test"},
                 f"episode {public_index}: controller contains non-public keys")
        _require(isinstance(controller["test"], list) and len(controller["test"]) == 4,
                 f"episode {public_index}: controller must store four queries")
        _require(all(set(pair) == {"input"} for pair in controller["test"]),
                 f"episode {public_index}: controller leaked query answers")
        _require(controller_bytes == public_challenge_bytes(episode),
                 f"episode {public_index}: controller is not the private episode projection")
        controller_query_counts.append(len(controller["test"]))

        _require(episode.get("controller_id") == controller_path.stem,
                 f"episode {public_index}: private controller ID mismatch")
        _require(episode.get("turn_ids") == turn_ids,
                 f"episode {public_index}: private turn order mismatch")
        _require(isinstance(episode.get("train"), list),
                 f"episode {public_index}: private train missing")
        _require(isinstance(episode.get("test"), list) and len(episode["test"]) == 4,
                 f"episode {public_index}: private test must contain four labels")
        demos_per_episode.append(len(episode["train"]))
        queries_per_episode.append(len(episode["test"]))
        pair_labels += len(episode["train"]) + len(episode["test"])
        settings.append(copy.deepcopy(episode.get("settings", {})))
        all_racket_checked = all_racket_checked and episode.get("certificate", {}).get("racket_checked") is True

        for query_index, turn_id in enumerate(turn_ids):
            _require(isinstance(turn_id, str) and len(turn_id) == 64,
                     f"episode {public_index} turn {query_index}: invalid opaque ID")
            public_path = root / "public" / f"{turn_id}.json"
            body = public_path.read_bytes()
            _require(hashlib.sha256(body).hexdigest() == turn_id,
                     f"episode {public_index} turn {query_index}: filename is not visible-byte SHA-256")
            visible = json.loads(body)
            _require(set(visible) == {"train", "test"},
                     f"episode {public_index} turn {query_index}: public keys leaked")
            _require(isinstance(visible["test"], list) and len(visible["test"]) == 1,
                     f"episode {public_index} turn {query_index}: public file must expose one query")
            _require(set(visible["test"][0]) == {"input"},
                     f"episode {public_index} turn {query_index}: public query leaked an answer")
            expected = public_challenge_bytes({
                "train": episode["train"],
                "test": [episode["test"][query_index]],
            })
            _require(body == expected,
                     f"episode {public_index} turn {query_index}: sequential projection mismatch")
            if query_index == 0:
                first_turn_matches = first_turn_matches and body == public_challenge_bytes({
                    "train": episode["train"],
                    "test": episode["test"][:1],
                })

    _require(all_racket_checked, "one or more retained episode certificates lack protected-Racket replay")
    _require(first_turn_matches, "first-turn bytes differ from single-query projection")
    _require(manifest.get("writer_executes_racket") is False,
             "writer_executes_racket must truthfully remain false")
    _require(str(manifest.get("manifest_usage", "")).startswith("Controller metadata"),
             "manifest must be explicitly marked as non-model-visible controller metadata")

    return {
        "episodes": len(episodes),
        "controller_queries": controller_query_counts,
        "public_turns": len(flattened_turn_ids),
        "one_query_per_public_turn": True,
        "first_turn_bytes_match_single_query": first_turn_matches,
        "public_ids_visible_byte_sha256": True,
        "manifest_hashes_verified": True,
        "all_certificates_racket_checked": all_racket_checked,
        "demos_per_episode": demos_per_episode,
        "queries_per_episode": queries_per_episode,
        "pair_labels_checked": pair_labels,
        "settings": settings,
        "runtime_identity": private.get("metadata", {}).get("runtime_identity"),
    }


def verify_export(task_id: str) -> dict[str, Any]:
    return _verify_export_root(task_id, _example_root(task_id))


def negative_corruption_probe(task_id: str) -> bool:
    """Prove the verifier rejects a changed public turn with stale manifest/ID."""
    source = _example_root(task_id)
    with tempfile.TemporaryDirectory(prefix=f"{task_id}-corrupt-export-") as tmp:
        copy_root = Path(tmp) / "export"
        shutil.copytree(source, copy_root)
        manifest = _load_json(copy_root / "manifest.json")
        victim = copy_root / "public" / f"{manifest['public_ids'][0]}.json"
        victim.write_bytes(victim.read_bytes() + b" ")
        try:
            _verify_export_root(task_id, copy_root)
        except VerificationError:
            return True
    raise AssertionError("corrupted public turn was accepted")


def build_receipt(task_id: str) -> dict[str, Any]:
    stats = verify_export(task_id)
    _require(negative_corruption_probe(task_id), "negative corruption probe did not reject")

    task_result_path = WORK / "checks" / task_id / "after/task-tests/result.json"
    task_result = _load_json(task_result_path)
    _require(task_result.get("passed") is True, f"{task_id}: task tests are not green")

    bounded_path = WORK / "checks/parametric/bounded-probe.json"
    bounded = _load_json(bounded_path)
    bounded_target = bounded.get("targets", {}).get(task_id)
    _require(isinstance(bounded_target, dict) and bounded_target.get("status") == "passed",
             f"{task_id}: bounded probe missing or not passed")
    _require(all(row.get("first_turn_query_count") == 1 for row in bounded_target.get("jobs", [])),
             f"{task_id}: bounded probe did not verify one-query first turns")

    private_path = _example_root(task_id) / "private.json"
    manifest_path = _example_root(task_id) / "manifest.json"
    focused_test = f"generators/{task_id}/tests/{TARGETS[task_id]}"

    bounded_receipt = copy.deepcopy(bounded_target)
    bounded_receipt.update({
        "path": "checks/parametric/bounded-probe.json",
        "sha256": _sha256(bounded_path),
    })

    return {
        "schema": "packet-parametric-task-receipt-v2",
        "task_id": task_id,
        "status": "prototype_proposed",
        "canonical_default_preserved": True,
        "focused_test_source": focused_test,
        "task_tests": {
            "passed": True,
            "counts": task_result["test_counts"],
            "path": f"checks/{task_id}/after/task-tests/result.json",
            "sha256": _sha256(task_result_path),
        },
        "racket_example": {
            "path": f"checks/parametric/{task_id}-example/private.json",
            "sha256": _sha256(private_path),
            "public_manifest_path": f"checks/parametric/{task_id}-example/manifest.json",
            "public_manifest_sha256": _sha256(manifest_path),
            "episodes": stats["episodes"],
            "settings": stats["settings"],
            "demos_per_episode": stats["demos_per_episode"],
            "queries_per_episode": stats["queries_per_episode"],
            "pair_labels_checked": stats["pair_labels_checked"],
            "all_certificates_racket_checked": stats["all_certificates_racket_checked"],
            "runtime_identity": stats["runtime_identity"],
            "sequential_export": {
                key: stats[key]
                for key in (
                    "controller_queries",
                    "public_turns",
                    "one_query_per_public_turn",
                    "first_turn_bytes_match_single_query",
                    "public_ids_visible_byte_sha256",
                    "manifest_hashes_verified",
                )
            },
        },
        "bounded_adversarial_probe": bounded_receipt,
        "export_verifier": {
            "status": "passed",
            "tool": "checks/parametric/refresh_parametric_receipts.py",
            "negative_corruption_rejected": True,
            "scope": "hash/member integrity, opaque public IDs, one-query turns, four-query controller, private mapping",
        },
        "limitations": [
            "finite declared settings and seeds only",
            "prototype is not owner-qualified or accepted",
            "training_admitted remains false",
        ],
    }


def write_receipt(task_id: str) -> Path:
    receipt = build_receipt(task_id)
    destination = REPO / "generators" / task_id / "workspace/parametric/evidence/current/receipt.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", nargs="*", choices=sorted(TARGETS))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    task_ids = args.task_id or list(TARGETS)
    rows = []
    for task_id in task_ids:
        receipt = build_receipt(task_id)
        destination = None if args.check_only else write_receipt(task_id)
        rows.append({
            "task_id": task_id,
            "status": "passed",
            "task_tests": receipt["task_tests"]["counts"]["passed"],
            "public_turns": receipt["racket_example"]["sequential_export"]["public_turns"],
            "negative_corruption_rejected": True,
            "receipt": str(destination) if destination else None,
        })
    print(json.dumps({"schema": "parametric-receipt-refresh-v1", "results": rows}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

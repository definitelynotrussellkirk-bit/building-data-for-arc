#!/usr/bin/env python3
"""Bounded adversarial pass over sampler/retry and public-export boundaries."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import time

HERE = Path(__file__).resolve()
REPO = HERE.parents[3] / "repo"
PARAMETRIC = REPO / "generators" / "48bda9528e71" / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    proto = _load("projection_reach_adversarial_proto", PARAMETRIC / "prototype.py")
    verify = _load("projection_reach_adversarial_verify", PARAMETRIC / "verify.py")

    # Surface 1: maximum supported counts, determinism, and bounded retry failure.
    large_a = proto.generate_episode(
        103, projection_reach="to_boundary", difficulty="hard", n_train=16, n_test=16
    )
    large_b = proto.generate_episode(
        103, projection_reach="to_boundary", difficulty="hard", n_train=16, n_test=16
    )
    large_pairs = [*large_a["train"], *large_a["test"]]
    large_hashes = [_grid_hash(pair["input"]) for pair in large_pairs]

    original_candidate = proto._candidate_input
    constant_grid = original_candidate(7, 0, "hard")
    calls = {"count": 0}

    def constant_candidate(seed, candidate_index, difficulty):
        del seed, candidate_index, difficulty
        calls["count"] += 1
        return deepcopy(constant_grid)

    proto._candidate_input = constant_candidate
    retry_error = None
    try:
        proto.generate_episode(
            7, projection_reach="one_step", difficulty="hard", n_train=1, n_test=1
        )
    except Exception as exc:
        retry_error = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        proto._candidate_input = original_candidate

    # Surface 2: exact-integer visible export, private-ID invariance, duplicate preflight.
    episode = proto.generate_episode(
        17, projection_reach="to_boundary", difficulty="hard", n_train=2, n_test=4
    )
    private_change = deepcopy(episode)
    private_change["meta"]["seed"] = 999999
    private_change["parameters"][proto.PARAMETER_NAME] = "one_step"
    private_change["test"][0]["output"][0][0] = (
        private_change["test"][0]["output"][0][0] + 1
    ) % 10
    visible_change = deepcopy(episode)
    visible_change["test"][0]["input"][0][0] = (
        visible_change["test"][0]["input"][0][0] + 1
    ) % 10
    bool_change = deepcopy(episode)
    bool_change["train"][0]["input"][0][0] = True
    bool_error = None
    try:
        proto.public_bytes(bool_change)
    except Exception as exc:
        bool_error = {"type": type(exc).__name__, "message": str(exc)}

    duplicate_dir = args.out.parent / "duplicate-write-target"
    if duplicate_dir.exists():
        shutil.rmtree(duplicate_dir)
    duplicate_error = None
    try:
        verify.write_public_batch([episode, deepcopy(episode)], duplicate_dir, proto=proto)
    except Exception as exc:
        duplicate_error = {"type": type(exc).__name__, "message": str(exc)}

    checks = {
        "max_counts_return_32_pairs": len(large_pairs) == 32,
        "max_counts_all_inputs_distinct": len(set(large_hashes)) == 32,
        "max_counts_deterministic": large_a == large_b,
        "max_counts_every_pair_setting_sensitive": all(
            pair["output"] != proto.apply_python(pair["input"], "one_step")
            for pair in large_pairs
        ),
        "retry_exhaustion_is_bounded": (
            calls["count"] == 256
            and retry_error is not None
            and retry_error["type"] == "RuntimeError"
            and "found only 1 distinct" in retry_error["message"]
        ),
        "private_fields_do_not_change_public_id": (
            proto.public_id(private_change) == proto.public_id(episode)
        ),
        "visible_input_changes_public_id": (
            proto.public_id(visible_change) != proto.public_id(episode)
        ),
        "bool_visible_color_rejected": (
            bool_error is not None
            and bool_error["type"] == "ValueError"
            and "exact integer colors" in bool_error["message"]
        ),
        "duplicate_public_payload_rejected_prewrite": (
            duplicate_error is not None
            and duplicate_error["type"] == "ValueError"
            and "duplicate public challenge" in duplicate_error["message"]
            and (not duplicate_dir.exists() or not list(duplicate_dir.iterdir()))
        ),
    }
    report = {
        "task_id": proto.TASK_ID,
        "scope": [
            "sampler count/retry boundaries",
            "public/private export and verifier rejection paths",
        ],
        "checks": checks,
        "details": {
            "max_pair_count": len(large_pairs),
            "max_unique_input_count": len(set(large_hashes)),
            "retry_candidate_calls": calls["count"],
            "retry_error": retry_error,
            "bool_export_error": bool_error,
            "duplicate_export_error": duplicate_error,
            "duplicate_target_exists": duplicate_dir.exists(),
        },
        "passed": all(checks.values()),
        "finding": (
            "No defect found within the bounded pass; maximum pair counts remained "
            "deterministic/distinct and all deliberate retry/export violations failed closed."
        ),
        "limitations": [
            "One maximum-count seed and one forced retry schedule were exercised.",
            "This does not establish support for every seed or filesystem failure mode.",
        ],
        "elapsed_seconds": time.monotonic() - started,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

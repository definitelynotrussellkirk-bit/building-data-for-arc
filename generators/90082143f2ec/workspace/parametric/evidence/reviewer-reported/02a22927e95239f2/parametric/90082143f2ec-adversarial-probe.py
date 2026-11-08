#!/usr/bin/env python3
"""Bounded adversarial probe for the proposed 90082143f2ec prototype."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
import time
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "90082143f2ec"


def load_prototype(repo_root: Path):
    path = repo_root / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    spec = importlib.util.spec_from_file_location("probe_parametric_90082143f2ec", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def fingerprint(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def expect_raises(error_type, fn, *args, **kwargs) -> str:
    try:
        fn(*args, **kwargs)
    except error_type as exc:
        return str(exc)
    raise AssertionError(f"expected {error_type.__name__} from {fn.__name__}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    repo_root = Path.cwd().resolve()
    p, prototype_path = load_prototype(repo_root)

    # Surface 1: sampler boundaries and exact Racket parity at the supported 8+8 limit.
    grids_even = p.episode_inputs(42, demo_count=8, query_count=8, root=repo_root)
    grids_odd = p.episode_inputs(43, demo_count=8, query_count=8, root=repo_root)
    assert grids_even == grids_odd
    assert len(grids_even) == 16
    assert len({fingerprint(grid) for grid in grids_even}) == 16

    canonical = p.materialize_rule("restore_mode", root=repo_root)
    alternate = p.materialize_rule("mask_zero", root=repo_root)
    with RacketBridge(max_calls_before_restart=128) as bridge:
        restored = p.execute_rule_many(canonical, grids_even, bridge=bridge, root=repo_root)
        masked = p.execute_rule_many(alternate, grids_even, bridge=bridge, root=repo_root)
    assert all(left != right for left, right in zip(restored, masked, strict=True))
    for grid, restored_grid, masked_grid in zip(grids_even, restored, masked, strict=True):
        expected = [
            [value if value == restored_grid[r][c] else 0 for c, value in enumerate(row)]
            for r, row in enumerate(grid)
        ]
        assert masked_grid == expected

    # Surface 2: public/private separation and rejection paths on a fresh writer run.
    with tempfile.TemporaryDirectory(prefix="arc-parametric-probe-") as temp:
        evidence = Path(temp) / "evidence"
        manifest = p.write_evidence(
            evidence,
            seeds=[42, 43],
            demo_count=8,
            query_count=8,
            root=repo_root,
        )
        public_paths = sorted((evidence / "public").glob("challenge-*.json"))
        assert len(public_paths) == 2
        assert [row["public_id"] for row in manifest["episodes"]] == sorted(
            row["public_id"] for row in manifest["episodes"]
        )
        forbidden = (
            b"outlier_action",
            b"restore_mode",
            b"mask_zero",
            b"query_answers",
            b'"seed"',
            b"program_sha256",
            b"paired_input_key",
        )
        public_ids = []
        for path in public_paths:
            raw = path.read_bytes()
            visible = json.loads(raw)
            assert raw == public_challenge_bytes(visible)
            public_id = public_challenge_id(visible)
            assert path.name == f"challenge-{public_id}.json"
            assert not any(token in raw for token in forbidden)
            assert len(visible["train"]) == 8
            assert len(visible["test"]) == 8
            assert all(set(pair) == {"input"} for pair in visible["test"])
            public_ids.append(public_id)

        rejection_messages = {
            "bool_seed": expect_raises(ValueError, p.parameter_for_seed, True),
            "negative_seed": expect_raises(ValueError, p.parameter_for_seed, -1),
            "bool_count": expect_raises(
                ValueError,
                p.episode_inputs,
                0,
                demo_count=True,
                query_count=4,
                root=repo_root,
            ),
            "oversize_count": expect_raises(
                ValueError,
                p.episode_inputs,
                0,
                demo_count=9,
                query_count=4,
                root=repo_root,
            ),
            "unknown_action": expect_raises(
                ValueError,
                p.materialize_rule,
                "keep_noise",
                root=repo_root,
            ),
            "source_drift": expect_raises(
                ValueError,
                p.materialize_rule,
                root=repo_root,
                source=canonical + "\n",
            ),
            "duplicate_seeds": expect_raises(
                ValueError,
                p.write_evidence,
                Path(temp) / "duplicates",
                seeds=[42, 42],
                root=repo_root,
            ),
            "overwrite": expect_raises(
                FileExistsError,
                p.write_evidence,
                evidence,
                seeds=[42, 43],
                root=repo_root,
            ),
        }

    result = {
        "schema": "90082143f2ec-outlier-action-adversarial-v1",
        "passed": True,
        "task_id": TASK_ID,
        "prototype": str(prototype_path.relative_to(repo_root)),
        "prototype_sha256": hashlib.sha256(prototype_path.read_bytes()).hexdigest(),
        "surfaces": {
            "sampler_and_racket_boundary": {
                "paired_seeds": [42, 43],
                "demo_count": 8,
                "query_count": 8,
                "distinct_inputs": len(grids_even),
                "all_settings_disagree": True,
                "mask_relation_checked_on": len(grids_even),
            },
            "public_private_and_rejections": {
                "public_ids": public_ids,
                "public_files_checked": len(public_ids),
                "forbidden_tokens_absent": True,
                "rejection_messages": rejection_messages,
            },
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "finding": "bounded no-finding on the two attacked surfaces",
        "limits": [
            "tested only paired seeds 42/43 at the declared maximum counts",
            "privacy scan covers declared metadata tokens and visible-byte identity",
            "Racket parity is exact for the 16 retained boundary inputs, not all inputs",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

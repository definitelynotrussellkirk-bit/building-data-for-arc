#!/usr/bin/env python3
"""Replay and privacy-check retained evidence for the border-policy prototype."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "36275402c6b2"
SCHEMA = "36275402c6b2-border-policy-evidence-v1"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON evidence file {path}") from exc


def _safe_file(base: Path, relative: Any, *, prefix: str | None = None) -> Path:
    if type(relative) is not str or not relative:
        raise ValueError("evidence path must be a nonempty relative string")
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe evidence path: {relative!r}")
    if prefix is not None and (not rel.parts or rel.parts[0] != prefix):
        raise ValueError(f"evidence path must stay under {prefix}/: {relative!r}")
    path = (base / rel).resolve()
    if not path.is_relative_to(base) or not path.is_file() or path.is_symlink():
        raise ValueError(f"missing or unsafe evidence file: {relative!r}")
    return path


def _load_prototype():
    path = Path(__file__).resolve().with_name("prototype.py")
    spec = importlib.util.spec_from_file_location(
        "parametric_border_policy_36275402c6b2_verifier_target", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require_equal(actual: Any, expected: Any, message: str) -> None:
    if actual != expected:
        raise ValueError(message)


def verify_evidence(
    evidence: str | Path,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Rebuild every episode and reject source drift, tamper, leakage, or extras."""
    evidence_path = Path(evidence).resolve()
    if not evidence_path.is_dir() or evidence_path.is_symlink():
        raise ValueError(f"evidence directory is missing or unsafe: {evidence_path}")
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    prototype = _load_prototype()

    manifest_path = evidence_path / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("missing manifest.json")
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    _require_equal(manifest.get("schema"), SCHEMA, "unexpected evidence schema")
    _require_equal(manifest.get("task_id"), TASK_ID, "unexpected task_id")
    _require_equal(manifest.get("status"), prototype.STATUS, "unexpected evidence status")
    _require_equal(
        manifest.get("parameter"),
        {
            "name": "border_policy",
            "allowed": list(prototype.ALLOWED_POLICIES),
            "default": prototype.DEFAULT_POLICY,
        },
        "unexpected parameter contract",
    )
    if manifest.get("canonical_default_unchanged") is not True:
        raise ValueError("manifest does not preserve the canonical default")
    _require_equal(
        manifest.get("canonical_rule_hash"),
        prototype.CANONICAL_RULE_HASH,
        "canonical rule hash drift",
    )
    _require_equal(
        manifest.get("canonical_source_sha256"),
        prototype.CANONICAL_SOURCE_SHA256,
        "canonical source hash drift",
    )

    demos = prototype._validate_count("demo_count", manifest.get("demo_count"))
    queries = prototype._validate_count("query_count", manifest.get("query_count"))
    expected_files = {"manifest.json"}

    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root_path
    )
    del generator
    _require_equal(
        manifest.get("selected_generator"),
        {
            "file": str(generator_path.relative_to(root_path)),
            "sha256": generator_sha256,
        },
        "selected generator binding mismatch",
    )

    prototype_path = Path(prototype.__file__).resolve()
    _require_equal(
        manifest.get("prototype"),
        {
            "file": str(prototype_path.relative_to(root_path)),
            "sha256": _sha256(prototype_path.read_bytes()),
        },
        "prototype source binding mismatch",
    )

    program_rows = manifest.get("programs")
    if not isinstance(program_rows, dict) or set(program_rows) != set(
        prototype.ALLOWED_POLICIES
    ):
        raise ValueError("program inventory does not contain both border policies")
    programs: dict[str, str] = {}
    for policy in prototype.ALLOWED_POLICIES:
        row = program_rows[policy]
        if not isinstance(row, dict):
            raise ValueError(f"program row for {policy} must be an object")
        path = _safe_file(evidence_path, row.get("file"), prefix="private")
        expected_files.add(str(path.relative_to(evidence_path)))
        source = path.read_text(encoding="utf-8")
        expected_source = prototype.materialize_rule(policy, root=root_path)
        _require_equal(source, expected_source, f"{policy} Racket source mismatch")
        _require_equal(row.get("sha256"), _sha256(source.encode("utf-8")), f"{policy} program hash mismatch")
        programs[policy] = source

    episode_rows = manifest.get("episodes")
    if not isinstance(episode_rows, list) or not episode_rows:
        raise ValueError("manifest must contain at least one episode")
    if any(not isinstance(row, dict) for row in episode_rows):
        raise ValueError("episode manifest row must be an object")
    declared_public_ids = [row.get("public_id") for row in episode_rows]
    if any(type(public_id) is not str for public_id in declared_public_ids):
        raise ValueError("episode manifest public IDs must be strings")
    if declared_public_ids != sorted(declared_public_ids):
        raise ValueError("episode manifest rows must be sorted by public ID")
    seeds: set[int] = set()
    public_ids: set[str] = set()
    policy_counts: Counter[str] = Counter()
    covered_sides: set[str] = set()

    with RacketBridge(max_calls_before_restart=128) as bridge:
        for row in episode_rows:
            if not isinstance(row, dict):
                raise ValueError("episode manifest row must be an object")
            seed = prototype._validate_seed(row.get("seed"))
            if seed in seeds:
                raise ValueError("episode seeds must be distinct")
            seeds.add(seed)

            public_path = _safe_file(
                evidence_path, row.get("public_file"), prefix="public"
            )
            private_path = _safe_file(
                evidence_path, row.get("private_file"), prefix="private"
            )
            expected_files.update(
                {
                    str(public_path.relative_to(evidence_path)),
                    str(private_path.relative_to(evidence_path)),
                }
            )

            raw_public = public_path.read_bytes()
            public = _read_json(public_path)
            try:
                canonical_public = public_challenge_bytes(public)
            except ValueError as exc:
                raise ValueError("public challenge is malformed") from exc
            if raw_public != canonical_public:
                raise ValueError("public challenge is not stored as canonical visible bytes")
            public_id = public_challenge_id(public)
            if public_id in public_ids:
                raise ValueError("duplicate public challenge ID")
            public_ids.add(public_id)
            _require_equal(
                public_path.name,
                f"challenge-{public_id}.json",
                "public filename is not content-addressed",
            )

            private = _read_json(private_path)
            expected_public, expected_private = prototype.generate_episode(
                seed,
                demo_count=demos,
                query_count=queries,
                bridge=bridge,
                root=root_path,
            )
            _require_equal(public, expected_public, "public episode replay mismatch")
            _require_equal(private, expected_private, "private episode replay mismatch")

            expected_row = {
                "public_id": public_id,
                "public_file": str(public_path.relative_to(evidence_path)),
                "private_file": str(private_path.relative_to(evidence_path)),
                "seed": seed,
                "input_pair_key": private["input_pair_key"],
                "parameter": private["parameter"],
                "border_sides": private["border_sides"],
            }
            _require_equal(row, expected_row, "episode manifest row mismatch")
            policy = private["parameter"]["border_policy"]
            policy_counts[policy] += 1
            covered_sides.update(private["border_sides"])

        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        actual_outputs = prototype.execute_rule_many(
            programs[prototype.DEFAULT_POLICY],
            [pair["input"] for pair in canonical],
            bridge=bridge,
            root=root_path,
        )
        _require_equal(
            actual_outputs,
            [pair["output"] for pair in canonical],
            "canonical default replay mismatch",
        )

    canonical_check_path = evidence_path / "private" / "canonical-default-check.json"
    if not canonical_check_path.is_file() or canonical_check_path.is_symlink():
        raise ValueError("missing canonical-default-check.json")
    expected_files.add(str(canonical_check_path.relative_to(evidence_path)))
    expected_canonical_checks = [
        {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input_sha256": prototype._grid_fingerprint(pair["input"]),
            "output_sha256": prototype._grid_fingerprint(actual),
            "matched": True,
        }
        for pair, actual in zip(canonical, actual_outputs, strict=True)
    ]
    _require_equal(
        _read_json(canonical_check_path),
        expected_canonical_checks,
        "canonical check receipt mismatch",
    )

    actual_files = {
        str(path.relative_to(evidence_path))
        for path in evidence_path.rglob("*")
        if path.is_file()
    }
    _require_equal(actual_files, expected_files, "evidence contains missing or untracked files")

    return {
        "task_id": TASK_ID,
        "status": "verified",
        "episodes": len(episode_rows),
        "demonstrations": len(episode_rows) * demos,
        "queries": len(episode_rows) * queries,
        "policies": dict(sorted(policy_counts.items())),
        "covered_border_sides": sorted(covered_sides),
        "canonical_pairs": len(canonical),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args(argv)
    result = verify_evidence(args.evidence, root=args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

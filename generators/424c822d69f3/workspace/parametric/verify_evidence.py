#!/usr/bin/env python3
"""Verify retained nearest/farthest evidence by hash and real Racket replay."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "424c822d69f3"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON file: {path}") from error


def _safe_path(root: Path, relative) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("retained path must be a nonempty string")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"unsafe retained path: {relative!r}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"retained path escapes evidence root: {relative!r}")
    if not resolved.is_file():
        raise ValueError(f"retained file is missing: {relative}")
    return resolved


def _load_prototype():
    path = Path(__file__).with_name("prototype.py").resolve()
    spec = importlib.util.spec_from_file_location(
        "parametric_424c822d69f3_evidence_verifier", path
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require_current_snapshot(evidence: Path, relative: str, current: Path, label: str) -> None:
    retained = _safe_path(evidence, relative)
    current = Path(current).resolve()
    if not current.is_file() or current.read_bytes() != retained.read_bytes():
        raise ValueError(f"{label} source does not match retained snapshot")


def _manifest_rows(evidence: Path, manifest: dict) -> dict[str, str]:
    rows = manifest.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("manifest must contain a nonempty files list")
    expected = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("manifest file rows must be objects")
        relative = row.get("path")
        digest = row.get("sha256")
        if relative in expected:
            raise ValueError(f"duplicate manifest path: {relative}")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"invalid manifest SHA-256 for {relative}")
        path = _safe_path(evidence, relative)
        actual = _sha256(path.read_bytes())
        if actual != digest:
            raise ValueError(f"manifest hash mismatch for {relative}: {actual} != {digest}")
        expected[relative] = digest

    actual_files = {
        path.relative_to(evidence).as_posix()
        for path in evidence.rglob("*")
        if path.is_file() and path.relative_to(evidence).as_posix() != "manifest.json"
    }
    if actual_files != set(expected):
        missing = sorted(set(expected) - actual_files)
        untracked = sorted(actual_files - set(expected))
        raise ValueError(f"manifest inventory mismatch: missing={missing}, untracked={untracked}")
    return expected


def verify_evidence(evidence, *, root=None) -> dict:
    evidence = Path(evidence).resolve()
    if not evidence.is_dir():
        raise ValueError(f"evidence directory is missing: {evidence}")
    root = find_root(__file__) if root is None else Path(root).resolve()

    manifest = _read_json(evidence / "manifest.json")
    manifest_rows = _manifest_rows(evidence, manifest)
    if manifest.get("schema") != "424c822d69f3-parametric-manifest-v1":
        raise ValueError("manifest schema does not match the verifier")

    prototype_path = Path(__file__).with_name("prototype.py").resolve()
    _require_current_snapshot(
        evidence, "private/source_snapshot/prototype.py", prototype_path, "prototype"
    )
    _require_current_snapshot(
        evidence, "private/source_snapshot/verify_evidence.py", Path(__file__), "verifier"
    )
    prototype = _load_prototype()
    if manifest.get("prototype_version") != prototype.VERSION:
        raise ValueError("manifest prototype version does not match the verifier source")

    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    generator_relative = generator_path.relative_to(root).as_posix()
    _require_current_snapshot(
        evidence, "private/source_snapshot/generator.py", generator_path, "generator"
    )

    report = _read_json(_safe_path(evidence, "report.json"))
    if (report.get("schema") != "424c822d69f3-parametric-evidence-v1"
            or report.get("task_id") != TASK_ID
            or report.get("status") != "proposed_unapproved"):
        raise ValueError("report is not the expected proposed task evidence")
    episode_rows = report.get("episodes")
    rule_rows = report.get("rules")
    if not isinstance(episode_rows, list) or not episode_rows:
        raise ValueError("report contains no episodes")
    if any(not isinstance(row, dict) for row in episode_rows):
        raise ValueError("episode report rows must be objects")
    if [row.get("public_id") for row in episode_rows] != sorted(
        row.get("public_id") for row in episode_rows
    ):
        raise ValueError("report episodes are not sorted by public ID")
    if not isinstance(rule_rows, list):
        raise ValueError("report rules must be a list")

    report_files = report.get("files")
    if not isinstance(report_files, list):
        raise ValueError("report files must be a list")
    report_file_rows = {}
    for row in report_files:
        relative = row.get("path") if isinstance(row, dict) else None
        digest = row.get("sha256") if isinstance(row, dict) else None
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise ValueError("report file rows must contain path and SHA-256 strings")
        if relative in report_file_rows:
            raise ValueError(f"duplicate report file path: {relative}")
        report_file_rows[relative] = digest
    expected_report_files = set(manifest_rows) - {"report.json"}
    if set(report_file_rows) != expected_report_files:
        raise ValueError("report file inventory does not match the manifest")
    for relative, digest in report_file_rows.items():
        path = _safe_path(evidence, relative)
        actual = _sha256(path.read_bytes())
        if actual != digest or manifest_rows.get(relative) != actual:
            raise ValueError(f"report file binding mismatch for {relative}")

    rules = {}
    for row in rule_rows:
        mode = row.get("selection_mode") if isinstance(row, dict) else None
        if mode in rules:
            raise ValueError(f"duplicate retained rule setting: {mode}")
        source_path = _safe_path(evidence, row.get("path") if isinstance(row, dict) else None)
        source = source_path.read_text(encoding="utf-8")
        digest = hashlib.sha256(source.encode()).hexdigest()
        if digest != row.get("sha256"):
            raise ValueError(f"retained rule hash mismatch for {mode}")
        rules[mode] = source
    if set(rules) != set(prototype.ALLOWED_SELECTION_MODES):
        raise ValueError("retained rules do not cover every allowed setting")
    if rules[prototype.DEFAULT_SELECTION_MODE] != prototype.canonical_source(root=root):
        raise ValueError("retained nearest rule is not the current canonical source")
    if prototype.restore_canonical(rules["farthest"]) != rules["nearest"]:
        raise ValueError("retained farthest rule is not the guarded reversible variant")
    rule_hashes = {mode: hashlib.sha256(source.encode()).hexdigest() for mode, source in rules.items()}

    labels_reexecuted = 0
    seen_public_ids = set()
    demonstration_counts = set()
    query_counts = set()
    settings = set()
    with RacketBridge() as bridge:
        for row in episode_rows:
            public_id = row.get("public_id")
            if public_id in seen_public_ids:
                raise ValueError(f"duplicate public ID in report: {public_id}")
            seen_public_ids.add(public_id)
            public_path = _safe_path(evidence, row.get("public_path"))
            private_path = _safe_path(evidence, row.get("private_path"))
            public_payload = public_path.read_bytes()
            actual_id = _sha256(public_payload)
            if public_id != actual_id or public_path.stem != actual_id:
                raise ValueError(f"public ID does not match exact visible bytes: {public_id}")
            private = _read_json(private_path)
            if prototype.public_bytes(private) != public_payload:
                raise ValueError(f"public projection mismatch for {public_id}")
            mode = row.get("selection_mode")
            if private.get("parameters") != {"selection_mode": mode}:
                raise ValueError(f"private setting mismatch for {public_id}")
            if mode not in rules:
                raise ValueError(f"unknown private setting for {public_id}: {mode}")
            if row.get("seed") != private.get("seed") or row.get("input_seed") != private.get("input_seed"):
                raise ValueError(f"episode seed binding mismatch for {public_id}")
            settings.add(mode)

            bindings = private.get("source_bindings")
            if not isinstance(bindings, dict):
                raise ValueError(f"missing source bindings for {public_id}")
            if (bindings.get("generator_path") != generator_relative
                    or bindings.get("generator_sha256") != generator_sha256):
                raise ValueError(f"generator source binding mismatch for {public_id}")
            if bindings.get("canonical_rule_sha256") != rule_hashes["nearest"]:
                raise ValueError(f"canonical rule source binding mismatch for {public_id}")
            if bindings.get("rules") != rule_hashes:
                raise ValueError(f"parameter rule source binding mismatch for {public_id}")

            train = private.get("train")
            test = private.get("test")
            if not isinstance(train, list) or not isinstance(test, list) or not train or not test:
                raise ValueError(f"private episode has invalid train/test lists: {public_id}")
            demonstration_counts.add(len(train))
            query_counts.add(len(test))
            if private.get("counts") != {"demonstrations": len(train), "queries": len(test)}:
                raise ValueError(f"private count binding mismatch for {public_id}")
            pairs = train + test
            for index, pair in enumerate(pairs):
                actual = prototype.execute_rule(rules[mode], pair.get("input"), bridge=bridge)
                if actual != pair.get("output"):
                    raise ValueError(
                        f"Racket label mismatch for {public_id} pair {index} under {mode}"
                    )
                labels_reexecuted += 1

            opposite = next(candidate for candidate in rules if candidate != mode)
            opposite_outputs = [
                prototype.execute_rule(rules[opposite], pair.get("input"), bridge=bridge)
                for pair in pairs
            ]
            demo_mismatches = [
                index for index, pair in enumerate(train)
                if opposite_outputs[index] != pair.get("output")
            ]
            query_mismatches = [
                index for index, pair in enumerate(test)
                if opposite_outputs[len(train) + index] != pair.get("output")
            ]
            if not demo_mismatches:
                raise ValueError(f"demonstrations do not refute {opposite} for {public_id}")
            if len(query_mismatches) != len(test):
                raise ValueError(f"queries do not all distinguish {opposite} for {public_id}")
            expected_rivals = []
            for candidate in prototype.ALLOWED_SELECTION_MODES:
                if candidate == mode:
                    expected_rivals.append({
                        "selection_mode": candidate,
                        "status": "matches_episode",
                        "demonstration_mismatch_indices": [],
                        "query_mismatch_indices": [],
                    })
                else:
                    expected_rivals.append({
                        "selection_mode": candidate,
                        "status": "refuted_by_demonstrations",
                        "demonstration_mismatch_indices": demo_mismatches,
                        "query_mismatch_indices": query_mismatches,
                    })
            if private.get("parameter_rivals") != expected_rivals or private.get("ambiguities") != []:
                raise ValueError(f"rival diagnostics do not match replay for {public_id}")

        canonical_reexecuted = 0
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = prototype.execute_rule(rules["nearest"], pair["input"], bridge=bridge)
            if actual != pair["output"]:
                raise ValueError(
                    "retained canonical rule fails "
                    f"variant {pair['variant']} {pair['split']} pair {pair['pair_index']}"
                )
            canonical_reexecuted += 1

    counts = report.get("counts", {})
    if counts.get("episodes") != len(episode_rows):
        raise ValueError("report episode count is inconsistent")
    if len(demonstration_counts) != 1 or counts.get("demonstrations_per_episode") != next(iter(demonstration_counts)):
        raise ValueError("report demonstration count is inconsistent")
    if len(query_counts) != 1 or counts.get("queries_per_episode") != next(iter(query_counts)):
        raise ValueError("report query count is inconsistent")
    if counts.get("settings_exercised") != len(settings):
        raise ValueError("report setting count is inconsistent")
    if counts.get("ambiguous_parameter_rivals") != 0:
        raise ValueError("report ambiguity count is inconsistent")
    if counts.get("canonical_pairs_checked") != canonical_reexecuted:
        raise ValueError("report canonical-pair count is inconsistent")
    if counts.get("canonical_pair_mismatches") != 0:
        raise ValueError("report canonical mismatch count is inconsistent")
    return {
        "status": "verified",
        "episodes": len(episode_rows),
        "labels_reexecuted": labels_reexecuted,
        "canonical_pairs_reexecuted": canonical_reexecuted,
        "manifest_files_verified": len(manifest_rows),
    }


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    print(json.dumps(verify_evidence(args.evidence), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

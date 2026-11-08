#!/usr/bin/env python3
"""Replay the optional patch in a small temporary tree; retain compact evidence.

From WORK:
  python3 checks/authority-proposal/replay_proposal.py --repo repo \
    --proposal checks/authority-proposal/generated \
    --out checks/authority-proposal/replay

Only the two affected authorities, their two canonical rows, the task's catalog
mapping and the existing checker are copied. This proves textual synchronization
and guarded patch behavior; a full relocated runtime must check Racket parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def differences(left, right, path=""):
    if isinstance(left, dict) and isinstance(right, dict) and set(left) == set(right):
        return [p for key in left for p in differences(left[key], right[key], path + "/" + key)]
    return [] if left == right else [path]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--proposal", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo, proposal_dir, out = (p.resolve() for p in (args.repo, args.proposal, args.out))
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((proposal_dir / "manifest.json").read_text())
    patch = proposal_dir / "authority-sync.patch"
    assert sha(patch.read_bytes()) == manifest["patch_sha256"]
    task = manifest["task_id"]
    builder = repo / "generators" / task / "workspace/propose_authority_sync.py"
    checker = repo / "shared/tools/check_task_authority_sync.py"
    commands = []
    log = []
    result = {
        "schema_version": 1, "task_id": task,
        "runtime_executable": sys.executable, "runtime_version": sys.version,
        "scope": "tiny copied authority tree; no Racket execution",
        "patch_sha256": manifest["patch_sha256"],
        "builder_sha256": sha(builder.read_bytes()),
        "checker_sha256": sha(checker.read_bytes()),
        "commands": commands,
    }

    def run(argv, cwd, expected=0):
        completed = subprocess.run(argv, cwd=cwd, text=True, capture_output=True)
        commands.append({
            "cwd": os.path.relpath(cwd, repo.parent),
            "argv": argv, "expected_exit_code": expected,
            "exit_code": completed.returncode,
        })
        log.append(json.dumps(commands[-1]) + "\n" + completed.stdout + completed.stderr)
        assert completed.returncode == expected, log[-1]
        return completed

    try:
        with tempfile.TemporaryDirectory(prefix="tiny-", dir=out) as temporary:
            stage = Path(temporary)
            originals = {}
            for entry in manifest["files"]:
                relative = entry["path"]
                blob = (repo / relative).read_bytes()
                assert sha(blob) == entry["original_sha256"]
                originals[relative] = blob
                path = stage / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(blob)
            canonical = repo / "shared/data/canonical/puzzles.jsonl"
            source_rows = [line for line in canonical.read_bytes().splitlines(keepends=True)
                           if json.loads(line).get("task_id") == task]
            assert len(source_rows) == 2
            (stage / "shared/data/canonical").mkdir(parents=True)
            (stage / "shared/data/canonical/puzzles.jsonl").write_bytes(b"".join(source_rows))
            mapping = json.loads((repo / "catalog/authority_files.json").read_text())
            (stage / "catalog").mkdir()
            (stage / "catalog/authority_files.json").write_text(json.dumps({
                path: owner for path, owner in mapping.items() if owner == task
            }) + "\n")
            (stage / "shared/tools").mkdir()
            shutil.copyfile(checker, stage / "shared/tools/check_task_authority_sync.py")
            builder_arg = os.path.relpath(builder, stage)
            patch_arg = os.path.relpath(patch, stage)
            checker_args = ["python3", "shared/tools/check_task_authority_sync.py", task,
                            "--require-selected-exact-sync", "--require-whitespace-normalized-sync",
                            "--require-comment-stripped-sync"]
            # --json-out is relative to the checker's ROOT (stage/shared).
            before_arg = os.path.relpath(out / "before-text.json", stage / "shared")
            after_arg = os.path.relpath(out / "after-text.json", stage / "shared")
            run(["python3", builder_arg, "check", "--repo", ".", "--state", "original"], stage)
            run(checker_args + ["--json-out", before_arg], stage, expected=1)
            run(["git", "init", "-q"], stage)
            root = run(["git", "rev-parse", "--show-toplevel"], stage).stdout.strip()
            assert Path(root).resolve() == stage.resolve()
            run(["git", "apply", "--check", patch_arg], stage)
            run(["git", "apply", patch_arg], stage)
            run(["python3", builder_arg, "check", "--repo", ".", "--state", "patched"], stage)
            run(checker_args + ["--json-out", after_arg], stage)
            field_checks = []
            for entry in manifest["files"]:
                relative = entry["path"]
                after_blob = (stage / relative).read_bytes()
                assert sha(after_blob) == entry["patched_sha256"]
                before, after = json.loads(originals[relative]), json.loads(after_blob)
                pointers = differences(before, after)
                assert pointers == ["/racket_target/target_code"]
                old = before["racket_target"]["target_code"]
                new = after["racket_target"]["target_code"]
                assert old == " ".join(new.split())
                assert before["racket_target"]["raw_code"] == after["racket_target"]["raw_code"]
                field_checks.append({"path": relative, "changed_json_pointers": pointers,
                                     "original_sha256": sha(originals[relative]),
                                     "patched_sha256": sha(after_blob),
                                     "whitespace_normalized_equal": True,
                                     "raw_code_unchanged": True})
            result["independent_field_checks"] = field_checks
            tampered = stage / manifest["files"][0]["path"]
            clean = tampered.read_bytes()
            tampered.write_bytes(clean + b"\n")
            changed_hash = sha(tampered.read_bytes())
            run(["python3", builder_arg, "check", "--repo", ".", "--state", "patched"], stage, expected=2)
            assert sha(tampered.read_bytes()) == changed_hash
            tampered.write_bytes(clean)
            result["stale_file_guard"] = {"status": "PASS", "exit_code": 2,
                                          "input_left_unchanged_on_refusal": True}
            before_report = json.loads((out / "before-text.json").read_text())
            after_report = json.loads((out / "after-text.json").read_text())
            assert before_report["status"] == "FAIL"
            assert before_report["audits"][0]["selected_group_counts"]["exact_sha256"] == 2
            assert after_report["status"] == "SELECTED_SYNC_ARCHIVAL_DIVERGENT"
            assert after_report["failures"] == []
            assert after_report["audits"][0]["selected_group_counts"]["exact_sha256"] == 1
            assert after_report["audits"][0]["selected_authority_count"] == 4
            assert len(after_report["audits"][0]["archival_divergent"]) == 2
            result["checker_transition"] = {"before": "FAIL", "after": "SELECTED_SYNC_ARCHIVAL_DIVERGENT",
                                            "active_authorities": 4, "active_exact_groups_before": 2,
                                            "active_exact_groups_after": 1}
            for relative, original in originals.items():
                assert (repo / relative).read_bytes() == original
            result["active_shared_files_unchanged"] = True
            result["status"] = "PASS"
    except Exception as exc:
        result["status"] = "FAIL"
        result["error"] = str(exc)
    finally:
        (out / "commands.log").write_text("\n".join(log))
        (out / "receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "scope", "patch_sha256")}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

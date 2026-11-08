#!/usr/bin/env python3
"""Verify the proposal against an actual archive, using an existing seed only.

Creates and removes its own private temporary checkout. Never edits the input
archive or the existing assignment. Never prepares a solve or reads private labels.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import packet_subset as ps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    parser.add_argument("assignment", type=Path)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "actual-verification.json")
    args = parser.parse_args()
    source, assignment = args.zip.resolve(), args.assignment.resolve()
    helper = Path(__file__).with_name("packet_subset.py").resolve()
    original = json.loads(assignment.read_bytes())
    before = {"archive_sha256": ps.file_sha(source), "assignment_sha256": ps.file_sha(assignment)}
    evidence = {"schema": "arcpuzzles-packet-subset-proposal-verification-v1", "status": "running",
        "source_zip": str(source), "input_assignment": str(assignment), **before,
        "assignment_id": original["assignment_id"], "commands": [], "solve_prepared": False,
        "generator_or_rule_contents_printed": False}
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

    def command(argv, cwd):
        started = time.monotonic()
        process = subprocess.run(argv, cwd=cwd, env=environment, capture_output=True, text=True, timeout=600)
        evidence["commands"].append({"argv": argv, "cwd": str(cwd), "exit_code": process.returncode,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stdout": process.stdout, "stderr": process.stderr})
        args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        if process.returncode:
            raise RuntimeError(f"Command failed: {argv[:3]}")
        return process.stdout

    try:
        with tempfile.TemporaryDirectory(prefix="arc-subset-verification-") as temporary:
            root = Path(temporary) / "packet"
            evidence["private_temporary_checkout"] = str(root)
            evidence["full_archive_verification"] = json.loads(command(
                [sys.executable, str(helper), "verify", str(source)], helper.parent))
            result = json.loads(command([sys.executable, str(helper), "extract", str(source),
                                         str(root), "--seed", original["seed"]], helper.parent))
            pending = json.loads((root / "WORK/.review/pending-main-draw.json").read_bytes())
            assert pending["contract"] == original, "Helper pending contract differs from original draw"
            command([sys.executable, str(root / "review.py"), "start"], root)
            assert json.loads((root / "WORK/ASSIGNMENT.json").read_bytes()) == original
            names = json.loads((root / ".packet-subset/inventory.json").read_bytes())["inventory"]
            times = {row["path"]: (root / row["path"]).stat().st_mtime_ns for row in names}
            repeated = json.loads(command([sys.executable, str(helper), "extract", str(source), str(root)], root))
            assert repeated == result, "Unchanged rerun changed receipt"
            assert all((root / name).stat().st_mtime_ns == value for name, value in times.items())
            sys.path.insert(0, str(root / "WORK/repo/src"))
            from arcpuzzles.review_replay import _runtime_members
            from arcpuzzles.review_full_draw import blind_id_for_seed
            with ps.Packet(source) as packet:
                official = set()
                for task in result["tasks"]:
                    official.update(_runtime_members(packet.zip, packet.expected, packet.prefix,
                                    task, packet.manifest["generators"][task]["rule_task_id"]))
                actual = {row["path"] for row in names}
                assert official <= actual, "Missing official runtime closure member"
                assert blind_id_for_seed(packet.manifest, original["task_id"], bytes.fromhex(original["seed"])) == result["blind_task_id"]
                homes = {task: {n for n in packet.expected if n.startswith(f"WORK/repo/generators/{task}/")}
                         for task in result["tasks"]}
                assert all(paths <= actual for paths in homes.values()), "Incomplete selected task home"
            inventory_path = args.out.with_name("actual-extraction-inventory.json.gz")
            inventory_path.write_bytes(gzip.compress((root / ".packet-subset/inventory.json").read_bytes(), mtime=0))
            evidence.update(extraction=result, official_runtime_closure_files=len(official),
                additional_documentation_files=sorted(actual - official),
                selected_task_home_counts={task: len(paths) for task, paths in homes.items()},
                original_pending_contract_exact=True, official_start_assignment_exact=True,
                official_blind_selection_exact=True, unchanged_rerun_exact=True,
                extraction_inventory={"path": str(inventory_path), "sha256": ps.file_sha(inventory_path)})
        evidence["private_temporary_checkout_removed"] = not root.exists()
        assert ps.file_sha(source) == before["archive_sha256"]
        assert ps.file_sha(assignment) == before["assignment_sha256"]
        evidence.update(status="passed", original_archive_and_assignment_unchanged=True)
    except BaseException as error:
        evidence.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": evidence["status"], "verified_files": evidence["full_archive_verification"]["verified_files"],
                      "selected_files": result["selected_files"], "evidence": str(args.out)}, sort_keys=True))


if __name__ == "__main__":
    main()
